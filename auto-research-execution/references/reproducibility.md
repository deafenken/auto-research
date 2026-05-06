# Reproducibility

The reproducibility floor (integrity rule 4) is non-negotiable: every row in `results.csv` must include `git_commit`, `seed`, `config_name`, `gpu_hours`, and hardware string. This file is how you make those guarantees true.

## The 5 fields and how to populate them

### `git_commit`

```python
import subprocess

def current_git_commit(repo_dir: str = ".") -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo_dir, text=True
    ).strip()
```

Capture this at run *start* (not end, in case the user commits mid-run). If the working tree is dirty:

```python
def git_status(repo_dir: str = ".") -> str:
    return subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=repo_dir, text=True
    ).strip()

dirty = bool(git_status())
commit = current_git_commit()
if dirty:
    commit = f"{commit}-DIRTY"  # signal in results.csv
    # also save the diff
    diff = subprocess.check_output(["git", "diff"], text=True)
    save_to(f"runs/.../logs/{run_name}/dirty_diff.patch", diff)
```

A `*-DIRTY` row in `results.csv` is invalid for publication. Stage 4's lint will reject it.

### `seed`

The seed for the run, exactly as listed in `experiment_plan.yaml::seeds`. Apply globally:

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

    # For DataLoader determinism:
    g = torch.Generator()
    g.manual_seed(seed)
    return g
```

Pass the generator into `DataLoader(generator=g, ...)` and set `worker_init_fn` to seed each worker.

### `config_name`

The basename of the YAML file used. Example:

```python
cfg_path = sys.argv[1]
config_name = pathlib.Path(cfg_path).stem  # "method" from "configs/method.yaml"
```

For overrides, append: `method__lr-2e-4__seed-42`.

### `gpu_hours`

Wall-clock × number of GPUs. Track from process start to process end.

```python
import time

start = time.monotonic()
n_gpus = torch.cuda.device_count()  # or len(accelerator.process_indices)
... # train + eval
elapsed_hours = (time.monotonic() - start) / 3600
gpu_hours = elapsed_hours * n_gpus
```

Push gpu_hours to a shared budget tracker (orchestrator reads this for Rule 5):

```python
budget_path = "runs/<run_id>/.budget.json"
with open(budget_path) as f:
    budget = json.load(f)
budget["consumed_gpu_hours"] = budget.get("consumed_gpu_hours", 0) + gpu_hours
with open(budget_path, "w") as f:
    json.dump(budget, f)
```

### Hardware string

```python
def hardware_string() -> str:
    n = torch.cuda.device_count()
    if n == 0:
        return "cpu-only"
    name = torch.cuda.get_device_name(0)  # assume homogeneous
    mem_gb = torch.cuda.get_device_properties(0).total_memory // (1024**3)
    return f"{n}x{name}-{mem_gb}GB"
```

Compare against `run.yaml::budget.hardware`. If they don't match, log a warning — gpu_hours from a different GPU class may not be comparable.

## Library versions

Pin in `requirements.txt`:

```
torch==2.5.1
transformers==4.48.0
datasets==3.2.0
accelerate==1.2.1
peft==0.14.0
trl==0.13.0
wandb==0.18.7
```

Lock the exact versions. At run start, log:

```python
import importlib.metadata as md
versions = {
    pkg: md.version(pkg)
    for pkg in ["torch", "transformers", "datasets", "accelerate", "wandb"]
    if md.distribution(pkg)
}
wandb.config.update({"library_versions": versions})
```

## The `RUN_INFO.json` file

At run start, write a per-run metadata file:

```python
run_info = {
    "run_id": run_id,
    "config_name": config_name,
    "config_full": OmegaConf.to_yaml(cfg),
    "seed": cfg.reproducibility.seed,
    "git_commit": current_git_commit(),
    "git_dirty": dirty,
    "hardware": hardware_string(),
    "library_versions": versions,
    "started_at": datetime.utcnow().isoformat(),
    "started_at_utc_unix": time.time(),
}
with open(f"logs/{run_name}/RUN_INFO.json", "w") as f:
    json.dump(run_info, f, indent=2)
```

This is the one file that, with the code repo at `git_commit`, lets someone re-run your experiment.

## Determinism limits

Even with all the above, exact bitwise reproducibility may not be possible because:

- **CUDA kernels** have nondeterministic implementations of some ops (e.g. atomic adds in scatter). `torch.use_deterministic_algorithms(True)` enforces deterministic kernels but some ops will then raise an error.
- **Mixed precision** can vary slightly between hardware (different tensor-core implementations).
- **Distributed training** introduces nondeterminism in gradient reduction order.

What is realistic:

- **Same seed + same hardware + same code → results within 1% of each other**, often exactly equal.
- **Same seed + different hardware → results within 2-3%**, sometimes more for sensitive metrics.

Document this in `code/README.md`'s "Reproducibility" section. State which level you achieve.

## When determinism makes you slow

`deterministic_cudnn=True` and `cudnn.benchmark=False` slow down training by ~5-15% typically. For final runs that go in the paper, accept the cost. For early iteration, use `deterministic_cudnn=False` and document this.

## Reproducibility checklist (end of Stage 3)

Before declaring Stage 3 done:

- [ ] Every row in `results.csv` has all 5 required fields.
- [ ] No row has `git_commit` ending in `-DIRTY`.
- [ ] `RUN_INFO.json` exists for every run.
- [ ] `requirements.txt` is pinned to exact versions.
- [ ] `configs/` directory has all configs used.
- [ ] `code/README.md` has a "How to reproduce" section.
- [ ] If using random data augmentation: data shuffling is also seeded.
- [ ] Mixed-precision setting is documented (bf16 vs fp16 vs fp32) and consistent across runs of the same config.

## Forbidden patterns

- **Manual seed setting in random spots** ("set seed at start of eval to make eval reproducible"). Set seed once per process.
- **Reading `time.time()` for randomness anywhere.** All randomness through the seeded generators.
- **Hardcoded data shuffling order.** Always go through `DataLoader(generator=g)`.
- **`cudnn.benchmark=True` during measured runs.** OK for early iteration only.
- **Different optimizer seeds across baselines and method.** Same seed list, applied identically.

## When you can't reproduce a number

If a result you reported in `results.csv` cannot be re-run to within 2% on the same hardware + same code + same seed: surface immediately. This is a serious bug in either the seeding, the data pipeline, or the eval, and Stage 4 will rely on this number.

Trace the nondeterminism by progressively turning ON determinism flags until the number stabilizes. The first flag that fixes it tells you where the nondeterminism was.
