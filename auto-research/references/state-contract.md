# State Contract Between Stages

The four sub-skills communicate exclusively through files under `runs/<run_id>/`. This makes the pipeline restartable, auditable, and parallelizable. **Never** pass implicit state in the conversation context — write it to disk.

## Top-level layout

```
runs/<run_id>/
├── run.yaml
├── stage0_setup/
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
target_venue:
  name: "ICLR 2027"
  track: "Main Conference"
  source_url: "https://..."
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

## Stage 0 — `stage0_setup/`

```
stage0_setup/
├── venue_profile.yaml
├── cfp.md
├── submission_requirements.md
├── latex_source.json
├── latex_template/
└── hand_off.md
```

### `venue_profile.yaml` schema

```yaml
venue:
  name: "ICLR 2027"
  track: "Main Conference"
  official_url: "https://..."
  template_url: "https://..."
review_emphasis:
  - "novel algorithmic contribution"
  - "strong empirical validation"
avoid_patterns:
  - "incremental benchmark chasing without insight"
  - "insufficient ablations"
format_constraints:
  page_limit: 9
  anonymized: true
  style: "iclr"
```

## Stage 1 — `stage1_ideation/`

```
stage1_ideation/
├── candidates.json       # all 3 brainstormed ideas with scores
├── chosen.json           # the one we proceed with
├── literature_pool.json  # the verified papers used during ideation
├── persona_notes/        # one JSON per STORM-style persona (theorist, engineer, skeptic, pm)
│   ├── theorist.json
│   ├── engineer.json
│   ├── skeptic.json
│   └── industry_pm.json
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
      "venue_fit_score": 0.0,      // 0–1: aligned with CFP / review criteria
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
run_id, config_name, seed, git_commit, gpu_hours, primary_metric, [secondary_metrics...], event_flags, notes
```

`event_flags` is a comma-separated subset of `oom`, `nan`, `restart`,
`timeout`, `clean` (or empty). Populated by the training-monitor sentinel
in `auto-research-execution/references/training-monitor.md`. Stage 4 +
the dashboard surface these as red/orange badges; do not strip them when
aggregating into `results_summary.json`.

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
├── figure_prompts/
│   └── pipeline_overview.md
├── figure_plan.md
├── tables/
│   └── main_results.tex   # written by render_table.py from results_summary.json
├── claims_ledger.jsonl    # per-claim provenance (see schema below)
├── lint_report.md         # output of lint_writeup.py — Phase 4 hard gate
├── revision_plan.md       # populated when auto-reviewer requests changes
└── review.md              # auto-reviewer output
```

### `figure_plan.md` required sections

- **Figure inventory**: each planned figure, target filename, section, and current status.
- **External-generation prompts**: pointer to each `figure_prompts/*.md` file.
- **Placeholder policy**: which figures are still placeholders in `paper.tex`.

### `claims_ledger.jsonl` schema (per-line)

```json
{
  "schema_version": 2,
  "claim_id": "C-1",
  "value": 73.4,
  "unit": "%",
  "metric": "accuracy",
  "config_name": "ours_method",
  "seed": null,
  "paper_tex_locator": "paper.tex:L7:C12",
  "source": "results_summary.json:ours_method.accuracy.mean"
}
```

* `paper_tex_locator` is `<file_relative_path>:L<line>` or
  `<file_relative_path>:L<line>:C<col>` — `trace_numbers.py` and the
  frontend tokenizer share this exact convention; do not invent another.
* `source` is a free-form pointer (`results.csv:row=17`,
  `results_summary.json:<dotted-key>`, `literature_pool:<key>:abstract`,
  ...) — `trace_numbers.py` does not parse it but it is shown in the
  Inspector's right pane.
* `seed` is `null` for cross-seed aggregates, or an integer for per-seed
  numbers; `value` always reflects the displayed number (so a "73.4%"
  table cell is `73.4`, not `0.734`).
* `schema_version` MUST be `2`. Version 1 fixtures from earlier branches
  are rejected by the linter and the dashboard.

### `revision_plan.md` revision counter

Every `revision_plan.md` produced by Phase 5 starts with the comment::

    <!-- revision: N -->

Where `N` is a 1-indexed integer (`1` on first revision, `2` on second).
The Inspector's revision-diff view orders successive revisions by this
counter rather than by file mtime.

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

## Stage markers (`stage_<n>_done`)

A marker file is written at the top level of `runs/<run_id>/` when each
stage finishes successfully. The orchestrator and the dashboard both rely
on the same JSON shape; an empty file no longer satisfies the contract.

```json
{
  "stage": 3,
  "started_at": "2026-05-09T11:53:00Z",
  "finished_at": "2026-05-09T13:42:00Z",
  "gpu_hours_consumed_so_far": 12.4
}
```

* `gpu_hours_consumed_so_far` is the **cumulative** sum from `run.yaml`
  start, not a per-stage delta. Compute it by summing the `gpu_hours`
  column of `stage3_execution/results.csv` (no other stage spends GPU
  hours by definition).
* `started_at` / `finished_at` are ISO-8601 UTC. Use `LINT_FREEZE_TIME`
  to pin them in tests.
* The orchestrator's `auto-research/SKILL.md` enumerates which stage may
  write each marker; sub-skills must not write markers of other stages.
