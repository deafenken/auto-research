# Auto Research Skills

`auto-research` is a staged CS/AI research skill suite for Codex-style agents. It takes a project from broad topic selection to a draft paper, with explicit contracts between stages and hard integrity checks against fabricated citations, unsupported claims, and silent baseline downgrades.

## Included Skills

- `auto-research`: orchestrator for the full pipeline
- `auto-research-ideation`: literature mining and gap-driven idea generation
- `auto-research-method`: method formalization and experiment design
- `auto-research-execution`: implementation, monitoring, and reproducible runs
- `auto-research-writing`: paper drafting, self-review, and revision

## Design Principles

- `Evidence first`: claims and tables must trace to run artifacts or verified citations.
- `Stage contracts`: each stage reads and writes files under `runs/<run_id>/`.
- `Output-first writing`: writing starts from results, limitations, and reviewability, not style.
- `Reviewer realism`: the pipeline optimizes for what a top-tier reviewer can attack.
- `Budget honesty`: compute, baselines, and failure criteria are fixed before execution.
- `Human accountability`: generated papers are drafts and require human review before submission.

## Repository Layout

```text
auto-research/
auto-research-ideation/
auto-research-method/
auto-research-execution/
auto-research-writing/
README.md
```

Each skill contains:

- `SKILL.md`: trigger and workflow instructions
- `references/`: load-on-demand guidance
- `assets/`: templates, scripts, or LaTeX scaffolds
- `agents/openai.yaml`: UI metadata

## Quick Start

1. Copy one or more skill folders into your Codex skills directory.
2. Invoke `auto-research` for end-to-end runs, or invoke a stage skill directly for partial continuation.
3. Use `auto-research-writing` only after Stage 3 artifacts exist.

## Notes

- This repo is tuned for CS/AI research workflows, not general academic writing.
- The writing stage supports negative-result framing instead of paper-washing failed hypotheses.
- `auto-research-writing` defaults to a generic NeurIPS-style LaTeX template, with ICLR and ICML variants included.
- The suite is research-assistance infrastructure, not an auto-submit system.
