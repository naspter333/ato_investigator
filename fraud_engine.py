"""Explainable chronological ATO rules, independent of Streamlit and evaluation labels."""
import csv
import io
import math
import re
from collections import defaultdict
from datetime import datetime, timezone

DEFAULT_RULES = dict(failed_count=3, window_minutes=30, transfer_amount=1500, followup_minutes=60, alert_threshold=40)
REQUIRED = ['event_id', 'account_id', 'timestamp', 'event_type', 'device_id', 'country', 'ip_address', 'amount', 'beneficiary_id']
TYPES = {'login_success', 'login_failed', 'password_reset', 'beneficiary_added', 'transfer'}

def parse_csv(text):
    try:
        reader = csv.reader(io.StringIO(text.lstrip('\ufeff')), strict=True)
        raw = list(reader)
    except csv.Error as exc:
        raise ValueError(f'Malformed CSV: {exc}') from exc
    raw = [row for row in raw if any(row)]
    if len(raw) < 2:
        raise ValueError('CSV must contain a header and at least one event.')
    headers = [x.strip() for x in raw[0]]
    if len(set(headers)) != len(headers):
        raise ValueError('Duplicate CSV columns.')
    rows = []
    for i, row in enumerate(raw[1:], 2):
        if len(row) != len(headers):
            raise ValueError(f'Row {i}: incorrect column count.')
        rows.append(dict(zip(headers, row)))
    return rows

def validate_events(rows):
    if not rows:
        raise ValueError('Dataset is empty.')
    if len(rows) > 50000:
        raise ValueError('Use 50,000 events or fewer.')
    seen, labels, result = set(), {}, []
    for i, raw in enumerate(rows, 2):
        r = dict(raw)
        def fail(message):
            raise ValueError(f'Row {i}: {message}')
        for key in REQUIRED:
            if key not in r:
                fail(f'missing column {key}.')
        for key in REQUIRED[:7]:
            if not str(r[key]).strip():
                fail(f'{key} is required.')
        if r['event_id'] in seen:
            fail('duplicate event_id.')
        seen.add(r['event_id'])
        if r['event_type'] not in TYPES:
            fail('unsupported event_type.')
        timestamp = str(r['timestamp'])
        try:
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})', timestamp):
                raise ValueError()
            time = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).astimezone(timezone.utc)
        except ValueError:
            fail('timestamp must be valid ISO 8601 with timezone.')
        try:
            amount = float(r['amount'])
            if not math.isfinite(amount) or amount < 0:
                raise ValueError()
        except (ValueError, TypeError):
            fail('amount must be a nonnegative number.')
        if r['event_type'] != 'transfer' and amount != 0:
            fail('only transfers can have an amount.')
        if r['event_type'] in {'transfer', 'beneficiary_added'} and not str(r['beneficiary_id']).strip():
            fail('beneficiary_id is required for this event.')
        label = r.get('is_ato')
        if label not in ('', None):
            if str(label) not in {'0', '1'}:
                fail('is_ato must be 0 or 1.')
            label = int(label)
        else:
            label = None
        if r['account_id'] in labels and labels[r['account_id']] != label:
            fail('is_ato must be consistent across an account.')
        labels[r['account_id']] = label
        result.append({**r, 'amount': amount, 'is_ato': label, '_time': time})
    return sorted(result, key=lambda e: (e['_time'], e['event_id']))

def analyze(events, rules=None):
    rules = {**DEFAULT_RULES, **(rules or {})}
    groups = defaultdict(list)
    for event in events:
        groups[event['account_id']].append(event)
    accounts = []
    for account_id, items in groups.items():
        items = sorted(items, key=lambda e: (e['_time'], e['event_id']))
        devices, countries, successes, failures, resets, payees, enriched = set(), set(), [], [], [], {}, []
        score = 0
        for e in items:
            reasons, value = [], 0
            def recent(x, minutes):
                return 0 <= (e['_time'] - x['_time']).total_seconds() <= minutes * 60
            kind = e['event_type']
            if kind == 'login_failed':
                failures.append(e)
            elif kind == 'password_reset':
                resets.append(e)
            elif kind == 'login_success':
                if devices and e['device_id'] not in devices:
                    reasons.append('New device'); value += 20
                if countries and e['country'] not in countries:
                    reasons.append('New country'); value += 20
                if sum(recent(x, rules['window_minutes']) for x in failures) >= rules['failed_count']:
                    reasons.append('Failed login burst before success'); value += 25
                if any(recent(x, rules['window_minutes']) for x in resets):
                    reasons.append('Password reset before success'); value += 15
                successes.append({**e, 'suspicious': value >= rules['alert_threshold']})
                devices.add(e['device_id']); countries.add(e['country'])
            elif kind == 'beneficiary_added':
                payees[e['beneficiary_id']] = e
            elif kind == 'transfer':
                login = next((x for x in reversed(successes) if x['device_id'] == e['device_id'] and recent(x, rules['followup_minutes'])), None)
                if e['amount'] >= rules['transfer_amount'] and login and login['suspicious']:
                    reasons.append('Large transfer after suspicious login'); value += 45
                payee = payees.get(e['beneficiary_id'])
                if e['amount'] >= rules['transfer_amount'] and payee and recent(payee, rules['followup_minutes']):
                    reasons.append('Large transfer to newly added beneficiary'); value += 35
            score = max(score, value)
            enriched.append({**e, 'event_score': min(100, value), 'reasons': reasons})
        score = min(100, score)
        transfers = [e for e in enriched if e['event_type'] == 'transfer']
        reasons = list(dict.fromkeys(r for e in enriched for r in e['reasons']))
        home = next((e['country'] for e in items if e['event_type'] == 'login_success'), items[0]['country'])
        accounts.append(dict(id=account_id, score=score, alert=score >= rules['alert_threshold'], severity='High' if score >= 70 else 'Review' if score >= rules['alert_threshold'] else 'Low', label=items[0]['is_ato'], events=enriched, reasons=reasons, exposure=sum(e['amount'] for e in transfers if e['event_score'] >= rules['alert_threshold']), total_transferred=sum(e['amount'] for e in transfers), home=home))
    return sorted(accounts, key=lambda a: (-a['score'], a['id']))

def metrics(accounts):
    labeled = [a for a in accounts if a['label'] is not None]
    tp = sum(a['alert'] and a['label'] == 1 for a in labeled)
    fp = sum(a['alert'] and a['label'] == 0 for a in labeled)
    fn = sum(not a['alert'] and a['label'] == 1 for a in labeled)
    tn = sum(not a['alert'] and a['label'] == 0 for a in labeled)
    return dict(tp=tp, fp=fp, fn=fn, tn=tn, labeled=len(labeled), alerts=sum(a['alert'] for a in accounts), precision=tp/(tp+fp) if tp+fp else None, recall=tp/(tp+fn) if tp+fn else None, exposure=sum(a['exposure'] for a in accounts))

def csv_export(rows, fields):
    out = io.StringIO()
    writer = csv.writer(out)
    def safe(x):
        s = '' if x is None else str(x)
        return "'" + s if re.match(r'^[=+\-@\t\r]', s) else s
    writer.writerow(fields)
    writer.writerows([[safe(r.get(f)) for f in fields] for r in rows])
    return out.getvalue()
