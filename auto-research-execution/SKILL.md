---
name: auto-research-execution
description: Implement and run the experiments specified in a Stage 2 experiment plan, producing logs, results.csv, and a run report that Stage 4 (writing) can consume. Generates a Sakana-AI-Scientist-style template repo (experiment.py + plot.py + configs/), trains/evaluates with mixed precision and proper checkpointing, captures every metric to WandB or local TensorBoard, and runs a self-healing debug loop (capped at 5 attempts) for failed runs. Use when an experiment plan exists and needs to be executed end-to-end. Do NOT use for ad-hoc one-off scripts (use a normal coding session) or to design experiments (route to auto-research-method).
---

# Skill 3 — Automated Engineering & Ablation Execution

You are a senior ML research engineer. The experiment plan is a contract — your job is to translate it into a reproducible, instrumented, debuggable experiment that produces clean results for Stage 4. The plan should not change in your hands; if it must, you escalate.

Built on the template-trio pattern from Sakana AI's `AI-Scientist` (`templates/{nanoGPT,grokking,2d_diffusion}/`), with self-healing & sandboxing patterns adapted from AutoResearchClaw's CodeAgent.

## When to invoke

Trigger when:

- The orchestrator (`auto-research`) hands off Stage 3 with `experiment_plan.yaml` and `pseudocode.py` ready.
- A user has a written experiment plan and says: "run this experiment", "implement and execute", "do the training and evaluation."

Do NOT trigger when:

- No plan exists (route to `auto-research-method`).
- The user just wants you to debug their existing code (use a normal coding session).
- The experiment is purely conceptual / no code needed.

## Stage outputs

In `runs/<run_id>/stage3_execution/`:

```
code/                  # version-controlled experiment repo (init'd by this skill)
├── .git/
├── train.py / experiment.py
├── eval.py / plot.py
├── configs/
├── requirements.txt
└── README.md
logs/                  # WandB or TensorBoard mirror + stdout/stderr per run
results.csv            # one row per (config, seed)
results_summary.json   # mean ± std per metric per config
checkpoints/           # may be gitignored if too large
run_report.md          # what worked, what broke, deviations
hand_off.md            # 1-paragraph note for Stage 4
```

The four critical files for Stage 4 are: `results.csv`, `results_summary.json`, `run_report.md`, `hand_off.md`.

## Workflow (6 phases)

### Phase 1 — Read the plan, scaffold the repo

Read `runs/<run_id>/stage2_method/experiment_plan.yaml`, `method.md`, `pseudocode.py`, and `hand_off.md`. From the plan, decide which template to start from (see `references/template-selection.md`):

- `nanoGPT-style` for LM training / fine-tuning experiments.
- `hf-trainer-style` for general fine-tuning with HuggingFace Transformers / TRL.
- `vision-clf-style` for image classification / detection / segmentation.
- `rl-style` for reinforcement learning (gym / pettingzoo).
- `eval-only-style` for inference-only studies (no training, just evaluating off-the-shelf models).
- `from-scratch` only if no template fits.

Initialize the repo from `assets/templates/<chosen>/` into `runs/<run_id>/stage3_execution/code/` and `git init` it. The first commit is "scaffold from <template>" — every subsequent change should be a separate commit, so `git_commit` per run actually means something (Rule 4).

### Phase 2 — Implement the method

Adapt the template by writing the proposed method (from `pseudocode.py`) into the template's `experiment.py` (or equivalent). Follow:

- **OOP boundaries.** Method = a class. Hyperparameters = a dataclass / Pydantic model. NO hardcoded constants in method-body code.
- **Configuration.** All knobs in a YAML config under `configs/`. The config is what `experiment_plan.yaml::seeds` etc. will index.
- **Determinism.** See `references/reproducibility.md`. Every random source seeded.
- **Logging.** Initialize WandB (or TensorBoard) at run start. Log: config, git commit, hardware, every metric every N steps.

See `references/code-style.md` for boundaries and `references/template-selection.md` for which template to pick.

### Phase 3 — Wire up baselines

For each baseline in `experiment_plan.yaml::baselines`:

- If `must_reproduce: true`, find or write a runnable implementation of the baseline. Prefer the original authors' code, with attribution.
- Reproduction must land within ±20% of `expected_metric` from the plan. If not, see `references/baseline-debug.md`.
- Each baseline gets its own config under `configs/baselines/`.

Failure to reproduce a baseline within tolerance is a Stage-3 escalation per `auto-research/references/escalation-policy.md::baseline_failure`. Do NOT silently swap in a weaker baseline.

### Phase 4 — Execute (with monitoring)

Launch runs. Use `assets/scripts/launch_runs.py` (or a similar pattern) to drive the matrix of (config × seed). For each run:

- Open WandB / TensorBoard scope.
- Pin `git_commit`, `seed`, `config_name`, `gpu_hours_so_far`, hardware string.
- Train; checkpoint; eval; close scope.
- Append row to `results.csv` (per columns specified in `state-contract.md`).

The training-monitor (`references/training-monitor.md`) watches for:

- **NaN / Inf in loss** → halt, log, escalate to debug loop.
- **Loss not decreasing** for > 100 steps after warmup → halt, log, escalate.
- **CUDA OOM** → halve batch size, restart (max 3 attempts).
- **Hang** > 5× expected step time → kill + retry once.

Stream a **one-line-per-N-steps** status to the user (visible in CLI). Do not silently consume budget.

### Phase 5 — Self-healing debug loop

When a run errors out, the debug loop kicks in. See `references/debug-loop.md` for the full protocol:

```
attempt 1: read traceback, identify root cause class, propose fix, apply, retry
attempt 2-4: vary hypothesis, retry
attempt 5: ESCALATE — surface full traceback chain to user
```

**Hard cap: 5 attempts on the same root cause.** This is integrity rule 7. After 5, the orchestrator stops the entire run and surfaces.

Auto-recoverable without escalation:

- CUDA OOM (handled by training-monitor).
- Transient HTTP failures (exp backoff, max 5 tries).
- Single-seed hang (kill & rerun once).

### Phase 6 — Aggregate, report, hand off

After all runs complete (or budget exhausted):

1. Build `results.csv` (raw rows) and `results_summary.json` (mean ± std per config per metric).
2. Render plots from `plot.py` into `figures/` for Stage 4 to use.
3. Write `run_report.md` per the template in `references/run-report-template.md`. This is required reading for Stage 4.
4. Write `hand_off.md`: headline number, what to lead with, what failed (if anything).

The orchestrator validates `results.csv` against integrity rules 3 & 4 (no silent baseline downgrade; reproducibility floor) before allowing Stage 4 to begin.

## Hard rules for this stage

1. **Plan is the contract.** `experiment_plan.yaml` may not be silently edited. Any deviation is logged in `run_report.md::Deviations from plan` with reason.
2. **Reproducibility floor.** Every `results.csv` row has `git_commit, seed, config_name, gpu_hours, hardware` (Rule 4).
3. **No silent baseline downgrade.** If a baseline fails reproduction → debug or escalate, never swap (Rule 3).
4. **Compute budget gate.** Track GPU-hours continuously. Warn @50%, ask @80%, hard-stop @100% (Rule 5).
5. **Sandbox for LLM-written code.** New code is AST-checked before execution (see `references/sandbox.md`). Forbidden imports / exec / eval / network without justification.
6. **No HARK-ing in Stage 3.** The hypothesis / success criteria from `experiment_plan.yaml` are read-only during this stage. Only Stage 4 (writing) handles unexpected results, and it does so via Limitations section, not by editing the hypothesis.
7. **Debug loop cap.** 5 consecutive failures on the same root cause → escalate (Rule 7).

## When to load which reference

| File | Load when |
|---|---|
| `references/template-selection.md` | Phase 1 (picking the right template) |
| `references/code-style.md` | Phase 2 (writing the method into the template) |
| `references/reproducibility.md` | Phase 2 + before any run (seed / config / git discipline) |
| `references/training-monitor.md` | Phase 4 (configuring per-run monitoring) |
| `references/debug-loop.md` | A run errored out (Phase 5) |
| `references/baseline-debug.md` | A baseline failed reproduction in Phase 3 |
| `references/sandbox.md` | Before executing newly-LLM-written code |
| `references/wandb-conventions.md` | Setting up logging |
| `references/run-report-template.md` | Phase 6 (writing run_report.md) |
| `references/cuda-oom-recovery.md` | OOM handling specifically |

Default: load `template-selection.md` and `reproducibility.md` first; load others on demand.

## Templates available

| Template | When to use | Key files |
|---|---|---|
| `assets/templates/nanoGPT-style/` | Pretraining or fine-tuning small LMs from scratch | `experiment.py`, `train.py`, `model.py`, `configs/{model,data,train}.yaml` |
| `assets/templates/hf-trainer-style/` | Fine-tuning HF models (LoRA, full FT, RLHF) | `experiment.py`, `train.py`, `prompts/`, `configs/sft.yaml` |
| `assets/templates/vision-clf-style/` | Image classification / detection | `experiment.py`, `model.py`, `data.py`, `configs/imagenet.yaml` |
| `assets/templates/rl-style/` | RL / RLHF training | `experiment.py`, `agent.py`, `env.py`, `configs/ppo.yaml` |
| `assets/templates/eval-only-style/` | Inference-only studies | `experiment.py` (just `eval.py`), `prompts/` |

Each template has its own README with what to swap, what to leave. Templates are starting points — you adapt, you do not rewrite from scratch.

## Anti-patterns this skill prevents

- **Quietly swapping a failing baseline for a weaker one.** Caught by Rule 3 + baseline-debug protocol.
- **NaN losses silently producing junk results.** Caught by training-monitor sentinel.
- **One-off "magic" hyperparameters in code.** Caught by code-style enforcement (config-only).
- **Unreproducible runs (no seed, no commit, no hardware).** Caught by reproducibility lint at end of stage.
- **Infinite debug loops eating budget.** Caught by 5-attempt cap.
- **Compute overrun.** Caught by 50/80/100 gates.
- **HARKing.** Caught by hypothesis lock at Stage 2 → Stage 3 transition.
