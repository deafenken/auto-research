# CUDA OOM Recovery

OOM is one of the few auto-recoverable failures.

## Recovery order

1. Reduce batch size by `2x`.
2. Increase gradient accumulation to preserve effective batch size when possible.
3. Enable or verify mixed precision.
4. Reduce sequence length or image resolution only if allowed by the experiment plan.

## Limits

- Maximum 3 automatic OOM retries per config.
- Every retry must be logged in `run_report.md`.
- If reducing memory usage would materially change the experiment, escalate instead of continuing.
