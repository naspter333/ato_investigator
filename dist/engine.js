export const TYPES=['login_success','login_failed','password_reset','beneficiary_added','transfer'];
export const DEFAULT_RULES={failedCount:3,windowMinutes:30,transferAmount:1500,followupMinutes:60,alertThreshold:40};
export const REQUIRED=['event_id','account_id','timestamp','event_type','device_id','country','ip_address','amount','beneficiary_id'];
export function parseCSV(text){
  text=text.replace(/^\uFEFF/,'');
  const records=[];let row=[],field='',quoted=false;
  for(let i=0;i<text.length;i++){
    const c=text[i];
    if(c==='"'){if(quoted&&text[i+1]==='"'){field+='"';i++;}else if(quoted){quoted=false;}else if(field===''){quoted=true;}else throw Error('Unexpected quote in CSV.');}
    else if(c===','&&!quoted){row.push(field);field='';}
    else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;row.push(field);if(row.some(x=>x!==''))records.push(row);row=[];field='';}
    else field+=c;
  }
  if(quoted)throw Error('Unclosed quote in CSV.');
  row.push(field);if(row.some(x=>x!==''))records.push(row);
  if(records.length<2)throw Error('CSV must contain a header and at least one event.');
  const headers=records.shift().map(x=>x.trim());
  if(new Set(headers).size!==headers.length)throw Error('Duplicate CSV columns.');
  return records.map((r,i)=>{if(r.length!==headers.length)throw Error(`Row ${i+2}: incorrect column count.`);return Object.fromEntries(headers.map((h,j)=>[h,r[j]]));});
}
export function validateEvents(rows){
  if(!Array.isArray(rows)||!rows.length)throw Error('Dataset is empty.');
  if(rows.length>50000)throw Error('Use a CSV with 50,000 events or fewer.');
  const seen=new Set(),labels=new Map();
  return rows.map((r,i)=>{
    const fail=m=>{throw Error(`Row ${i+2}: ${m}`);};
    for(const key of REQUIRED){if(!(key in r))fail(`missing column ${key}.`);}
    for(const key of ['event_id','account_id','timestamp','event_type','device_id','country','ip_address'])if(!String(r[key]).trim())fail(`${key} is required.`);
    if(seen.has(r.event_id))fail('duplicate event_id.');seen.add(r.event_id);
    if(!TYPES.includes(r.event_type))fail('unsupported event_type.');
    if(!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(r.timestamp)||!Number.isFinite(Date.parse(r.timestamp)))fail('timestamp must be ISO 8601 with timezone.');
    const amount=Number(r.amount);if(String(r.amount).trim()===''||!Number.isFinite(amount)||amount<0)fail('amount must be a nonnegative number.');
    if(r.event_type!=='transfer'&&amount!==0)fail('only transfers can have an amount.');
    if(['transfer','beneficiary_added'].includes(r.event_type)&&!String(r.beneficiary_id).trim())fail('beneficiary_id is required for this event.');
    let label=null;if(r.is_ato!==undefined&&r.is_ato!==''&&r.is_ato!==null){if(!['0','1'].includes(String(r.is_ato)))fail('is_ato must be 0 or 1.');label=Number(r.is_ato);}
    if(labels.has(r.account_id)&&labels.get(r.account_id)!==label)fail('is_ato must be consistent across an account.');labels.set(r.account_id,label);
    return {...r,amount,is_ato:label,_time:Date.parse(r.timestamp)};
  }).sort((a,b)=>a._time-b._time||a.event_id.localeCompare(b.event_id));
}
export function analyze(events,rules=DEFAULT_RULES){
  const groups=new Map();for(const e of events){if(!groups.has(e.account_id))groups.set(e.account_id,[]);groups.get(e.account_id).push(e);}
  return [...groups].map(([id,items])=>{
    items=[...items].sort((a,b)=>a._time-b._time||a.event_id.localeCompare(b.event_id));
    const devices=new Set(),countries=new Set(),successes=[],failures=[],resets=[],payees=new Map(),signals=[];
    let score=0;const enriched=[];
    for(const e of items){
      const reasons=[];let value=0;
      const recent=(x,minutes)=>e._time-x._time>=0&&e._time-x._time<=minutes*60000;
      if(e.event_type==='login_failed')failures.push(e);
      if(e.event_type==='password_reset')resets.push(e);
      if(e.event_type==='login_success'){
        const newDevice=devices.size>0&&!devices.has(e.device_id),newCountry=countries.size>0&&!countries.has(e.country);
        if(newDevice){reasons.push('New device');value+=20;}
        if(newCountry){reasons.push('New country');value+=20;}
        if(failures.filter(x=>recent(x,rules.windowMinutes)).length>=rules.failedCount){reasons.push('Failed login burst before success');value+=25;}
        if(resets.some(x=>recent(x,rules.windowMinutes))){reasons.push('Password reset before success');value+=15;}
        successes.push({...e,suspicious:value>=rules.alertThreshold});devices.add(e.device_id);countries.add(e.country);
      }
      if(e.event_type==='beneficiary_added')payees.set(e.beneficiary_id,e);
      if(e.event_type==='transfer'){
        const login=[...successes].reverse().find(x=>recent(x,rules.followupMinutes)&&x.device_id===e.device_id);
        if(e.amount>=rules.transferAmount&&login?.suspicious){reasons.push('Large transfer after suspicious login');value+=45;}
        const payee=payees.get(e.beneficiary_id);
        if(e.amount>=rules.transferAmount&&payee&&recent(payee,rules.followupMinutes)){reasons.push('Large transfer to newly added beneficiary');value+=35;}
      }
      score=Math.max(score,value);
      const row={...e,eventScore:Math.min(100,value),reasons};enriched.push(row);
      if(reasons.length)signals.push(row);
    }
    score=Math.min(100,score);
    const transfers=enriched.filter(x=>x.event_type==='transfer');
    const exposure=transfers.filter(x=>x.eventScore>=rules.alertThreshold).reduce((s,x)=>s+x.amount,0);
    return {id,score,alert:score>=rules.alertThreshold,severity:score>=70?'High':score>=rules.alertThreshold?'Review':'Low',label:items[0].is_ato,events:enriched,signals,reasons:[...new Set(signals.flatMap(x=>x.reasons))],exposure,totalTransferred:transfers.reduce((s,x)=>s+x.amount,0),lastTime:items.at(-1)._time};
  }).sort((a,b)=>b.score-a.score||a.id.localeCompare(b.id));
}
export function metrics(accounts){
  const labeled=accounts.filter(a=>a.label!==null),tp=labeled.filter(a=>a.alert&&a.label===1).length,fp=labeled.filter(a=>a.alert&&a.label===0).length,fn=labeled.filter(a=>!a.alert&&a.label===1).length,tn=labeled.filter(a=>!a.alert&&a.label===0).length;
  return {tp,fp,fn,tn,labeled:labeled.length,alerts:accounts.filter(a=>a.alert).length,precision:tp+fp?tp/(tp+fp):null,recall:tp+fn?tp/(tp+fn):null,exposure:accounts.reduce((s,a)=>s+a.exposure,0)};
}
export function csvExport(rows,fields){
  const cell=x=>{let s=String(x??'');if(/^[=+\-@\t\r]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';};
  return [fields.map(cell).join(','),...rows.map(r=>fields.map(f=>cell(r[f])).join(','))].join('\r\n');
}
