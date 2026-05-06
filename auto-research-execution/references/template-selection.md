# Template Selection

Pick the closest template, then adapt. Building from scratch is allowed but should be a last resort because templates encode reproducibility/logging/checkpointing best-practices that are tedious to re-derive.

## Decision tree

```
Does the experiment train a model from scratch (or major architecture change)?
├── Yes — small LM / encoder        → nanoGPT-style
├── Yes — vision classifier         → vision-clf-style
├── Yes — RL agent                  → rl-style
├── Yes — none of the above         → from-scratch (with reason)
└── No — uses a pretrained model
     ├── Fine-tuning (SFT, LoRA, RLHF)  → hf-trainer-style
     ├── Inference-only evaluation       → eval-only-style
     └── Custom inference pipeline (RAG / agent) → eval-only-style + custom additions
```

## Template comparison

| Template | Backbone | Data assumptions | Logging | When NOT to use |
|---|---|---|---|---|
| `nanoGPT-style` | Karpathy nanoGPT-class transformer | OWT / TinyStories / custom text | wandb + minimal stdout | Multi-modal / non-LM tasks |
| `hf-trainer-style` | Anything in HF Hub (Llama, Mistral, T5, ViT, ...) | HF Datasets format | wandb (HF Trainer integration) | When HF Trainer abstractions hide what you need |
| `vision-clf-style` | timm models or torchvision | ImageFolder / WebDataset | wandb + tensorboard | Non-classification (use detection-specific framework) |
| `rl-style` | Custom torch policy net | Gym / pettingzoo env | wandb + custom env stats | Symbolic / non-gradient RL |
| `eval-only-style` | Any (called via API or local) | Benchmark format | wandb (eval-only mode) | Anything that needs training |

## Trade-offs

### Use `hf-trainer-style` when:

- You're fine-tuning an existing pretrained model.
- Standard losses (CE, DPO, ORPO, KTO).
- HF ecosystem (Datasets, Trainer, Accelerate, PEFT, TRL) gives you 80% of what you need.

**Pros:** Battle-tested. Free distributed training, mixed precision, gradient accumulation, lr schedulers. Direct compatibility with most pretrained models.

**Cons:** Trainer hides things. If your method needs custom backward / custom data sampling / custom optimizer step, you may need to subclass or break out of Trainer.

### Use `nanoGPT-style` when:

- You're studying transformer training itself (architecture, optimization, scaling).
- You want full control of every line.
- You're working at small scale where Trainer overhead matters.

**Pros:** Every line is yours. Easy to modify any part of the loop.

**Cons:** You re-implement amp, distributed, checkpointing. Typos in the loop = silent bugs. Use this only when needed.

### Use `eval-only-style` when:

- The contribution is at inference time (decoding strategy, prompting, RAG, agent).
- No training is required.
- You're measuring an off-the-shelf model under varying conditions.

**Pros:** Skip all training infrastructure. Fast iteration.

**Cons:** Can't easily transition to "we tried training too" unless you switch templates mid-stream.

## Adapting a template — what to change vs. what to leave

### Always keep (do not refactor)

- Logging hooks (`log_step`, `log_eval`, `log_checkpoint`).
- Config loading (`load_config`).
- Seeding (`set_global_seed`).
- Distributed-init / Accelerate setup.
- Checkpoint save/restore.
- Run-metadata collection (git_commit, hardware, library versions).

These are the "infrastructure tax" that makes runs reproducible and comparable. Touch only to *add* fields, never to remove.

### Always change (template-specific)

- The model class — replace with your method's model.
- The training step / loss — replace with your method's loss.
- The eval routine — replace with the metrics from `experiment_plan.yaml::metrics`.
- The configs — populate per `experiment_plan.yaml`.
- The data loader — point to the dataset(s) in `experiment_plan.yaml::datasets`.

### Optional changes

- The optimizer (default Adam / AdamW is fine for most; only change if your method needs it).
- The scheduler (default cosine + warmup is fine).
- The precision (default bf16 if available, else fp16).

## "from-scratch" mode

Reserved for genuinely novel research where no template fits — e.g., a new training paradigm that doesn't fit standard step / eval / checkpoint cycles.

If you go from-scratch, you must:

- Build in: seeded RNG, config-loading, logging, checkpointing, error handling, monitor sentinel.
- Replicate the file structure of the closest template (so Stage 4 knows where to look for things).
- Document why no template fit, in `code/README.md`.

## Adapting one template to a new sub-domain

If the template fits 80% but not 100%:

- Don't fork the template into the user's repo (then your bug fixes upstream are lost).
- Instead, copy and adapt the specific files you need. Keep imports from the template package where possible.
- Document the divergence in `code/README.md`.

## Naming the run

Once a template is picked and adapted:

- The repo at `runs/<run_id>/stage3_execution/code/` is the run's repo.
- Initial commit message: "scaffold from <template_name>".
- Each subsequent change is its own commit ("add method M", "wire baseline X", "fix lr scheduler bug" etc.).

`git_commit` per row in `results.csv` will index into this history.
