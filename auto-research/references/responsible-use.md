# Responsible Use

This pipeline drafts research artifacts. It does not remove human responsibility.

## Core stance

- AI-generated papers are drafts, not final submissions.
- Named authors remain responsible for every claim, citation, table, and conclusion.
- Human review is mandatory before submission, public release, or external sharing as research evidence.

## Required human checks before submission

1. Verify every citation is real and contextually correct.
2. Verify every headline number against `results.csv` and `results_summary.json`.
3. Confirm the manuscript discloses AI assistance if the target venue or institution requires it.
4. Confirm limitations, failed hypotheses, and baseline caveats are not hidden.

## Disallowed uses

- Paper-mill style bulk generation.
- Concealing failed primary results behind weaker secondary wins.
- Submitting without a human reading the final manuscript.
- Using fabricated or unverifiable references.

## When the agent should escalate

- The user asks to hide a failed result.
- The user asks to invent or pad references.
- The user asks whether the draft can be submitted "as is".
- The venue's disclosure policy is unclear and the user asks for submission advice.
