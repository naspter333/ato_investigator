import json
import unittest
from pathlib import Path
from fraud_engine import analyze, csv_export, metrics, parse_csv, validate_events

SAMPLE=json.loads((Path(__file__).resolve().parents[1]/'dist/data/events.json').read_text())

class EngineTests(unittest.TestCase):
    def test_default_outcomes(self):
        m=metrics(analyze(validate_events(SAMPLE)))
        self.assertEqual((m['tp'],m['fp'],m['fn'],m['tn']),(8,14,4,54))
        self.assertEqual(m['exposure'],35118)
    def test_threshold_tradeoff(self):
        m=metrics(analyze(validate_events(SAMPLE),{'alert_threshold':70}))
        self.assertEqual((m['tp'],m['fp'],m['fn'],m['tn']),(8,0,4,68))
    def test_labels_do_not_affect_scores(self):
        original=analyze(validate_events(SAMPLE))
        changed=analyze(validate_events([{**e,'is_ato':1,'scenario':'irrelevant'} for e in SAMPLE]))
        self.assertEqual([(a['id'],a['score'],a['exposure']) for a in original],[(a['id'],a['score'],a['exposure']) for a in changed])
    def test_future_context_excluded(self):
        first=next(e for e in SAMPLE if e['account_id']=='ACC-0033' and e['event_type']=='login_success')
        future={**first,'event_id':'FUTURE','event_type':'password_reset','timestamp':'2026-10-12T10:00:00Z'}
        self.assertEqual(analyze(validate_events([future,first]))[0]['events'][0]['event_score'],0)
    def test_expired_failures(self):
        rows=[dict(e) for e in SAMPLE if e['account_id']=='ACC-0021']
        last=next(e for e in reversed(rows) if e['event_type']=='login_success')
        last['timestamp']='2026-10-11T15:00:00Z'
        self.assertEqual(analyze(validate_events(rows))[0]['score'],0)
    def test_missing_labels(self):
        rows=[{k:v for k,v in e.items() if k!='is_ato'} for e in SAMPLE]
        m=metrics(analyze(validate_events(rows)))
        self.assertIsNone(m['precision']);self.assertIsNone(m['recall']);self.assertEqual(m['labeled'],0)
    def test_csv_quoting(self):
        row={**SAMPLE[0],'scenario':'Travel, then "new phone"\nVerified'}
        self.assertEqual(parse_csv(csv_export([row],list(row)))[0]['scenario'],row['scenario'])
    def test_validation(self):
        for updates in [{'amount':-1},{'timestamp':'2026-02-30T10:00:00Z'},{'event_type':'unknown'},{'is_ato':7}]:
            with self.subTest(updates=updates),self.assertRaises(ValueError):validate_events([{**SAMPLE[0],**updates}])
        with self.assertRaises(ValueError):validate_events([SAMPLE[0],SAMPLE[0]])
        with self.assertRaises(ValueError):parse_csv('a,a\nx,y')
    def test_export_formula_guard(self):
        self.assertIn("'=HYPERLINK",csv_export([{'id':'=HYPERLINK("bad")'}],['id']))

if __name__=='__main__':unittest.main()
