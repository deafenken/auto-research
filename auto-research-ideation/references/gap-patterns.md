# Gap Patterns — when personas are stuck

The persona-debate sometimes produces only generic complaints ("the paper could have more ablations"). This file lists common, *specific* research-gap patterns in CS/AI that you can use to prime the personas.

Use these as "have you considered…" prompts to inject when Round 1 outputs are too vague. Do not present them as ideas — they are seed *questions* the personas should investigate against the literature pool.

## Pattern bank

### LLM / NLP

| Pattern | Question to inject |
|---|---|
| Chain-of-thought as expensive sampling | Does the proposed method scale CoT budget by problem hardness, or use a fixed-token prefix? |
| RLHF reward hacking | Does the reward model's preferred output correlate with quality, or with stylistic markers (length, formatting, hedging)? |
| Long-context decay | Does the method test on > 32k tokens with adversarial position of the answer (not just the start)? |
| Tokenizer bias | Are claimed multilingual gains real or artifacts of tokenization differences? |
| Prompting brittleness | Does small prompt perturbation break the method's headline metric? |
| Distribution shift in eval | Are eval sets drawn from the same distribution as the SFT/RLHF data? |
| Calibration | Does confidence calibrate with accuracy? Do the proposed CoT methods make this *worse*? |
| Test-time compute | Where is the actual compute budget being spent (sampling vs verifier vs retrieval)? Is it fairly compared? |
| Tool use | Is success measured by "the tool was called" or by "the right tool was called with the right args"? |
| Code generation | Are evaluations on contaminated benchmarks (e.g. HumanEval pieces in pretraining data)? |

### Vision

| Pattern | Question |
|---|---|
| Backbone-induced leakage | Do gains come from the proposed method or from upgrading the backbone (e.g. ViT-B → ViT-L)? |
| Data scale confound | Does the method's gain shrink as pretraining data grows (suggesting method substitutes for data)? |
| Robustness ≠ generalization | Does the method tested on ImageNet-C also handle natural shift (ImageNet-Sketch, etc.)? |
| Diffusion sampling | Are FID gains from better sampling, or from cherry-picked prompts / nucleus parameters? |
| Multi-modal alignment | Are vision-language matches semantic or structural (e.g. caption length matching)? |
| Segmentation IoU games | Are mIoU gains uniform across classes, or concentrated on already-easy classes? |
| Detection in the long tail | Does mAP improve on rare classes or only on dominant ones? |
| Self-supervised learning eval | Linear probe vs. fine-tune vs. nearest-neighbor — methods often optimize for one. |

### RL

| Pattern | Question |
|---|---|
| Sample efficiency vs wall-clock | Does the method save samples but increase per-sample compute, washing out the gain? |
| Reward shaping | Are gains from the method or from a non-standard reward signal? |
| Sim2real | Does the method work outside the specific simulator's quirks? |
| Exploration vs exploitation | Is the "exploration bonus" really an information-seeking term or just stochasticity? |
| Off-policy bias | Are claimed off-policy methods actually using on-policy data via importance sampling tricks? |
| Multi-task negative transfer | Does the multi-task setup hurt some tasks while helping others, with average being misleading? |

### General methodology

| Pattern | Question |
|---|---|
| Hyperparameter sweep asymmetry | Was the proposed method swept harder than baselines? Same compute budget? |
| Random seed cherry-picking | If only 3 seeds run, what is run-to-run std? Is the gain within noise? |
| Validation-set leakage | Is the validation set used for hyperparameter tuning the same as the test set? |
| Compute-matched comparison | Are baselines given the same FLOPs as the proposed method? |
| Pretraining-stage leakage | Did the pretraining data overlap with the eval distribution? |
| Inference-time confound | Does the method use more inference compute than baselines (more samples, longer sequences)? |
| Annotator artifacts | For human eval, were annotators primed in a way that biases toward the method? |

## How to use

When persona output is stuck:

1. Identify which 2-3 patterns from this bank match the literature pool's topic.
2. Inject as additional context to that persona: "Re-read the literature pool with this specific question in mind: <pattern>."
3. Run Round 1 again *for that persona only*. Append, don't replace.

## How to add new patterns

When a debate surfaces a gap that isn't in this bank but feels reusable, add it. Format:

```
| Pattern name | One-question prompt |
```

Keep the question specific (it should map to a check the persona can perform on a single paper's abstract or method section).

## Anti-pattern: pattern-matching to fit

Do not use this bank to *generate* candidates directly. The candidates must come from the cluster intersection in the persona debate. Patterns are seeds, not conclusions.
