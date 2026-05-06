# State Contract Between Stages

The four sub-skills communicate exclusively through files under `runs/<run_id>/`. This makes the pipeline restartable, auditable, and parallelizable. **Never** pass implicit state in the conversation context — write it to disk.

## Top-level layout

```
runs/<run_id>/
├── run.yaml
├── stage1_ideation/
├── stage2_method/
├── stage3_execution/
└── stage4_writing/
```

`<run_id>` format: `YYYY-MM-DD-<slug>` where slug is a 4–6 word kebab-case summary of the domain (e.g. `2026-05-06-ttc-small-lm`).

## `run.yaml`

Written by the orchestrator at Stage 0. Read by every subsequent stage.

```yaml
run_id: 2026-05-06-ttc-small-lm
domain: "test-time compute scaling for small LMs"
created_at: 2026-05-06T14:32:00Z
budget:
  gpu_hours: 40
  hardware: "1xH100-80GB"
  wall_clock_days: 14
deadline: 2026-05-20
mode: autonomous          # or interactive
constraints:
  - "no closed-source models"
  - "results must be reproducible from a single seed"
human_contact: kanella_hatleli588@mail.com
```

## Stage 1 — `stage1_ideation/`

```
stage1_ideation/
├── candidates.json       # all 3 brainstormed ideas with scores
├── chosen.json           # the one we proceed with
├── literature_pool.json  # the verified papers used during ideation
└── hand_off.md           # 1 paragraph: "what stage 2 needs to know"
```

### `candidates.json` schema

```json
{
  "generated_at": "ISO-8601 timestamp",
  "perspectives_used": ["theorist", "engineer", "skeptic", "industry-pm"],
  "candidates": [
    {
      "id": "C1",
      "title": "string, ≤120 chars",
      "pain_point": "the limitation in prior work this solves",
      "key_intuition": "1–2 sentence why-this-might-work",
      "expected_baseline": "name + arxiv id of the SOTA we'll beat",
      "novelty_score": 0.0,        // 0–1 from rubric
      "feasibility_score": 0.0,    // 0–1 from rubric (compute-aware)
      "expected_compute_hours": 0,
      "risk_factors": ["bullet 1", "bullet 2"],
      "supporting_citations": ["semantic_scholar:1234", "arxiv:2401.00000"]
    }
  ]
}
```

### `chosen.json`

A copy of one candidate from `candidates.json` plus `chosen_by` (`human` | `auto`) and `chosen_reason`.

## Stage 2 — `stage2_method/`

```
stage2_method/
├── method.md             # narrative + math
├── experiment_plan.yaml  # machine-readable plan
├── pseudocode.py         # algorithm in pure Python (not runnable)
└── hand_off.md
```

### `experiment_plan.yaml` schema

```yaml
hypothesis: "string — testable, falsifiable"
datasets:
  - name: "MMLU"
    split: "test"
    size: 14042
    license: "MIT"
    download_url: "https://..."
baselines:
  - name: "method X"
    paper: "arxiv:2403.xxxxx"
    expected_metric: {accuracy: 0.74}
    must_reproduce: true
metrics:
  primary: "accuracy"
  secondary: ["calibration_ece", "wall_clock_inference_s"]
ablations:
  - name: "remove component A"
    expected_drop: ">= 2 pp"
  - name: "remove component B"
    expected_drop: ">= 1 pp"
compute_estimate:
  total_gpu_hours: 35
  per_run_hours: 1.5
  num_runs: 23   # 5 seeds × main + ablations
seeds: [13, 42, 123, 1234, 7777]
success_criteria:
  - "primary metric >= baseline + 2pp on at least 3/5 seeds"
  - "no ablation removes more than 50% of the gain"
failure_criteria:
  - "primary metric < baseline on majority of seeds → kill, do not paper-wash"
```

## Stage 3 — `stage3_execution/`

```
stage3_execution/
├── code/                 # actual repo, version-controlled
│   ├── .git/
│   ├── train.py
│   ├── eval.py
│   ├── configs/
│   ├── requirements.txt
│   └── README.md
├── logs/
│   ├── wandb/            # or tensorboard/
│   └── stdout/
├── results.csv           # one row per (config, seed)
├── results_summary.json  # mean ± std per metric per config
├── checkpoints/          # may be gitignored if too large
└── run_report.md         # what worked, what broke, what was changed from plan
```

### `results.csv` minimum columns

```
run_id, config_name, seed, git_commit, gpu_hours, primary_metric, [secondary_metrics...], notes
```

### `run_report.md` required sections

- **Executed as planned**: list of plan items completed verbatim.
- **Deviations from plan**: any hyperparameter / dataset / baseline change, with reason.
- **Failed runs**: tracebacks, what was tried.
- **Compute consumed**: GPU-hours actual vs. planned.
- **Headline number**: one sentence the writing stage will lead with.

## Stage 4 — `stage4_writing/`

```
stage4_writing/
├── paper.tex
├── paper.pdf
├── references.bib
├── figures/
│   ├── teaser.pdf
│   ├── pipeline.pdf
│   └── results_main.pdf
├── tables/
│   └── main_results.tex
└── review.md             # auto-reviewer output
```

### `review.md` required sections

Per the rubric in `auto-research-writing/references/auto-reviewer.md`:

```
Score: contribution X/10 | clarity X/10 | soundness X/10 | significance X/10
Overall: <accept | weak accept | borderline | weak reject | reject>

Strengths:
- ...

Weaknesses:
- ...

Required revisions before resubmit:
- [ ] specific actionable item with file:line reference
```

## Hand-off notes (`hand_off.md`)

Each stage writes one of these for the next stage. Strict format:

```markdown
# Hand-off: stage N → stage N+1

## What was decided
<2–4 bullets>

## Open questions for the next stage
<bullets — things explicitly NOT decided that the next stage must resolve>

## Don't-touch list
<bullets — decisions upstream stages must NOT silently revise>

## Files the next stage must read first
- relative/path/to/file
```

The next stage's first action is to `Read` this file.

## Restart semantics

- Re-running `auto-research` on an existing `runs/<run_id>/` resumes from the latest `stage_N_done` marker.
- To force restart from a stage: delete that stage's directory.
- To rerun only stage K: invoke `auto-research-<stage-k-name>` directly with `--run-id <run_id>`.
