# Development record

## Actual user instructions in this conversation

1. “Hi Codex - Need help with project suggestions for my project. Here are the guidelines. I prefer picking path-3 and I need ideas to build something in fraud domain that I work on for this project.”
2. “I want to pick account takeover project and would need help building the project end to end for submission.”
3. In response to the repository question: “Create a new public repository.”

## Implementation steps completed by Codex

1. Read the supplied Week 1 guidelines and identify Path 3 deliverables.
2. Inspect the empty workspace and select a static browser app so the core runtime has no package installation dependency.
3. Generate 1,578 events for 80 fictional accounts with six scenario groups and seed 42.
4. Implement chronological detection rules in a separate JavaScript module. Keep labels and scenario text out of scoring.
5. Build overview charts, the review queue, account timelines, case notes, rule controls, and CSV validation/import/export.
6. Add nine tests for meaningful detection and data-handling behavior. All pass.
7. Start a local HTTP server. The sandbox initially blocked socket binding; the server was started after native permission approval.
8. Run headless browser QA. The default Playwright browser executable was unavailable; use the installed Chrome executable after native approval.
9. Verify thirteen browser behaviors and capture five screenshots.
10. Review the captured images, improve small-screen table scrolling and timeline controls, and change slider result updates to occur on release so dragging remains usable.
11. Prepare documentation and a demo narration script. Registration created an owner-private Site; publication status is tracked separately in the final handoff.

## Reusable follow-up prompts

These are suggested prompts for your own iterations, not a claim that you sent them during this build.

- “Add MFA challenge and recovery events to the dataset and explain how they change the account takeover investigation.”
- “Show a session-level timeline that distinguishes existing trusted devices from new devices, using only earlier events to build the baseline.”
- “Add a rule comparison view with a review-capacity budget, while keeping synthetic labels separate from detection features.”
- “Review my CSV schema and identify missing fields needed to evaluate account takeover with approved historical data.”

## Evidence to add personally

Capture screenshots of the initial project selection and build request in this Codex conversation, plus one implementation/testing update. Add your own observations about the app and any subsequent prompts. Do not describe suggested prompts as actual history.
