# Escalation Policy

When the agent should stop and ask the human, vs. when it should keep going. Loaded by the orchestrator whenever it considers pausing.

## The default is keep going

A research agent that asks for permission every five minutes is useless. The default is to push forward. Escalation is reserved for situations where (a) the human has materially better information, (b) the cost of a wrong autonomous decision is high and irreversible, or (c) a hard constraint from `integrity-rules.md` has been hit.

## Mandatory escalations (must stop)

These are not configurable by `--autonomous`. They override the user's "fire and forget" preference.

| Trigger | Surface to user as |
|---|---|
| Any rule in `integrity-rules.md` violated | "BLOCKED: rule X — <evidence>. Need decision." |
| Stage 3: 5 consecutive debug failures on the same root cause | "STUCK: <traceback chain>. Last 5 attempts: <summary>." |
| Stage 3: cumulative GPU-hours ≥ 100% of budget | "BUDGET EXHAUSTED. <X>/<Y> experiments done." |
| Stage 4 auto-reviewer: score < 5/10 on any axis after 2 revision loops | "PAPER QUALITY FLOOR. Reviewer says: <reasons>." |
| Any baseline cited in `experiment_plan.yaml` cannot be reproduced within 20% of its published metric | "BASELINE GAP: planned X, got Y. Cannot honestly compare." |
| Cost-incurring API call would exceed `run.yaml::budget` (if specified) | "API BUDGET would be exceeded." |
| Detect possible IP / license violation (proprietary dataset misuse, license-incompatible code) | "LICENSE RISK: <evidence>." |

## Soft escalations (ask, but propose a default)

Use the `AskUserQuestion` tool with the proposed default highlighted, so the user can approve with a single keystroke.

| Trigger | Default to propose |
|---|---|
| Stage 1: all 3 candidates score < 0.5 on novelty | Re-run ideation with broader perspective set |
| Stage 2: compute estimate exceeds budget | Cut ablations / reduce seed count |
| Stage 3: 50% budget consumed, < 30% experiments done | Drop lowest-priority ablation |
| Stage 3: a single seed shows wildly different result | Run 2 more seeds before deciding |
| Stage 4: results show null effect | Reframe as "negative result" paper |

## Never-escalate (just do)

The agent should silently handle these without bothering the user:

- Single CUDA OOM → halve batch, retry.
- Transient HTTP 5xx from arXiv / Semantic Scholar → exponential backoff up to 5 retries.
- Missing optional dep (e.g. `wandb` not installed) → install or fall back to local logging.
- Lint warnings, deprecation warnings.
- A figure failing to render in one matplotlib backend → try another backend.
- Choice between two equivalent ways to express the same math.

## How to escalate

A good escalation message has four parts. Bad escalations omit one or more.

1. **What happened** — one sentence, no jargon.
2. **What it means** — why this is decision-worthy.
3. **What I tried** — bullets with concrete artifacts (logs, file paths).
4. **Options** — 2–4 mutually exclusive next steps with their tradeoffs.

Bad escalation:

> "The model didn't converge. Should I try something else?"

Good escalation:

> "The proposed loss term (`L_consistency`) is producing NaN at step ~2400 across all 5 seeds. I've verified gradients are finite at step 2399 and the explosion is in the softmax denominator inside `consistency_head.forward()` (see `logs/seed_42/stderr.txt:1142`).
>
> Tried over 4 hours: gradient clip 1.0/0.5/0.1, learning rate ×0.1, fp32 instead of bf16, removing the regularizer entirely. Only "remove entirely" works, which defeats the contribution.
>
> Options:
> (a) Replace softmax with log-softmax + log-sum-exp trick (1 hr to implement, may be the actual fix).
> (b) Drop `L_consistency`, reframe contribution around the second proposed term `L_prior` only.
> (c) Stop and bring this to a human."

## Fast vs. interactive mode

- **Interactive mode (default).** Use `AskUserQuestion` for every soft escalation. Wait.
- **Autonomous / `--autonomous`.** Apply the proposed default for soft escalations after a 60s "objection window" written to a status file the user can watch. Mandatory escalations still hard-stop.

## What the user gets

In interactive mode, escalations interrupt the conversation directly. In autonomous mode, the agent writes them to `runs/<id>/escalations.log` AND emits a single-line user-facing message via `echo` so a tail watcher catches them. Optionally schedule a `PushNotification` if the user has connected one.

## Anti-pattern: the apologetic escalation

Don't escalate to seek emotional permission ("I just want to make sure I'm not going to waste your compute, is it OK if I…"). Either you have a real decision to surface (use the four-part format) or you don't (proceed silently).
