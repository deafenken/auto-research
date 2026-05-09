# auto-research-frontend — Claim-to-Evidence Inspector

A static SPA that visualises an `auto-research` run. The MVP view aligns
every numeric claim and `\cite{}` in `paper.tex` to its evidence:

| Underline      | Status                | Source                                        |
|----------------|------------------------|-----------------------------------------------|
| solid green    | VERIFIED               | `claims_ledger.jsonl` / `results_summary.json`|
| dashed orange  | VERIFIED-PRIOR-WORK    | abstract of a paper cited within 30 chars     |
| wavy red       | UNTRACED               | nothing matched — Rule 1 violation            |

This frontend reads only files that already exist in the repo's run
contract (`auto-research/references/state-contract.md` v2). It never
talks to a backend.

## Build

```bash
cd auto-research-frontend
npm ci          # install pinned deps once
npm run build   # → dist/  (static, no Node runtime needed at serve time)
```

Vite is configured with `base: './'`, so `dist/` works from any path.

> The auto-research VPS does not have Node/npm and isn't supposed to.
> Build the bundle on a developer machine and `rsync` it over.

## Stage into a run

`auto-research-writing/assets/scripts/build_dashboard.py` does this for you:

```bash
python ../auto-research-writing/assets/scripts/build_dashboard.py \
    --run-dir runs/2026-05-09-my-paper
cd runs/2026-05-09-my-paper/_dashboard && python -m http.server 8000
# open http://localhost:8000/
```

## Develop offline (no real run)

```bash
npm run dev
# open http://localhost:5173/?fixture=dirty
```

`?fixture=` selects one of:

* `clean`   — full happy path; all green underlines
* `dirty`   — citation + number violations from `lint_report.md`
* `partial` — `claims_ledger.jsonl` + `results_summary.json` missing
* `empty`   — only `paper.tex` + `run.yaml` — bare-bones rendering

Fixtures are kept in sync with `auto-research-writing/assets/scripts/tests/fixtures/`
so the linter and the Inspector exercise the same artifacts.

## Scope

This is the MVP. Additional views (pipeline timeline, idea-debate
viewer, live run monitor, auto-reviewer diff) are deliberately deferred —
see the implementation plan at
`/home/winbeau/.claude/plans/agent-drifting-tiger.md`.
