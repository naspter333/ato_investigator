import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP=Path(__file__).resolve().parents[1]/'app.py'

class StreamlitTests(unittest.TestCase):
    def setUp(self):self.app=AppTest.from_file(str(APP),default_timeout=30).run()
    def clean(self):self.assertEqual(len(self.app.exception),0,str(self.app.exception))
    def test_overview_and_filters(self):
        self.clean();self.assertEqual(self.app.metric[0].value,'80');self.assertEqual(self.app.metric[1].value,'22')
        self.app.selectbox(key='home_country').set_value('US').run();self.clean();self.assertEqual(self.app.metric[0].value,'20')
        self.app.text_input(key='account_search').set_value('NO-MATCH').run();self.clean();self.assertEqual(self.app.metric[0].value,'0')
    def test_investigation_and_notes(self):
        self.app.radio(key='workspace_view').set_value('Account investigation').run();self.clean();self.assertEqual(self.app.metric[0].value,'80')
        self.app.selectbox[0].set_value('ACC-0013').run();self.clean();self.assertEqual(self.app.metric[0].value,'40')
        self.app.text_area[0].set_value('Travel verified')
        next(b for b in self.app.button if b.label=='Save case notes').click().run();self.clean()
        self.assertTrue(any(x['text']=='Travel verified' for x in self.app.session_state['notes'].values()))
    def test_rule_comparison(self):
        self.app.radio(key='workspace_view').set_value('Detection playground').run();self.clean()
        next(s for s in self.app.slider if s.label=='Account alert threshold').set_value(70)
        next(b for b in self.app.button if b.label=='Apply rules').click().run();self.clean()
        self.assertEqual(self.app.metric[0].value,'8');self.assertEqual(self.app.metric[1].value,'0');self.assertEqual(self.app.metric[2].value,'4')
    def test_data_view(self):
        self.app.radio(key='workspace_view').set_value('Data and methodology').run();self.clean();self.assertEqual(len(self.app.dataframe),1)
    def test_process_journal(self):
        self.app.radio(key='workspace_view').set_value('Vibe coding build journal').run();self.clean()
        self.assertTrue(any('Please go ahead with Streamlit.' in x.value for x in self.app.code))
        self.app.radio(key='journal_evidence').set_value('Code and tests').run();self.clean()
        self.assertTrue(any('def analyze' in x.value for x in self.app.code))

if __name__=='__main__':unittest.main()
