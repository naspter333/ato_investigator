"""Generate fictional account activity. No real customer information is used."""
import csv
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ['event_id','account_id','timestamp','event_type','device_id','country','ip_address','amount','beneficiary_id','is_ato','scenario']

def generate(seed=42):
    rng = random.Random(seed)
    rows = []
    start = datetime(2026, 10, 1, tzinfo=timezone.utc)
    def add(account, time, kind, device, country, amount=0, beneficiary='', label=0, scenario='Routine activity'):
        rows.append(dict(event_id=f'EVT-{len(rows)+1:05d}', account_id=account, timestamp=time.isoformat().replace('+00:00','Z'), event_type=kind, device_id=device, country=country, ip_address=f'192.0.2.{rng.randint(1,254)}', amount=amount, beneficiary_id=beneficiary, is_ato=label, scenario=scenario))
    for i in range(1,81):
        account = f'ACC-{i:04d}'
        home = ['US','GB','IN','CA'][i % 4]
        device = f'DEV-{i:04d}'
        compromised = i <= 12
        scenario = ('Credential compromise' if i <= 8 else 'Low signal takeover') if compromised else ('Benign travel' if i <= 20 else 'Forgotten password' if i <= 26 else 'New phone' if i <= 32 else 'Routine activity')
        for day in range(10):
            t = start + timedelta(days=day, hours=8 + i % 10, minutes=rng.randint(0,40))
            add(account,t,'login_success',device,home,label=int(compromised),scenario=scenario)
            if rng.random() < .75:
                add(account,t+timedelta(minutes=15),'transfer',device,home,rng.randint(20,400),f'PAYEE-{i:04d}',int(compromised),scenario)
        t = start + timedelta(days=10, hours=10, minutes=i)
        if i <= 8:
            attacker = f'NEW-{i:04d}'
            foreign = 'DE' if home != 'DE' else 'SG'
            for j in range(4):
                add(account,t+timedelta(minutes=j),'login_failed',attacker,foreign,label=1,scenario=scenario)
            add(account,t+timedelta(minutes=5),'password_reset',attacker,foreign,label=1,scenario=scenario)
            add(account,t+timedelta(minutes=7),'login_success',attacker,foreign,label=1,scenario=scenario)
            add(account,t+timedelta(minutes=10),'beneficiary_added',attacker,foreign,beneficiary=f'NEWPAYEE-{i}',label=1,scenario=scenario)
            add(account,t+timedelta(minutes=18),'transfer',attacker,foreign,rng.randint(1800,6500),f'NEWPAYEE-{i}',1,scenario)
        elif i <= 12:
            add(account,t,'login_success',device,home,label=1,scenario=scenario)
            add(account,t+timedelta(minutes=20),'transfer',device,home,220,f'PAYEE-{i:04d}',1,scenario)
        elif i <= 20:
            add(account,t,'login_success',f'TRAVEL-{i}', 'SG',scenario=scenario)
            add(account,t+timedelta(minutes=12),'transfer',f'TRAVEL-{i}','SG',600,f'PAYEE-{i:04d}',scenario=scenario)
        elif i <= 26:
            for j in range(4):
                add(account,t+timedelta(minutes=j),'login_failed',device,home,scenario=scenario)
            add(account,t+timedelta(minutes=6),'password_reset',device,home,scenario=scenario)
            add(account,t+timedelta(minutes=9),'login_success',device,home,scenario=scenario)
        elif i <= 32:
            add(account,t,'login_success',f'PHONE-{i}',home,scenario=scenario)
        else:
            add(account,t,'login_success',device,home,scenario=scenario)
    return sorted(rows, key=lambda row: (row['timestamp'], row['event_id']))

if __name__ == '__main__':
    rows=generate()
    target=ROOT/'dist'/'data'
    target.mkdir(parents=True,exist_ok=True)
    with (target/'events.csv').open('w', newline='') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS); writer.writeheader(); writer.writerows(rows)
    (target/'events.json').write_text(json.dumps(rows,separators=(',',':')))
    print(f'Generated {len(rows)} events across 80 accounts with seed 42')
