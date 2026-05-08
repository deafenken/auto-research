# Auto Research Skills

`auto-research` is a staged CS/AI research skill suite for Claude and Codex agents. It starts by asking which venue you want to target, fetches the official LaTeX template and submission requirements from official sources, analyzes the CFP to shape the innovation angle, then takes the project from broad topic selection to a draft paper with explicit contracts between stages and hard integrity checks against fabricated citations, unsupported claims, and silent baseline downgrades.

## Included Skills

- `auto-research`: orchestrator for the full pipeline
- `auto-research-ideation`: literature mining and gap-driven idea generation
- `auto-research-method`: method formalization and experiment design
- `auto-research-execution`: implementation, monitoring, and reproducible runs
- `auto-research-writing`: paper drafting, self-review, and revision

## Design Principles

- `Evidence first`: claims and tables must trace to run artifacts or verified citations.
- `Stage contracts`: each stage reads and writes files under `runs/<run_id>/`.
- `Venue-first setup`: the workflow asks for the target conference or journal before ideation, then grounds innovation choices in the CFP and official template.
- `Output-first writing`: writing starts from results, limitations, and reviewability, not style.
- `Reviewer realism`: the pipeline optimizes for what a top-tier reviewer can attack.
- `Budget honesty`: compute, baselines, and failure criteria are fixed before execution.
- `Human accountability`: generated papers are drafts and require human review before submission.
- `No evaluation-paper drift`: unless explicitly requested, the pipeline avoids collapsing into a pure benchmark or model-comparison paper.
- `External figure handoff`: when conceptual figures are better made outside the agent, the writing stage leaves LaTeX placeholders and saves prompts for external image models such as Gemini or GPT-image.
- `Venue-aware writing budget`: the writing stage respects venue page limits and defaults to a citation-rich Related Work section, typically around 1 to 1.5 pages when space allows.

## Repository Layout

```text
auto-research/
auto-research-ideation/
auto-research-method/
auto-research-execution/
auto-research-writing/
README.md
README.en.md
README.zh-CN.md
```

Each skill contains:

- `SKILL.md`: trigger and workflow instructions
- `references/`: load-on-demand guidance
- `assets/`: templates, scripts, or LaTeX scaffolds
- `agents/openai.yaml`: UI metadata for Codex-compatible skill UIs; Claude-side tooling can ignore it

## Quick Start

1. Copy one or more skill folders into your Claude or Codex skills directory (see [Installation](#installation) below for paths).
2. Invoke `auto-research` for end-to-end runs, or invoke a stage skill directly for partial continuation.
3. Use `auto-research-writing` only after Stage 3 artifacts exist.

## Installation

### Claude Code

Claude Code discovers skills under `~/.claude/skills/` (user scope) or `<project>/.claude/skills/` (project scope). Copy or symlink the five folders there:

```bash
# User scope — available in every project
mkdir -p ~/.claude/skills
cp -r auto-research auto-research-ideation auto-research-method \
      auto-research-execution auto-research-writing ~/.claude/skills/

# Or project scope — available only inside the current repo
mkdir -p .claude/skills
cp -r auto-research auto-research-ideation auto-research-method \
      auto-research-execution auto-research-writing .claude/skills/
```

After copying, restart Claude Code (or run `/skills` to verify they show up). The trigger phrases inside each `SKILL.md` (e.g. "write me a paper on X", "auto research X") will surface the skill automatically; you can also invoke a specific stage by name.

### Codex / OpenAI-compatible agents

Place the same folders in whatever skills directory your Codex-style runtime uses; the `agents/openai.yaml` files supply the UI metadata.

## Compatibility

- `SKILL.md`, `references/`, and `assets/` are the portable core and can be used by both Claude-style and Codex-style skill systems.
- `SKILL.md` frontmatter (`name` + `description`) is exactly the format Claude Code expects — no conversion needed, and all descriptions stay within Claude Code's 1024-character limit.
- `agents/openai.yaml` is Codex/OpenAI-compatible UI metadata only; Claude Code ignores it without error.
- The workflow itself is model-agnostic: the main assumptions are staged file hand-offs, tool access, and human checkpoints.

## Notes

- This repo is tuned for CS/AI research workflows, not general academic writing.
- The writing stage supports negative-result framing instead of paper-washing failed hypotheses.
- `auto-research-writing` defaults to a generic NeurIPS-style LaTeX template, with ICLR and ICML variants included.
- The suite is research-assistance infrastructure, not an auto-submit system.
- By default, the suite aims for real research ideas rather than "evaluate many models on many benchmarks" papers.
- For pipeline or idea diagrams, the writing stage can leave figure placeholders plus saved prompts for external generation tools such as Gemini or GPT-image.
