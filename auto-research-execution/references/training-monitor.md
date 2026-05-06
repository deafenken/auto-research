# Training Monitor (Sentinel Watchdog)

A lightweight in-process watchdog that catches the most common training pathologies *as they happen*, instead of letting a 4-hour run silently produce garbage. Adapted from AutoResearchClaw's `Sentinel Watchdog`.

## The 4 pathologies it catches

| Pathology | Detection | Action |
|---|---|---|
| NaN / Inf loss | `not torch.isfinite(loss)` | halt, dump state, escalate to debug loop |
| Loss collapse | loss plateaus at 0 / inf for K consecutive steps | halt, dump state, escalate |
| Loss not decreasing | EMA of loss after warmup is not monotonically decreasing | warn, mark, continue |
| OOM | `torch.cuda.OutOfMemoryError` | halve batch size, restart |

## Implementation

```python
# src/<package_name>/monitor.py
from dataclasses import dataclass, field
from collections import deque
import math
import torch


@dataclass
class MonitorConfig:
    nan_action: str = "halt"            # "halt" | "skip"
    loss_window: int = 100              # for plateau / EMA detection
    plateau_eps: float = 1e-6           # std under which we call it a plateau
    plateau_after_step: int = 200       # only check plateau after warmup
    warn_no_decrease_after: int = 1000  # warn if EMA hasn't dropped after N steps


class Monitor:
    def __init__(self, cfg: MonitorConfig, run_dir: str):
        self.cfg = cfg
        self.run_dir = run_dir
        self.losses = deque(maxlen=cfg.loss_window)
        self.ema_loss = None
        self.ema_alpha = 0.05
        self.last_decrease_step = 0
        self.flagged: list[dict] = []

    def observe(self, metrics: dict, step: int):
        loss = metrics.get("loss")
        if loss is None:
            return

        if not math.isfinite(loss):
            self._on_nan(metrics, step)
            return

        self.losses.append(loss)
        self.ema_loss = (
            loss if self.ema_loss is None
            else (1 - self.ema_alpha) * self.ema_loss + self.ema_alpha * loss
        )

        if step > self.cfg.plateau_after_step and len(self.losses) == self.cfg.loss_window:
            arr = list(self.losses)
            std = (sum((x - sum(arr) / len(arr)) ** 2 for x in arr) / len(arr)) ** 0.5
            if std < self.cfg.plateau_eps:
                self._on_plateau(arr, step)

        if loss < (self.ema_loss - 1e-4):
            self.last_decrease_step = step
        if step > self.cfg.warn_no_decrease_after and (step - self.last_decrease_step) > self.cfg.warn_no_decrease_after:
            self._on_no_decrease(step)

    def observe_eval(self, eval_metrics: dict, step: int):
        for k, v in eval_metrics.items():
            if isinstance(v, (int, float)) and not math.isfinite(v):
                self._on_nan({k: v}, step)

    def _on_nan(self, metrics: dict, step: int):
        evt = {"type": "nan", "step": step, "metrics": dict(metrics)}
        self.flagged.append(evt)
        self._dump(evt)
        if self.cfg.nan_action == "halt":
            raise NaNLossError(f"NaN/Inf at step {step}: {metrics}")

    def _on_plateau(self, recent: list[float], step: int):
        evt = {"type": "plateau", "step": step, "recent_mean": sum(recent) / len(recent)}
        self.flagged.append(evt)
        self._dump(evt)
        raise PlateauError(f"Loss plateau at step {step}, recent_mean={evt['recent_mean']:.4f}")

    def _on_no_decrease(self, step: int):
        # Warn only — do not halt
        evt = {"type": "no_decrease", "step": step, "since_step": self.last_decrease_step}
        self.flagged.append(evt)
        self._dump(evt, severity="warn")

    def _dump(self, evt: dict, severity: str = "halt"):
        path = f"{self.run_dir}/monitor_events.jsonl"
        with open(path, "a") as f:
            f.write(json.dumps({"severity": severity, **evt}) + "\n")


class NaNLossError(RuntimeError): pass
class PlateauError(RuntimeError): pass
```

## Wiring it into the trainer

```python
monitor = Monitor(MonitorConfig(), run_dir=f"logs/{run_name}")

for step in range(cfg.training.max_steps):
    metrics = train_step(batch)
    try:
        monitor.observe(metrics, step)
    except (NaNLossError, PlateauError) as e:
        # surface to debug loop
        save_full_state(run_dir=run_dir, step=step, error=str(e))
        raise

    if step % cfg.logging.eval_every_n_steps == 0:
        eval_metrics = eval()
        try:
            monitor.observe_eval(eval_metrics, step)
        except NaNLossError as e:
            save_full_state(run_dir=run_dir, step=step, error=str(e))
            raise
```

## Tuning thresholds

The defaults above are conservative. Tune per template:

| Template | `loss_window` | `plateau_eps` | `plateau_after_step` |
|---|---|---|---|
| nanoGPT-style | 200 | 1e-5 | 500 |
| hf-trainer-style | 100 | 1e-4 | 200 |
| vision-clf-style | 100 | 1e-3 | 500 |
| rl-style | (don't use plateau) | — | — |

For RL the loss/return is inherently noisy and plateau detection mostly false-positives. Use a moving average of episode return instead.

## OOM recovery

```python
# In train.py outer loop
def run_with_oom_recovery(cfg: DictConfig, max_oom_attempts: int = 3) -> dict:
    attempt = 0
    while attempt < max_oom_attempts:
        try:
            return train(cfg)
        except torch.cuda.OutOfMemoryError as e:
            attempt += 1
            new_bs = max(1, cfg.training.batch_size // 2)
            if new_bs == cfg.training.batch_size:
                raise  # already at minimum
            log_warn(f"OOM: halving batch size {cfg.training.batch_size} -> {new_bs}")
            cfg.training.batch_size = new_bs
            cfg.training.gradient_accumulation = (
                cfg.training.gradient_accumulation * 2
            )  # preserve effective batch
            torch.cuda.empty_cache()
            gc.collect()
    raise RuntimeError(f"OOM after {max_oom_attempts} batch-size reductions")
```

The doubled `gradient_accumulation` keeps the effective batch size the same — important so the run is comparable to the planned config.

Document the OOM-induced change in `run_report.md::Deviations from plan` because the reduced micro-batch may slow throughput.

## Hang detection

For methods that may hang (deadlocks in distributed, infinite loops in custom samplers):

```python
# In a separate watchdog thread
import threading, time

class HangWatchdog:
    def __init__(self, expected_step_seconds: float, multiplier: float = 5.0):
        self.last_step_at = time.monotonic()
        self.threshold = expected_step_seconds * multiplier
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def heartbeat(self):
        self.last_step_at = time.monotonic()

    def _loop(self):
        while not self._stop.is_set():
            time.sleep(min(self.threshold, 30))
            if time.monotonic() - self.last_step_at > self.threshold:
                # Dump py-spy or faulthandler stack
                import faulthandler
                with open(f"{self.run_dir}/hang_traceback.txt", "w") as f:
                    faulthandler.dump_traceback(file=f, all_threads=True)
                # signal main thread
                os.kill(os.getpid(), signal.SIGUSR1)

    def start(self): self._thread.start()
    def stop(self): self._stop.set()
```

Trigger after 5× expected step time. SIGUSR1 to the main process to allow graceful shutdown + dump.

## Outputs

The monitor produces:

- `logs/<run_name>/monitor_events.jsonl` — every flagged event.
- `logs/<run_name>/dirty_state_at_step_N.pt` — full state dump on halt (model weights, optimizer state, batch).
- `logs/<run_name>/hang_traceback.txt` — if hang detected.

These are read by the debug loop (`debug-loop.md`) when a run errors out.

## What this prevents

- 8 hours of training silently producing NaN-output → caught in 1 minute.
- Loss plateaus from a buggy data pipeline → caught after `plateau_after_step` steps.
- OOM after a config bump → auto-recovers without manual intervention.
- Distributed deadlocks that hang indefinitely → caught and surfaced.

## What it does not prevent

- Slow but correct learning (could be a real result).
- Numerical issues that don't show up as NaN (e.g. silent fp16 underflow).
- Methodological issues (e.g. data leakage producing too-good results).

For (3), use `auto-research-method/references/method-stress-test.md` Q3 (alternative explanations) — caught at design time, not training time.
