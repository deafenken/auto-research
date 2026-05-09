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

This project uses **pnpm** (declared via `package.json::packageManager`).
Install pnpm once if you don't have it:

```bash
npm install -g pnpm
# or, with corepack (bundled with Node 16+):
corepack enable && corepack prepare pnpm@latest --activate
```

Then:

```bash
cd auto-research-frontend
pnpm install     # first run creates pnpm-lock.yaml; subsequent runs are reproducible
pnpm build       # → dist/  (static, no Node runtime needed at serve time)
```

After the lock file is generated, commit it so CI / teammates get
reproducible installs (`pnpm install --frozen-lockfile`).

Vite is configured with `base: './'`, so `dist/` works from any path.

> The auto-research VPS does not run pnpm install (1.9 GB RAM, shared).
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
pnpm dev
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
