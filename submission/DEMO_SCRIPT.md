# Account takeover project demo

Target duration: 4 minutes 30 seconds. Record your voice and the running application. This script is prepared narration; it is not evidence that a narrated video has already been recorded.

## 0:00–0:30 Problem and project

“I chose Path 3 and built ATO Investigator, an account takeover investigation app. Fraud analysts need to connect login behavior, credential changes, and money movement into a single account story. I used Codex to build a working Streamlit app with explainable detection rules and synthetic data.”

Show the overview. Explain that no real customer data is included.

## 0:30–1:00 Overview

“The sample contains 80 fictional accounts and 1,578 events. The default rules flag 22 accounts. The dashboard shows account activity, detection signals, and a prioritized queue. Flagged transfer value is exposure for review, not confirmed fraud loss.”

Briefly filter home country to US, show the count update, and reset.

## 1:00–2:00 Investigate the attack sequence

Open Account investigation and choose ACC-0001. Turn Signals only off to show all activity. Scroll the timeline table to October 11.

“This account has four failed logins, followed by a password reset, a successful login from a new device and country, a new beneficiary, and a $6,322 transfer. The successful login and transfer each score 80. The account score is the highest event score, not a fraud probability.”

Turn Signals only on. Enter a short note and select Escalated, then Save case notes.

“The reasons are visible, and I can record my investigation outcome. Notes are saved for the current Streamlit session and can be exported.”

## 2:00–2:40 Show a benign lookalike

Go to Account investigation, choose ACC-0013, and reveal synthetic ground truth.

“This legitimate traveler triggers new-device and new-country signals. It demonstrates why an alert needs investigation rather than being treated as proof of fraud.”

Reset the filters.

## 2:40–3:25 Compare detection settings

Open Detection playground. Raise Account alert threshold from 40 to 70 and click Apply rules.

“Alerts drop from 22 to 8. The 14 benign alerts disappear in this synthetic example, but recall remains 8 out of 12 takeovers. Four low-signal takeovers are still missed. This shows the limits of the available signals; these results are not a production performance claim.”

Optionally restore defaults, select All accounts in Investigate accounts, and search ACC-0009 to reveal a missed takeover.

## 3:25–4:00 Data and vibe coding

Open Data & methodology and point to Upload CSV and the schema.

“The app accepts an activity CSV and validates its columns, timestamps, amounts, and account labels. Labels are optional and used only for evaluation. I defined the problem with Codex, then iterated through synthetic data generation, detection rules, interface development, validation, and screenshots.”

Show the tests or report briefly. Only claim work or iterations you can explain from this conversation and the actual code.

## 4:00–4:30 Learnings and close

“The main learnings were to keep labels out of scoring, explain metric definitions, and include benign scenarios and missed attacks. Nine Python engine tests and five Streamlit AppTest workflows verify the key behavior. A future version could add approved data, MFA events, and a more complete analyst workflow. The code and documentation are included with the submission.”

## Recording checklist

- Use a desktop browser with a readable zoom level and reset filters/rules before starting.
- Keep the video at five minutes or less.
- Include live interaction, not only screenshots.
- Record yourself explaining the problem and use of Codex.
- Upload to Loom or another shareable video host; verify viewer access.
- Run `streamlit run app.py` and record the Streamlit URL. The old private Site is a historical static prototype; do not use it for the final Streamlit demo.

## Show the coding process

Use about 20 seconds of the data/workflow section to open Vibe coding build journal. Show Actual prompts, Build steps, and Code and tests. These pages contain real recorded messages and executed validation output. They are rendered journal evidence rather than original Codex UI screenshots.
