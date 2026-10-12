import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {validateEvents,parseCSV,analyze,metrics,DEFAULT_RULES,csvExport} from '../dist/engine.js';
const sample=JSON.parse(fs.readFileSync(new URL('../dist/data/events.json',import.meta.url)));
const events=validateEvents(sample);
test('demo provides interpretable true positives, false positives and missed attacks',()=>{
  const accounts=analyze(events),m=metrics(accounts);
  assert.equal(accounts.length,80);assert.equal(m.tp,8);assert.equal(m.fp,14);assert.equal(m.fn,4);assert.equal(m.tn,54);
  assert.equal(accounts.find(a=>a.id==='ACC-0001').score,80);
  assert.equal(accounts.find(a=>a.id==='ACC-0013').score,40);
  assert.equal(accounts.find(a=>a.id==='ACC-0009').score,0);
});
test('higher alert threshold reduces benign alerts but catches strong attack sequences',()=>{const m=metrics(analyze(events,{...DEFAULT_RULES,alertThreshold:70}));assert.equal(m.tp,8);assert.equal(m.fp,0);assert.equal(m.fn,4);});
test('labels and scenario text never affect detection scores',()=>{
  const changed=validateEvents(sample.map(e=>({...e,is_ato:1,scenario:'irrelevant'})));
  assert.deepEqual(analyze(events).map(a=>[a.id,a.score,a.exposure]),analyze(changed).map(a=>[a.id,a.score,a.exposure]));
});
test('future password reset cannot increase earlier login score',()=>{
  const rows=sample.filter(e=>e.account_id==='ACC-0033').slice(0,2);
  const first=rows.find(e=>e.event_type==='login_success');
  const future={...first,event_id:'FUTURE',event_type:'password_reset',timestamp:'2026-10-12T10:00:00Z'};
  const a=analyze(validateEvents([...rows,future]))[0];assert.equal(a.events[0].eventScore,0);
});
test('lookback expiration excludes stale login failures',()=>{
  const rows=sample.filter(e=>e.account_id==='ACC-0021');
  const success=rows.findLast(e=>e.event_type==='login_success');
  const expired=rows.map(e=>e===success?{...e,timestamp:'2026-10-11T15:00:00Z'}:e);
  assert.equal(analyze(validateEvents(expired))[0].score,0);
});
test('unlabeled uploads have no fabricated precision or recall',()=>{const rows=validateEvents(sample.map(({is_ato,...rest})=>rest));const m=metrics(analyze(rows));assert.equal(m.labeled,0);assert.equal(m.precision,null);assert.equal(m.recall,null);});
test('CSV round trip preserves quoted content and line endings',()=>{const rows=[{...sample[0],scenario:'Travel, then "new phone"\nVerified'}];const csv=csvExport(rows,Object.keys(rows[0]));assert.deepEqual(parseCSV(csv),rows.map(r=>Object.fromEntries(Object.entries(r).map(([k,v])=>[k,String(v)]))));});
test('CSV validation catches malformed uploads',()=>{
  assert.throws(()=>parseCSV('a,b\n"oops,x'),/Unclosed/);
  assert.throws(()=>parseCSV('a,a\nx,y'),/Duplicate/);
  assert.throws(()=>validateEvents([{...sample[0],amount:-1}]),/nonnegative/);
  assert.throws(()=>validateEvents([{...sample[0],timestamp:'2026-10-01 10:00'}]),/timezone/);
  assert.throws(()=>validateEvents([sample[0],sample[0]]),/duplicate/);
  assert.throws(()=>validateEvents([{...sample[0],event_type:'unknown'}]),/unsupported/);
  assert.throws(()=>validateEvents([{...sample[0],is_ato:7}]),/0 or 1/);
});
test('export guards spreadsheet formula injection',()=>assert.match(csvExport([{account_id:'=HYPERLINK("bad")'}],['account_id']),/"'=HYPERLINK/));
