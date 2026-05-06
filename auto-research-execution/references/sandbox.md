# Sandbox

Treat newly written experiment code as untrusted until inspected.

## Forbidden patterns

- `exec(...)`
- `eval(...)`
- `subprocess` calls that touch the network without explicit need
- deleting arbitrary files
- reading secrets from unrelated paths

## Lightweight AST screen

Before first execution, scan Python files for:

- forbidden imports
- dynamic code execution
- suspicious filesystem mutation outside the run directory

## Execution discipline

1. Run from `runs/<run_id>/stage3_execution/code/`.
2. Keep outputs inside `logs/`, `checkpoints/`, or `figures/`.
3. Require explicit justification before enabling network-dependent code.
4. Record the exact command line in `run_report.md`.
