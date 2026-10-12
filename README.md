# ATO Investigator — Streamlit

A Week 1 Path 3 data application for investigating account takeover. **The primary app is now Python and Streamlit (`app.py`).** The earlier static demo and JavaScript assets in `dist/` are retained as development history; they are not the final Streamlit submission. The synthetic data in `dist/data/` is reused by the Python app.

## Run the Streamlit app

Requires Python 3.11 or newer. Tested with Python 3.14, Streamlit 1.65.0, pandas 3.0.6, and Plotly 7.1.0.

```bash
git clone https://github.com/naspter333/ato_investigator.git ato-investigator
cd ato-investigator
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the URL printed by Streamlit, normally http://localhost:8501. Streamlit uses Python on a server and displays its interface in a browser. This is a real Streamlit application, not the earlier static HTML app.

## Views

- **Overview:** shared cohort filters, metrics, Plotly charts, account queue, alert CSV export.
- **Account investigation:** account selector, chronological timeline, evidence, optional label reveal, review outcomes, session notes, timeline and note downloads.
- **Detection playground:** configurable thresholds and time windows, Apply rules form, confusion matrix, default-versus-current comparison.
- **Data and methodology:** schema, current dataset download, data-processing semantics, limitations.
- **Vibe coding build journal:** actual conversation prompts, twelve build steps, source artifacts, executed test output, and observed iterations.

## Data and rules

The included CSV and JSON contain 1,578 events for 80 fictional accounts from October 1–11, 2026 UTC. Regenerate with `python scripts/generate_data.py`; seed 42 reproduces the data. All amounts are USD; IP addresses use the documentation range 192.0.2.0/24. Scenarios include 8 strong-signal takeovers, 4 low-signal takeovers, 8 legitimate travelers, 6 password recoveries, 6 new phones, and 48 routine accounts.

Required columns: `event_id`, `account_id`, `timestamp`, `event_type`, `device_id`, `country`, `ip_address`, `amount`, `beneficiary_id`. Optional: `is_ato` (consistent 0/1 label per account) and `scenario`. Uploads are limited to 10 MB and 50,000 events.

At successful login: new device +20, new country +20, recent failed-login burst +25, recent password reset +15. At transfer: large transfer after a suspicious login on the same device +45, large transfer to a recently added beneficiary +35. Scores on an event add together; the account score is the highest event score, capped at 100. The first successful login establishes the initial baseline. Equal-time events use event ID order. Labels and scenario text are never scoring features.

The account threshold also defines which login is suspicious for a follow-up transfer. Default rules flag 22 accounts: 8 true positives, 14 false positives, 4 false negatives, and 54 true negatives. Threshold 70 flags 8 accounts: 8 true positives, 0 false positives, 4 false negatives, and 68 true negatives. These are engineered synthetic examples, not production benchmarks.

Dates select accounts with any activity in the selected UTC window. Home country is the first-successful-login country (or first-event country if there is no successful login). Rules, account timelines, exposure, and evaluation use full available account history. Only the overview daily chart restricts events to selected dates. Flagged transfer value is rule-flagged exposure, not confirmed loss. Precision and recall exclude unlabeled accounts and show N/A for zero denominators.

## Session and upload behavior

CSV files are sent to the Streamlit server for Python processing. Running locally keeps processing on your computer; deploying to a host processes data on that server. Use the supplied synthetic data for this project. Do not infer that hosted uploads stay solely in the browser.

Case notes persist across reruns in the current Streamlit session and are scoped to the dataset. Export them as JSON before ending the session. There is no durable database or multi-user workflow. Uploaded datasets and rule settings are also session-scoped.

## Validation

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

Fourteen tests cover nine Python engine behaviors and five Streamlit AppTest workflows: overview/cohort filters/empty results, investigations and notes, rule comparisons, the schema view, and the process journal. The saved command and output are in `submission/streamlit_validation.json`. Older JavaScript/browser checks apply only to the initial static prototype.

## Submission materials

- `submission/Account_Takeover_Project_Report.docx`: revised report with actual prompts, full build steps, Streamlit process screenshots, validation, and app views.
- `submission/process_journal.json`: actual messages and implementation history, clearly separated from source code decisions.
- `submission/screenshots/streamlit/`: captures of the live Streamlit app and its build journal.
- `submission/DEMO_SCRIPT.md`: live walkthrough of five minutes or less.
- `submission/SUBMISSION_CHECKLIST.md`: remaining Google Doc, narrated video, and form steps.

Journal screenshots render actual recorded messages, artifacts, and executed outputs. They are not screenshots of the original Codex chat UI; automated capture of that UI was blocked. Add original conversation screenshots manually if your evaluator requires original chat UI evidence. No suggested prompts are presented as messages actually sent.

## Optional Streamlit hosting

Deploy this GitHub repository on Streamlit Community Cloud using branch `main` and entrypoint `app.py`; `requirements.txt` supplies the dependencies. This deployment requires your Streamlit account and is not completed automatically here. The prior chatgpt.site URL still serves the initial static prototype and should not be presented as the final Streamlit app.

## Source layout

```text
app.py                         Primary Streamlit entrypoint
fraud_engine.py                Python detection, validation, and metrics
requirements.txt               Runtime dependency pins
.streamlit/config.toml         Theme, upload limit, telemetry setting
tests/test_fraud_engine.py     Nine Python engine tests
tests/test_streamlit_app.py    Five AppTest workflows
scripts/generate_data.py      Reproducible synthetic data
dist/data/                     Shared synthetic CSV and JSON
submission/                    Report, process journal, screenshots, demo
```

The historical browser assets are retained for traceability. The app does not train a model, enforce MFA, block transfers, infer travel speed, or contact customers.
