# Debug Loop

The goal is to fix the smallest credible root cause, not to thrash.

## Loop

1. Capture the full traceback and failing command.
2. Classify the root cause:
   - dependency / environment
   - shape or dtype mismatch
   - config or path error
   - numerical instability
   - data contract violation
   - unknown
3. Write one hypothesis for the failure.
4. Apply one targeted fix.
5. Retry.

Repeat up to 5 times for the same root-cause family.

## Logging

Maintain a ledger in `run_report.md`:

- attempt number
- root cause family
- fix applied
- result

## Escalation boundary

Escalate immediately if:

- the fix would weaken an assertion or remove an evaluation,
- the fix would alter the Stage 2 hypothesis,
- the failure suggests silent data corruption,
- 5 attempts have been exhausted.
