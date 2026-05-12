# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A library of five **portable skill packages** for Claude Code and Codex-style agents. It is *not* a runnable application — there is no build, no test suite, no `requirements.txt` at the repo root. The deliverables are markdown + YAML + a few small Python helpers + LaTeX templates that get copied into `~/.claude/skills/` (or `<project>/.claude/skills/`) and executed by an agent at runtime.

Implication for editing: the "code" here is the prompts and workflow contracts. Changes are validated by reading them, not by running them. Don't try to `pip install` or execute anything from inside the repo to "verify" a change.

## The five skills and how they compose

```
auto-research            ← orchestrator (Stage 0..4 driver, integrity gate)
  ├─ auto-research-ideation     ← Stage 1: literature mining + STORM-style debate
  ├─ auto-research-method       ← Stage 2: formal method + experiment_plan.yaml
  ├─ auto-research-execution    ← Stage 3: scaffolds repo, runs, debug-loop
  └─ auto-research-writing      ← Stage 4: LaTeX draft + auto-review + revise
```

Each skill folder has the same shape:

- `SKILL.md` — frontmatter (`name`, `description`) + workflow. The description is read by Claude Code/Codex to decide when to trigger; keep it under 1024 chars.
- `references/*.md` — load-on-demand reference docs cited from `SKILL.md`'s "When to load which reference" table. Skills should NOT be told to load all references upfront.
- `assets/` — concrete artifacts: scripts (`launch_runs.py`, `citation_verify.py`, `search_literature.py`), code-skeleton templates (`hf-trainer-style/`, `nanoGPT-style/`, etc.), or LaTeX scaffolds (`neurips`, `iclr`, `icml`).
- `agents/openai.yaml` — Codex-side UI metadata only. Claude Code ignores it. When changing skill metadata, keep `SKILL.md` frontmatter and `openai.yaml` in sync.

The orchestrator never does the research itself; it sequences the four sub-skills and enforces the contract between them.

## State contract — do not invent paths

All inter-stage state lives under `runs/<run_id>/` (where `<run_id>` = `YYYY-MM-DD-<kebab-slug>`). The full file schema is defined in `auto-research/references/state-contract.md` — treat that file as authoritative. When editing any skill that reads or writes stage artifacts, cross-check it against `state-contract.md` so the contract stays consistent across all five skills.

Key files the next stage always reads first:

- `runs/<run_id>/run.yaml` — domain, venue, budget, deadline, mode
- `runs/<run_id>/stage{N}_*/hand_off.md` — one paragraph from stage N for stage N+1
- `runs/<run_id>/stage0_setup/{venue_profile.yaml,cfp.md,latex_template/}` — venue grounding for every later stage

`runs/` is gitignored — never commit experimental output back into this repo.

## The integrity rules override everything

`auto-research/references/integrity-rules.md` defines the eight non-negotiable rules (no fabricated data, no fabricated citations, no silent baseline downgrade, reproducibility floor, compute budget gate, human-before-submit, official venue assets only, no evaluation-paper drift). When editing any skill:

- Do not loosen these rules to make a workflow easier.
- A skill that adds a new code path must say how that path satisfies (or escalates under) these rules.
- The orchestrator's "stop and ask the human" checkpoints listed in `auto-research/SKILL.md` are part of the contract — preserve them when touching the orchestration loop.

## Conventions when editing skills

- Keep `SKILL.md` frontmatter `description` field within Claude Code's 1024-character limit and written so the trigger logic ("when to invoke" / "do NOT trigger when") is unambiguous.
- Examples in skills use absolute dates (e.g. `2026-05-06-...`); do not rewrite to relative phrases like "today".
- The repo intentionally has both English (`README.md` — GitHub's default render) and Chinese (`README.zh-CN.md`) READMEs; if you change one substantively, mirror the change in the other.
- Bundled LaTeX templates (`auto-research-writing/assets/latex/{neurips,iclr,icml}/template.tex`) are *fallbacks*. The pipeline prefers the template fetched into `runs/<run_id>/stage0_setup/latex_template/` at Stage 0. Do not change the writing skill in a way that bypasses the fetched template.

## Working in this environment

This machine is shared and resource-constrained — it is for *editing skills and committing*, not for executing them. Do not attempt to invoke a skill end-to-end from this checkout to test it: actual runs (literature search APIs, training, LaTeX compile) belong on the user's local/compute machine. When the user wants to validate a change, list the commands they should run locally rather than running them here.
