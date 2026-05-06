# Experiment Design

The experimental scaffold for a top-tier paper. The goal is not "produce numbers" — it is "produce numbers that *uniquely* support the central claim and could not be explained by a simpler hypothesis."

## The 7 components

Every plan in `experiment_plan.yaml` must have all 7. Skipping any one reads as sloppiness to a reviewer.

### 1. Hypothesis

Write *one* falsifiable sentence:

> **Hypothesis.** Method M improves metric P on dataset D by at least δ over baseline B, where δ is large enough to exceed run-to-run variance under N seeds.

Examples:

- Good: "Verifier-guided decoding improves MATH accuracy by ≥ 3 percentage points over greedy decoding under matched FLOPs, on Llama-3-8B, with 5 seeds."
- Bad: "Our method improves accuracy." (No metric, no dataset, no baseline, no magnitude, no compute matching.)
- Bad: "Our method works in the chosen setting." (Tautological.)

The hypothesis is locked at end of Stage 2 (integrity rule 6).

### 2. Datasets

```yaml
datasets:
  - name: "MMLU"
    split: "test"
    size: 14042
    license: "MIT"
    download_url: "https://..."
    role: "primary"
  - name: "MMLU-Pro"
    split: "test"
    size: 12000
    license: "MIT"
    role: "harder OOD check"
```

Required: ≥ 2 datasets total, including:

- A **primary** evaluation set (where the headline metric lives).
- At least one **OOD / robustness / harder** set. Without this, the gain may be a benchmark-overfitting artifact.

For domains without standard benchmarks, you may *propose* one — but it then becomes a contribution and the paper must justify it (see `references/baseline-selection.md::custom_dataset_rules`).

Forbidden: tested only on a subset, or a custom-curated subset, of a standard benchmark, without disclosing.

### 3. Baselines

```yaml
baselines:
  - name: "Greedy decoding"
    paper: "Standard"
    must_reproduce: false
  - name: "Verifier-Guided Tree Search (VGTS)"
    paper: "arxiv:2403.xxxxx"
    must_reproduce: true
    expected_metric: {accuracy: 0.74}
  - name: "Best-of-N (N=64)"
    paper: "arxiv:2204.yyyyy"
    must_reproduce: true
    expected_metric: {accuracy: 0.71}
```

Required: ≥ 2 baselines, including:

- The **closest method-family SOTA** from the past 12-24 months.
- A **strong-but-cheap** baseline (e.g. greedy / random) as a sanity floor.

Each baseline must be runnable. `must_reproduce=true` means Stage 3 will halt if the reproduction is more than ±20% off the published metric.

See `references/baseline-selection.md` for what counts as a fair comparison and how to compute-match.

### 4. Metrics

```yaml
metrics:
  primary: "accuracy"
  secondary:
    - "calibration_ece"          # Expected Calibration Error
    - "wall_clock_inference_s"
    - "FLOPs_per_response"
  reporting:
    - "mean ± std across N seeds"
    - "best-of-N for N in [1, 4, 16, 64] (compute-matched)"
```

The **primary** metric must directly test the hypothesis. Don't sneak in a secondary metric as the headline.

Required secondary metrics depend on the claim:

- If the claim is about quality: include calibration / robustness check.
- If the claim is about efficiency: include FLOPs and wall-clock.
- If the claim is about reasoning: include a difficulty-stratified breakdown.

Forbidden: reporting only the metric where you win.

### 5. Ablations

See `references/ablation-design.md`. Brief here:

```yaml
ablations:
  - name: "remove component A"
    description: "drop the verifier head; use only the LM logits"
    expected_drop: ">= 2 pp"
    purpose: "show the verifier is the source of the gain"
  - name: "swap component B for naive variant"
    description: "replace adaptive temperature with fixed 0.7"
    expected_drop: ">= 1 pp"
    purpose: "show adaptivity is non-trivial"
```

Required: ≥ 2 ablations. Each one isolates a *single* design choice. Each has a pre-registered expected drop.

If an ablation comes back with a smaller drop than expected → the component might not matter. The paper must address this honestly; doing so often strengthens the writeup ("we find that B contributes less than expected; the dominant signal is A").

### 6. Seeds

```yaml
seeds: [13, 42, 123, 1234, 7777]
seeds_for_main: 5
seeds_for_ablation: 3
```

Required: ≥ 3 seeds for credible mean ± std. 5 is standard for top venues. The seeds list is locked here so Stage 3 can't quietly drop one.

For language model evaluation where the eval is deterministic given the model, "seed" means the seed for any randomness in *training* (or in Best-of-N sampling). Even if eval is deterministic, you need multiple training seeds to claim the gain isn't a fluke.

### 7. Compute estimate

```yaml
compute_estimate:
  per_run_hours: 1.5
  num_runs: 23           # 5 seeds × main + 6 ablations × 3 seeds
  buffer_multiplier: 1.3
  total_gpu_hours: 45    # = 1.5 * 23 * 1.3, rounded
```

Compare against `run.yaml::budget.gpu_hours`. If `total_gpu_hours > budget.gpu_hours`, **scope down here** — drop ablations, reduce seeds, or shrink model — until it fits. Do NOT punt overage to Stage 3.

Common scope-down moves:

- 7B model → 1B model (state caveat in paper).
- 5 seeds → 3 seeds (mandatory variance reporting still).
- Drop the lowest-priority ablation.
- Smaller eval subset (only if a sub-sample is principled, e.g. random 1k of MMLU's 14k).

## Pre-registration discipline

The plan written at end of Stage 2 is *the* plan. Stage 3 may not silently:

- Add seeds (running the same config more times until you get a good number).
- Add ablations after seeing main results (HARK-ing).
- Switch primary metric.
- Drop a baseline because it became inconvenient.

Any deviation goes in `run_report.md` under "Deviations from plan" with reason.

## Success / failure criteria

```yaml
success_criteria:
  - "primary metric ≥ baseline + 2pp on at least 4/5 seeds"
  - "no required ablation removes < 1pp of the gain (i.e. each component matters)"

failure_criteria:
  - "primary metric ≤ baseline mean on majority of seeds"
  - "any required baseline failed to reproduce within 20% of published metric"
  - "compute consumed > 100% of budget before main runs complete"
```

`failure_criteria` are **kill switches**. If hit, Stage 3 escalates and the project may pivot to a "negative result" framing (see `auto-research-writing/references/negative-result-paper.md`) rather than paper-wash.

## What "compute-matched" means

When comparing methods that use different inference budgets (e.g. greedy vs. best-of-64), compute-matching is essential to honest comparison:

- Match **total inference FLOPs** per evaluation example.
- Match **wall-clock per evaluation example** if the claim is about latency.
- Match **memory** if the claim is about deployment.

Most reviewer complaints in this area are: "the gain comes from spending 64x compute, not from the method." Pre-empt by showing your method beats the baseline at *equal* compute.

For a clear pattern, plot the metric on the y-axis vs. inference compute on the x-axis, showing both methods scaling. Win convincingly only if your curve is above the baseline's at the *same* x.

## Domain-specific add-ons

| Domain | Required extra |
|---|---|
| LLM | Test set decontamination check (against pretraining data). |
| Vision | Multiple architectures for the gain (not just one backbone). |
| RL | Both online and offline evaluation; both seeded environment and IC variation. |
| RAG / agents | Both controlled benchmark and a held-out real-world set. |
| Diffusion | Multiple sampler steps (not just the one favorable to your method). |
| Robustness | Multiple shift types (not just one). |

## Output: what `experiment_plan.yaml` looks like end-to-end

See `auto-research/references/state-contract.md` for the exact schema. The plan is what Stage 3 reads.

## Cross-references

- For baseline-selection details: `baseline-selection.md`
- For ablation design: `ablation-design.md`
- For the stress test that catches reviewer-anticipated weaknesses: `method-stress-test.md`
