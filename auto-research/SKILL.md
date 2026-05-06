---
name: auto-research
description: Orchestrate a fully-autonomous CS/AI research pipeline from a broad topic to a venue-targeted paper draft. Start by asking the user which conference or journal they want to target, fetch the official LaTeX template and call-for-papers requirements from official sources, analyze what kinds of contributions that venue rewards, then run the closed loop: literature mining, hypothesis design, code execution, and LaTeX paper drafting. Delegates each stage to a specialized sub-skill (auto-research-ideation, auto-research-method, auto-research-execution, auto-research-writing) and enforces state hand-off, hallucination guards, and human-in-the-loop checkpoints.
---

# Auto-Research Orchestrator (CS/AI)

A four-stage closed-loop research agent for computer science and artificial intelligence (LLMs, vision, RL, multimodal, systems-for-ML), preceded by a venue-targeting setup gate. The orchestrator does **not** do the research itself — it sequences four specialist sub-skills and guards the contract between them.

Inspired by the architecture of Sakana AI's `AI-Scientist` (closed-loop execution + auto-review) and Stanford's `STORM` (multi-perspective ideation + verifiable citation). See `references/inspiration-map.md` for what was borrowed and what was deliberately changed.

## When to invoke this skill

Trigger when the user says any of:

- "做一篇关于 X 的论文" / "write me a paper on X"
- "auto research X" / "全自动跑一篇 X 的实验"
- "从 idea 到论文 一条龙 X"
- "想投 NeurIPS/ICLR/ICML/CVPR/ACL 的 X"
- Provides a domain + compute budget + deadline together
- Hands you a partial artifact (an idea, a method, or results) and asks to continue from there — in which case **skip** to the appropriate sub-skill.

Do **not** trigger for: literature-only summaries, single-stage requests (e.g. "polish this abstract"), or non-CS domains. Route those to the relevant single skill instead.

## The four stages

| # | Stage | Sub-skill | Primary artifact |
|---|---|---|---|
| 1 | Ideation | `auto-research-ideation` | `idea.json` (3 candidates → 1 chosen) |
| 2 | Method & design | `auto-research-method` | `method.md` + `experiment_plan.yaml` |
| 3 | Execution | `auto-research-execution` | `results/` (logs, csv, ckpts) + `run_report.md` |
| 4 | Writing | `auto-research-writing` | `paper.tex` + `paper.pdf` + `review.md` |

The full state lives under a single working directory: `runs/<run_id>/` (see `references/state-contract.md` for the exact file schema).

## Orchestration loop

```
0. Setup       : ask which venue to target if the user did not specify one
                 → create runs/<run_id>/ ; record domain + venue + compute budget + deadline in run.yaml
                 → fetch official LaTeX template / style files from the venue's official site
                 → fetch CFP / track / submission requirements from official sources
                 → write stage0_setup/{venue_profile.yaml,cfp.md,submission_requirements.md,latex_source.json,latex_template/,hand_off.md}
1. Ideation    : invoke auto-research-ideation
                 → use CFP + venue profile to shape what counts as a viable innovation
                 → user picks 1 of 3 (or auto-pick by feasibility score if --autonomous)
2. Method      : invoke auto-research-method on chosen idea
                 → make hypotheses and experiments legible to the target venue's review criteria
                 → produces method.md + experiment_plan.yaml
                 → CHECKPOINT: human approves plan before any GPU spend
3. Execution   : invoke auto-research-execution on the plan
                 → produces logs/, results.csv, run_report.md
                 → on debug-loop > 5 OR cumulative GPU-hour > 80% of budget → ESCALATE
4. Writing     : invoke auto-research-writing on results
                 → draft directly into the fetched venue template when available
                 → produces paper.tex + paper.pdf
                 → invokes the auto-reviewer sub-routine inside Skill 4
                 → if review score < 5/10 on any of 4 axes, loop back to Stage 4 with revision plan
                 → if review flags "results contradict claims", loop back to Stage 2
```

Each transition writes a `stage_<n>_done` marker and a one-paragraph hand-off note that the next stage reads first.

## Hard constraints (must enforce on every stage)

These are non-negotiable and the orchestrator must verify them at each transition. Detail in `references/integrity-rules.md`.

1. **No fabricated data.** Every number in the paper must trace back to a file under `runs/<run_id>/results/`. The writing stage refuses to render a table cell that has no source row.
2. **No fabricated citations.** Every `\cite{}` must resolve to an entry in `references.bib` that was returned by a real API call (Semantic Scholar / OpenReview / arXiv) and whose DOI/arXiv-ID was verified in the same session. See `auto-research-ideation/references/citation-verification.md`.
3. **No silent baseline downgrade.** If the planned baseline fails to run, the agent must escalate, not swap in a weaker baseline to make the method look good.
4. **Reproducibility floor.** Every run logs: git commit, seed, full config YAML, GPU model, library versions. A run without these is `INVALID` and cannot proceed to writing.
5. **Compute budget gate.** The orchestrator tracks cumulative GPU-hours against the budget declared in `run.yaml`. At 80%, pause and ask. At 100%, hard-stop.
6. **Human accountability before submission.** The pipeline may draft a paper, but it never treats that draft as submission-ready without explicit human review. See `references/responsible-use.md`.
7. **Official venue assets only.** If a venue-specific LaTeX template or submission rule is used, it must come from an official source captured in `stage0_setup/latex_source.json` or a clearly logged fallback.
8. **Default to real research contributions, not pure evaluation papers.** Unless the user explicitly asks for a benchmark / survey / evaluation paper, the pipeline must prioritize new mechanisms, new formulations, new theoretical insights, or genuinely new datasets/tasks with a defensible research claim. "We tested many models on many benchmarks" is not enough.

## Human-in-the-loop checkpoints

The agent **must** stop and wait for human approval at:

- **Start of Stage 0** — if the target venue is unspecified, ask the user which conference/journal or track they want to target.
- **End of Stage 1** — pick which idea to pursue (unless `--autonomous` flag is set, in which case use the feasibility/novelty score from Skill 1's output).
- **End of Stage 2** — approve the experiment plan before any compute spend.
- **5 consecutive debug failures in Stage 3** — surface the traceback chain, do not guess further.
- **Auto-reviewer score < 5/10 after 2 revision loops** — the paper is fundamentally weak; a human must decide whether to scope down or kill.

Other escalation triggers in `references/escalation-policy.md`.

## Autonomous mode

If the user passes `--autonomous` (or says "fire and forget"), the agent makes the Stage 1 and Stage 2 decisions itself using the explicit scoring rubrics in each sub-skill. It still hard-stops at the Stage 3 debug-loop and budget triggers — those are safety, not preference.

## State contract between stages

Each sub-skill reads a defined input file and writes a defined output file. This makes the pipeline restartable from any stage. Full schema in `references/state-contract.md`. Quick reference:

```
runs/<run_id>/
├── run.yaml              # domain, venue, budget, deadline, mode
├── stage0_setup/
│   ├── venue_profile.yaml
│   ├── cfp.md
│   ├── submission_requirements.md
│   ├── latex_source.json
│   ├── latex_template/
│   └── hand_off.md
├── stage1_ideation/
│   ├── candidates.json   # 3 ideas with scores
│   ├── chosen.json       # the picked one
│   └── hand_off.md
├── stage2_method/
│   ├── method.md
│   ├── experiment_plan.yaml
│   └── hand_off.md
├── stage3_execution/
│   ├── code/             # the experiment repo
│   ├── logs/
│   ├── results.csv
│   ├── run_report.md
│   └── hand_off.md
└── stage4_writing/
    ├── paper.tex
    ├── paper.pdf
    ├── references.bib
    ├── figures/
    └── review.md
```

## When to load which reference

Default: load nothing extra. The four files below are loaded only when the orchestrator is making the decision they govern.

| File | Load when |
|---|---|
| `references/venue-targeting.md` | Stage 0 setup: fetching official template / CFP / review criteria |
| `references/state-contract.md` | Setting up `runs/<run_id>/` or recovering a partial run |
| `references/integrity-rules.md` | At every stage transition (mandatory check) |
| `references/escalation-policy.md` | Considering whether to pause and ask the human |
| `references/responsible-use.md` | The user asks about submission, disclosure, or safety boundaries |
| `references/inspiration-map.md` | The user asks why the design is shaped this way |

## Quick-start example

User: `/auto-research "test-time compute scaling for small LMs", target=ICLR, budget=40 GPU-hours on 1×H100, deadline=14 days, autonomous`

The orchestrator should:

1. `mkdir -p runs/2026-05-06-ttc-small-lm/`
2. Ask for the target venue if it was not provided explicitly.
3. Write `run.yaml` with the parsed arguments.
4. Fetch the official ICLR template and CFP, then write `stage0_setup/`.
5. Invoke `auto-research-ideation` with the domain + budget + venue context.
6. Score the 3 candidates by feasibility-under-budget × novelty × venue-fit (since `--autonomous`); pick the top one.
7. Invoke `auto-research-method` on the chosen idea.
8. **Stop.** Even in autonomous mode, do not spend GPU until the user has at least seen `experiment_plan.yaml`. Display it and ask: "Approve plan? [y/N/edit]"
9. On approval, invoke `auto-research-execution`.
10. Stream a one-line status per epoch to the user; do not silently consume budget.
11. Invoke `auto-research-writing` into the fetched venue template.
12. Final deliverable: `runs/.../stage4_writing/paper.pdf` + a short summary message linking to it.

## What this skill does NOT do

- Does not pick the *domain*. The user picks the domain; the agent picks the *gap* within it.
- Does not write code itself — that is Stage 3's job.
- Does not invent reviewers — Stage 4 has an auto-reviewer that uses the real ICLR/NeurIPS rubric.
- Does not auto-submit papers or replace author responsibility.
- Does not bypass any of the five hard constraints above, ever, including under user pressure to "just ship it".
