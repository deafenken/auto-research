# Code Style for the Experiment Repo

The code in `runs/<run_id>/stage3_execution/code/` is going to be re-read by Stage 4 (for the algorithm-block details), audited by reviewers (post-publication if open-sourced), and possibly reused by you in 6 months for a follow-up. Treat it as production-grade research code, not throwaway.

## Top-level structure

```
code/
├── .git/
├── .gitignore                  # ignore: data/, checkpoints/*.pt, logs/*.log
├── README.md                   # how to reproduce
├── pyproject.toml or setup.py  # installable as a package
├── requirements.txt            # pinned versions
├── configs/
│   ├── base.yaml               # shared defaults
│   ├── method.yaml             # the proposed method
│   └── baselines/
│       ├── greedy.yaml
│       ├── vgts.yaml
│       └── best_of_n.yaml
├── src/<package_name>/
│   ├── __init__.py
│   ├── data.py                 # dataset loading
│   ├── model.py                # model class(es)
│   ├── method.py               # the proposed method (the paper's contribution)
│   ├── baselines.py            # baseline implementations
│   ├── train.py                # training loop
│   ├── eval.py                 # evaluation
│   ├── monitor.py              # NaN/loss-flat sentinel
│   └── utils.py                # logging, seeding, config loading
├── scripts/
│   ├── launch_runs.py          # drives the (config × seed) matrix
│   └── aggregate_results.py    # builds results_summary.json from results.csv
├── experiment.py               # AI-Scientist-style entrypoint (or train.py)
├── plot.py                     # standardized plotting (Sakana convention)
└── tests/                      # at minimum, smoke tests for each baseline
```

## Configuration discipline

### Hyperparameters live in YAML, not Python.

```yaml
# configs/method.yaml
model:
  name: "Llama-3-8B"
  precision: "bf16"
  lora_rank: 16

training:
  batch_size: 32
  gradient_accumulation: 4
  lr: 1.0e-4
  warmup_steps: 100
  max_steps: 5000

method:
  beam_width: 4
  verifier_threshold: 0.9
  alpha: 1.0

logging:
  wandb_project: "ttc-small-lm-2026"
  log_every_n_steps: 25
  eval_every_n_steps: 500

reproducibility:
  seed: 13
  deterministic_cudnn: true
```

In code:

```python
from omegaconf import OmegaConf
cfg = OmegaConf.load("configs/method.yaml")
# cli overrides
cfg.merge_with_dotlist(sys.argv[1:])
```

Forbidden: hardcoded `lr=1e-4` anywhere in `train.py`.

### Configs compose

Use a base config + overrides:

```bash
python experiment.py --config configs/method.yaml \
    --override training.lr=2e-4 reproducibility.seed=42
```

This is how the (config × seed) sweep is driven.

## Object boundaries

### Model = a class

```python
class VerifierGuidedDecoder(nn.Module):
    def __init__(self, base_lm: PreTrainedModel, verifier: nn.Module, cfg: DictConfig):
        super().__init__()
        self.base_lm = base_lm
        self.verifier = verifier
        self.beam_width = cfg.method.beam_width
        self.alpha = cfg.method.alpha

    def generate(self, prompt: torch.Tensor, max_tokens: int) -> torch.Tensor:
        # The actual method
        ...

    def loss(self, batch: dict) -> torch.Tensor:
        # Training loss
        ...
```

### Method = a function or class with explicit interface

```python
def vgd(prompt: list[int], base_lm, verifier, cfg) -> list[int]:
    ...
```

### Trainer = explicit, not magic

```python
class Trainer:
    def __init__(self, model, optimizer, dataloader, cfg, monitor: Monitor):
        ...

    def train_step(self, batch) -> dict:
        # returns metrics for logging
        ...

    def eval(self) -> dict:
        # returns metrics
        ...

    def train(self):
        for step in range(self.cfg.training.max_steps):
            metrics = self.train_step(next(self.dataloader))
            self.monitor.observe(metrics, step)
            self.log(metrics, step)
            if step % self.cfg.logging.eval_every_n_steps == 0:
                eval_metrics = self.eval()
                self.log(eval_metrics, step)
                self.monitor.observe_eval(eval_metrics, step)
            if step % self.cfg.logging.checkpoint_every_n_steps == 0:
                self.save_checkpoint(step)
```

## Defensive code

### Validate inputs at the API boundary

```python
def vgd(prompt: list[int], base_lm, verifier, cfg) -> list[int]:
    assert len(prompt) > 0, "empty prompt"
    assert all(isinstance(t, int) for t in prompt), "prompt must be list of int token IDs"
    assert cfg.method.beam_width >= 1
    assert cfg.method.alpha >= 0
    ...
```

The `assert`s are cheap and they save you in the debug loop.

### Don't catch broad exceptions silently

```python
# BAD
try:
    out = base_lm(input_ids)
except Exception:
    return torch.zeros(...)  # silent failure → mysterious results

# GOOD
try:
    out = base_lm(input_ids)
except torch.cuda.OutOfMemoryError as e:
    raise OOMRetryable(e) from e  # surfaces to monitor
```

### Type hints everywhere

Modern PyTorch projects use type hints. Reviewers reading your code 6 months from now will thank you. Use `mypy --ignore-missing-imports` as a smoke test.

## Determinism

See `reproducibility.md` for the full protocol. Quick version:

```python
def set_global_seed(seed: int, deterministic_cudnn: bool = True):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    if deterministic_cudnn:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
```

Call this at the start of every run, before anything else (after argparse).

## Logging

Standardize on WandB (`auto-research-execution/references/wandb-conventions.md`). For each run, log:

- `config` (full YAML serialized).
- `git_commit`, `hardware`, `python_version`, library versions.
- Every step: loss, lr, gradient_norm, throughput.
- Every eval: all primary + secondary metrics from `experiment_plan.yaml::metrics`.
- Every checkpoint: step, eval-metric, file-path.

Mirror to a local `runs/<id>/stage3_execution/logs/<run_name>/` directory so the run is auditable without WandB access.

## Tests

Even research code benefits from a few tests:

```python
# tests/test_method_smoke.py
def test_vgd_runs_on_dummy_input():
    base_lm = build_dummy_lm(vocab=128, hidden=64)
    verifier = build_dummy_verifier(hidden=64)
    cfg = OmegaConf.load("configs/method.yaml")
    out = vgd(prompt=[1, 2, 3], base_lm=base_lm, verifier=verifier, cfg=cfg)
    assert len(out) > 0
```

Run before launching the full sweep. Catches "I broke the method during a refactor" in 5 seconds vs. 5 GPU-hours.

## .gitignore

```
__pycache__/
*.pyc
.venv/
.pytest_cache/

# data and checkpoints — too large for git
data/
checkpoints/*.pt
checkpoints/*.bin
*.npy
*.parquet

# local logs — wandb is the source of truth
logs/wandb/
logs/tensorboard/
*.log

# secrets
.env
*.api_key
```

## Anti-patterns

- **Magic numbers in code.** Always: cfg-driven.
- **Global state.** Bad: `model = build_model()` at module level. Good: instantiate inside `main()`.
- **Print debugging left in.** Use logging (`logger.debug`) so it can be silenced.
- **`if __name__ == '__main__':` doing everything.** Factor into `main(cfg)` for testability.
- **Mixing model + training in one class.** Separate model (architecture) from trainer (loop). Eases reuse.
- **Importing from notebooks.** Notebooks are for exploration; production code is in `.py`.
- **Logging to stdout only.** Mirror to a file. Stage 4 may need to read it.

## End-of-Stage-3 lint

Before declaring Stage 3 done, run:

```bash
# In runs/<id>/stage3_execution/code/
ruff check src/ tests/
mypy src/ --ignore-missing-imports
pytest tests/ -q
```

Doesn't have to be perfect, but no errors. Warnings are OK if documented.
