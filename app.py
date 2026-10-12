"""Run with: streamlit run app.py"""
import hashlib
import json
from collections import Counter
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from fraud_engine import DEFAULT_RULES, REQUIRED, analyze, csv_export, metrics, parse_csv, validate_events

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title='ATO Investigator', page_icon='🛡️', layout='wide')
st.markdown('''<style>.block-container{padding-top:2rem}h1{letter-spacing:-1px}
[data-testid="stMetric"]{background:white;border:1px solid #e1e8ec;border-radius:10px;padding:18px}
[data-testid="stMetricValue"]{color:#087f75;font-size:1.6rem}[data-testid="stMetricLabel"] p{white-space:normal}.stCaption{line-height:1.6}</style>''', unsafe_allow_html=True)

@st.cache_data
def demo_events():
    return validate_events(json.loads((ROOT/'dist/data/events.json').read_text()))

def money(n):
    return f'${n:,.0f}'

def percent(n):
    return 'N/A' if n is None else f'{n:.1%}'

def event_table(events):
    return pd.DataFrame([dict(timestamp=e['_time'].strftime('%Y-%m-%d %H:%M:%S UTC'), event=e['event_type'], device=e['device_id'], country=e['country'], ip=e['ip_address'], amount_usd=e['amount'], beneficiary=e['beneficiary_id'], score=e['event_score'], reasons='; '.join(e['reasons'])) for e in events])

def account_table(accounts, dataset_key):
    return pd.DataFrame([{'Account':a['id'], 'Score':a['score'], 'Priority':a['severity'], 'Home country':a['home'], 'Signals':'; '.join(a['reasons']) or 'No rule signals', 'Flagged transfers USD':a['exposure'], 'Review status':st.session_state.notes.get(dataset_key+'|'+a['id'], {}).get('status','Not reviewed')} for a in accounts])

def show_journal():
    st.title('Vibe coding build journal')
    st.info('This journal renders actual project messages, implementation artifacts, and saved test outputs. Screenshots of this page are build-journal evidence, not screenshots of the original Codex chat UI.')
    journal=json.loads((ROOT/'submission/process_journal.json').read_text())
    stage=st.radio('Evidence view',['Actual prompts','Build steps','Code and tests','Iterations'],horizontal=True,key='journal_evidence')
    if stage=='Actual prompts':
        st.subheader('Actual prompts used in this conversation')
        for i,entry in enumerate(journal['prompts'],1):
            st.markdown(f'**Prompt {i} — {entry["stage"]}**')
            st.code(entry['text'],language=None,wrap_lines=True)
    elif stage=='Build steps':
        st.subheader('Full step-by-step build breakdown')
        for step in journal['steps']:
            st.markdown(f'**{step["number"]}. {step["title"]}**')
            st.write(step['detail'])
    elif stage=='Code and tests':
        st.subheader('Implementation evidence')
        source=st.selectbox('Source artifact',['fraud_engine.py','app.py','tests/test_fraud_engine.py','requirements.txt'])
        st.code((ROOT/source).read_text(),language='python' if source.endswith('.py') else None,line_numbers=True,height=300)
        st.subheader('Executed validation commands and outputs')
        path=ROOT/'submission/streamlit_validation.json'
        if path.exists():
            result=json.loads(path.read_text())
            for entry in result['commands']:
                st.markdown(f'**{entry["purpose"]}**')
                st.code(entry['command'],language='bash')
                st.code(entry['output'],language=None,wrap_lines=True,height=380)
        else:
            st.caption('Validation output has not yet been captured.')
    else:
        st.subheader('Observed iterations and learnings')
        for item in journal['iterations']:
            st.write('• '+item)

if 'notes' not in st.session_state:
    st.session_state.notes={}
if 'rules' not in st.session_state:
    st.session_state.rules=DEFAULT_RULES.copy()

with st.sidebar:
    st.title('🛡️ ATO Investigator')
    st.caption('Account takeover investigation lab')
    view=st.radio('Workspace',['Overview','Account investigation','Detection playground','Data and methodology','Vibe coding build journal'],key='workspace_view')
    st.divider()
    st.caption('Fictional dataset · Week 1 Path 3')
    st.caption('Python + Streamlit + pandas + Plotly')

if view=='Vibe coding build journal':
    show_journal()
    st.stop()

if 'events' not in st.session_state:
    st.session_state.events=demo_events()
    st.session_state.dataset_key='demo'
    st.session_state.dataset_name='Included synthetic dataset'

with st.sidebar:
    uploaded=st.file_uploader('Upload activity CSV',type=['csv'],max_upload_size=10)
    if uploaded:
        raw=uploaded.getvalue()
        digest=hashlib.sha256(raw).hexdigest()
        if digest != st.session_state.get('upload_digest'):
            try:
                converted=validate_events(parse_csv(raw.decode('utf-8-sig')))
                st.session_state.events=converted
                st.session_state.dataset_key=digest
                st.session_state.dataset_name=f'Uploaded: {uploaded.name}'
                st.session_state.upload_digest=digest
                for key in ['date_range','home_country','account_search','selected_account']:
                    st.session_state.pop(key,None)
            except (ValueError,UnicodeDecodeError) as exc:
                st.error(f'Upload rejected: {exc}. The previous valid dataset remains active.')
    if st.button('Restore demo data'):
        st.session_state.events=demo_events()
        st.session_state.dataset_key='demo'
        st.session_state.dataset_name='Included synthetic dataset'
        # The uploader can remain selected; ignore its current digest until changed.
        for key in ['date_range','home_country','account_search','selected_account']:
            st.session_state.pop(key,None)
        st.rerun()

events=st.session_state.events
rules=st.session_state.rules
accounts=analyze(events,rules)
key=st.session_state.dataset_key
with st.sidebar:
    st.subheader('Account cohort filters')
    dates=st.date_input('Activity dates in UTC',value=(min(e['_time'].date() for e in events),max(e['_time'].date() for e in events)),key='date_range')
    country=st.selectbox('Account home country',['All']+sorted({a['home'] for a in accounts}),key='home_country')
    search=st.text_input('Account search',placeholder='ACC-0001',key='account_search').strip().lower()
    if st.button('Reset filters'):
        for name in ['date_range','home_country','account_search']:
            st.session_state.pop(name,None)
        st.rerun()

if len(dates)!=2:
    st.warning('Select both a start date and an end date.');st.stop()
start,end=dates
scope=[a for a in accounts if (country=='All' or country==a['home']) and search in a['id'].lower() and any(start<=e['_time'].date()<=end for e in a['events'])]
m=metrics(scope)
st.caption(f'{st.session_state.dataset_name} · {len(events):,} events · {len(accounts)} accounts · USD amounts')
st.caption('Dates select accounts with activity in the UTC window; home country uses the first successful login. Rules, metrics, and account timelines use full available account history. The activity chart uses selected dates only.')

if view=='Overview':
    st.title('Investigation overview')
    cols=st.columns(4)
    for col,label,value,hint in zip(cols,['Accounts in scope','Accounts needing review','Flagged transfer value','Detection recall'],[len(scope),m['alerts'],money(m['exposure']),percent(m['recall'])],['Selected account cohort',f'Score ≥ {rules["alert_threshold"]}','Rule-flagged transfer exposure',f'{m["tp"]} caught / {m["tp"]+m["fn"]} labeled takeovers']):
        col.metric(label,value);col.caption(hint)
    left,right=st.columns([1.5,1])
    with left:
        st.subheader('Activity over time')
        counts=Counter(e['_time'].date() for a in scope for e in a['events'] if start<=e['_time'].date()<=end)
        flagged=Counter(e['_time'].date() for a in scope for e in a['events'] if start<=e['_time'].date()<=end and e['event_score']>=rules['alert_threshold'])
        days=sorted(counts)
        if days:
            fig=go.Figure([go.Bar(x=days,y=[counts[d] for d in days],name='All activity',marker_color='#b4d9d1'),go.Bar(x=days,y=[flagged[d] for d in days],name='Flagged events',marker_color='#087f75')])
            fig.update_layout(barmode='overlay',height=310,margin=dict(l=10,r=10,t=15,b=10),legend=dict(orientation='h'),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig,width='stretch')
        else:st.info('No activity in the selected dates.')
    with right:
        st.subheader('Signals across alerted accounts')
        counts=Counter(r for a in scope if a['alert'] for r in a['reasons'])
        if counts:
            rows=counts.most_common()
            fig=go.Figure(go.Bar(x=[n for _,n in reversed(rows)],y=[r for r,_ in reversed(rows)],orientation='h',marker_color='#087f75'))
            fig.update_layout(height=310,margin=dict(l=0,r=10,t=15,b=10),xaxis_title='Accounts',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig,width='stretch')
        else:st.info('No rule signals in the selected cohort.')
    st.subheader('Account review queue')
    include_all=st.toggle('Include accounts without alerts')
    queue=[a for a in scope if include_all or a['alert']]
    if queue:st.dataframe(account_table(queue,key),hide_index=True,width='stretch')
    else:st.info('No accounts match. Adjust filters or the detection threshold.')
    st.download_button('Export alerts CSV',csv_export([dict(account_id=a['id'],score=a['score'],priority=a['severity'],reasons='; '.join(a['reasons']),flagged_transfer_value_usd=a['exposure']) for a in scope if a['alert']],['account_id','score','priority','reasons','flagged_transfer_value_usd']),'ato-alerts.csv','text/csv')

elif view=='Account investigation':
    st.title('Account investigation')
    if not scope:st.info('No accounts match the filters.');st.stop()
    chosen=st.selectbox('Choose an account',[a['id'] for a in scope],key='selected_account')
    a=next(a for a in scope if a['id']==chosen)
    st.subheader(f'{a["id"]} · {a["severity"]} priority')
    cols=st.columns(4)
    for col,label,value in zip(cols,['Account score','Signals observed','Total transfers','Flagged transfers'],[a['score'],len(a['reasons']),money(a['total_transferred']),money(a['exposure'])]):col.metric(label,value)
    st.caption('Score is the highest event score, not a probability. Transfer values use full account history.')
    left,right=st.columns([1.7,1])
    with left:
        st.subheader('Chronological activity timeline')
        signals_only=st.toggle('Signals only',value=True)
        visible=[e for e in a['events'] if not signals_only or e['reasons']]
        st.dataframe(event_table(visible),hide_index=True,width='stretch',height=420)
        st.download_button('Download timeline CSV',csv_export([{**e,'reasons':'; '.join(e['reasons'])} for e in a['events']],REQUIRED+['event_score','reasons']),'account-timeline.csv','text/csv')
    with right:
        st.subheader('Investigation evidence')
        for reason in a['reasons']:st.write('• '+reason)
        if not a['reasons']:st.write('No configured detection rules matched.')
        st.warning('Travel, a new phone, and password recovery can trigger signals. A rule match is a reason to investigate.')
        with st.expander('Reveal synthetic ground truth'):
            st.write('No evaluation label' if a['label'] is None else 'Labeled takeover account' if a['label']==1 else 'Labeled legitimate account')
            st.write(a['events'][0].get('scenario','No scenario supplied'))
            st.caption('Labels apply to accounts and are excluded from scoring.')
    st.subheader('Case notes')
    st.caption('Notes persist across reruns in the current Streamlit session. Export them before ending the session; there is no durable case database.')
    note_key=key+'|'+chosen
    saved=st.session_state.notes.get(note_key,{})
    with st.form('case-form-'+note_key):
        statuses=['Not reviewed','Investigating','Escalated','Benign activity']
        status=st.selectbox('Review outcome',statuses,index=statuses.index(saved.get('status','Not reviewed')))
        note=st.text_area('Investigator notes',value=saved.get('text',''))
        if st.form_submit_button('Save case notes'):
            st.session_state.notes[note_key]={'status':status,'text':note}
            st.success('Saved for this Streamlit session.')
    st.download_button('Export case notes JSON',json.dumps(st.session_state.notes,indent=2),'case-notes.json','application/json')

elif view=='Detection playground':
    st.title('Detection playground')
    st.info('Compare alert workload and detection tradeoffs. Synthetic results are demonstrations, not production benchmarks.')
    left,right=st.columns([1,1.4])
    with left:
        st.subheader('Detection settings')
        with st.form('rule-settings'):
            proposed={}
            for name,label,minimum,maximum,step in [('failed_count','Failed login count',1,8,1),('window_minutes','Login lookback minutes',5,120,5),('transfer_amount','Large transfer threshold USD',100,7000,100),('followup_minutes','Transfer follow-up minutes',10,180,10),('alert_threshold','Account alert threshold',20,90,5)]:
                proposed[name]=st.slider(label,minimum,maximum,int(rules[name]),step=step)
            if st.form_submit_button('Apply rules'):
                st.session_state.rules=proposed;st.rerun()
        if st.button('Restore default rules'):
            st.session_state.rules=DEFAULT_RULES.copy();st.rerun()
    with right:
        st.subheader('Detection outcomes')
        st.caption(f'{m["labeled"]} labeled accounts in the selected cohort')
        cols=st.columns(2)
        cols[0].metric('Takeovers caught',m['tp']);cols[1].metric('Legitimate accounts flagged',m['fp'])
        cols=st.columns(2)
        cols[0].metric('Takeovers missed',m['fn']);cols[1].metric('Legitimate accounts unflagged',m['tn'])
        ids={a['id'] for a in scope}
        base=metrics([a for a in analyze(events) if a['id'] in ids])
        st.dataframe(pd.DataFrame({'Metric':['Accounts alerted','Precision','Recall','Flagged transfer value'],'Default rules':[str(base['alerts']),percent(base['precision']),percent(base['recall']),money(base['exposure'])],'Current rules':[str(m['alerts']),percent(m['precision']),percent(m['recall']),money(m['exposure'])]}),hide_index=True,width='stretch')
    st.subheader('How scoring works')
    st.write('At login: new device +20, new country +20, recent failed-login burst +25, recent password reset +15. At transfer: large transfer after a suspicious login on the same device +45; large transfer to a newly added beneficiary +35. Reasons on the same event add together. Account score is the highest event score, capped at 100.')
    st.caption('The account threshold also defines a suspicious login for the follow-up transfer rule. Rules process earlier events only; equal timestamps use event ID order.')

else:
    st.title('Data and methodology')
    st.write('The synthetic dataset has 80 accounts: 8 strong-signal takeovers, 4 low-signal takeovers, 8 benign travelers, 6 password recoveries, 6 new phones, and 48 routine accounts. Python generates it reproducibly with seed 42. IPs use documentation addresses; amounts are USD.')
    st.download_button('Download current dataset CSV',csv_export(events,REQUIRED+['is_ato','scenario']),'account-events.csv','text/csv')
    st.subheader('CSV schema')
    st.dataframe(pd.DataFrame({'Column':REQUIRED+['is_ato','scenario'],'Meaning':['Unique event identifier','Account identifier','ISO 8601 timestamp with timezone','login_success, login_failed, password_reset, beneficiary_added, transfer','Device identifier','Event country','IP or masked identifier','Nonnegative USD amount; zero for non-transfers','Required for transfers and beneficiary additions','Optional consistent account label 0 or 1','Optional scenario description']}),hide_index=True,width='stretch')
    st.subheader('Interpretation and limitations')
    st.write('Labels are optional and used only for evaluation. Flagged transfer value is review exposure, not confirmed loss. Detection misses low-signal takeovers and can flag legitimate changes. The app does not enforce MFA, block transactions, infer travel speed, or contact customers.')
    st.write('CSV uploads are sent to the Streamlit server for Python analysis. Local execution keeps processing on your computer. Hosted execution processes data on the hosting server. Use the included synthetic data for this project. Uploaded data and notes are session-scoped; no file upload or case database is persisted by this app.')
    st.subheader('Build evidence')
    st.write('Open Vibe coding build journal in the sidebar for actual prompts, the step-by-step implementation, source code, observed iterations, and saved validation output.')
