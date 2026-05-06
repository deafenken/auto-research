# Inspiration Map — what was borrowed, what was changed, why

This skill set stands on the shoulders of three open-source projects. This file documents what each one contributed, what we deliberately did differently, and where to look in their source if you want to extend a sub-skill.

## 1. Sakana AI — `AI-Scientist` & `AI-Scientist-v2`

Repo: https://github.com/SakanaAI/AI-Scientist

### What we borrowed

| What | Where it lives in their repo | Where we use it |
|---|---|---|
| Template-trio engineering structure: `experiment.py` + `plot.py` + `prompt.json` + `seed_ideas.json` + `latex/template.tex` | `templates/{nanoGPT,grokking,2d_diffusion}/` | `auto-research-execution/assets/templates/` |
| Auto-reviewer with ensemble + reflection (`num_reflections=5, num_reviews_ensemble=5, temperature=0.1`) | `ai_scientist/perform_review.py` | `auto-research-writing/references/auto-reviewer.md` |
| LaTeX template per conference target (NeurIPS / ICLR / ICML) | `templates/*/latex/template.tex` | `auto-research-writing/assets/latex/` |
| Cost-per-paper as a first-class budget concept | `launch_scientist.py --max-cost` | `auto-research/run.yaml::budget` |
| The fact that LLM-written code can be dangerous → needs container isolation | `experimental/Dockerfile` | `auto-research-execution/references/sandbox.md` |

### What we changed

- Sakana's reviewer notes **"GPT-4o has less positivity bias than other models for review"**. We don't hard-code a model — instead we cross-check: reviewer must surface ≥ 2 weaknesses or the review is invalidated and rerun. Catches positivity drift in any model.
- Sakana's ideation runs novelty-check via Semantic Scholar only. We add OpenReview comment mining (Stage 1 reads negative reviewer comments to find real pain points) and a 4-layer citation verifier (see AutoResearchClaw borrow below).
- Their template assumes one-shot code generation. We split into "scaffold from template" + "iterate with self-healing repair loop" (see AutoResearchClaw borrow).

## 2. Stanford OVAL — `STORM`

Repo: https://github.com/stanford-oval/storm

### What we borrowed

| What | Where it lives in their repo | Where we use it |
|---|---|---|
| Perspective-Guided Question Asking (discover viewpoints by surveying existing articles, then ask each viewpoint different questions) | `knowledge_storm/storm_wiki/modules/persona_generator.py` | `auto-research-ideation/references/multi-perspective-debate.md` |
| Simulated Conversation between writer + topic expert | `knowledge_storm/storm_wiki/modules/knowledge_curation.py` | `auto-research-ideation/references/multi-perspective-debate.md` |
| Outline-then-fill writing pattern (`do_generate_outline` then `do_generate_article`) | `knowledge_storm/storm_wiki/engine.py` | `auto-research-writing/references/outline-then-fill.md` |
| Four-module decomposition (Knowledge Curation / Outline Gen / Article Gen / Article Polishing) | `knowledge_storm/interface.py` | Mirrored in our 4 sub-skills (Stage 1, Stage 4 internal phases) |
| Citation density requirement — every claim must trace to a source | `knowledge_storm/storm_wiki/modules/article_generation.py` | `auto-research/references/integrity-rules.md` Rule 1 & 2 |

### What we changed

- STORM is built for Wikipedia-style survey articles. We adapt the perspective-debate pattern to *research-gap mining* — each persona looks for a different *kind* of weakness (theoretical, empirical, engineering, ethical) rather than asking different *questions about the same topic*.
- STORM uses dspy. We use plain prompts so the skill is portable across LLM backends. The `dspy.ChainOfThought` and `dspy.ReAct` patterns are translated into explicit prompt scaffolds in our reference files.
- STORM's outline is a Wikipedia hierarchy. Ours is a top-tier-conference paper structure (Abstract / Intro / Related / Method / Experiments / Conclusion / Limitations) with section-specific length budgets and content rules.

## 3. aiming-lab — `AutoResearchClaw`

Repo: https://github.com/aiming-lab/AutoResearchClaw

### What we borrowed

| What | Where it lives in their repo | Where we use it |
|---|---|---|
| 4-layer citation verification (arXiv ID → CrossRef DOI → Semantic Scholar title match → LLM relevance scoring) | their `VerifiedRegistry` | `auto-research-ideation/references/citation-verification.md` |
| HITL collaboration phases with named modes (Idea Workshop / Baseline Navigator / Paper Co-Writer) | their HITL co-pilot modes | `auto-research/references/escalation-policy.md` (interactive vs autonomous) |
| Self-healing repair loop with retry cap (they use 10 rounds) | their `Self-Healing Repair Loop` | `auto-research-execution/references/debug-loop.md` (we cap at 5; surface earlier) |
| Sentinel watchdog for NaN/Inf/consistency | their `Sentinel Watchdog` | `auto-research-execution/references/training-monitor.md` |
| Cost tracking with 50%/80%/100% pause thresholds | their per-token budget | `auto-research/references/integrity-rules.md` Rule 5 |
| Multi-agent specialization (CodeAgent / BenchmarkAgent / FigureAgent) | their multi-agent subsystems | Encoded as separate sub-skills (Method = BenchmarkAgent role, Execution = CodeAgent role, Writing has FigureAgent role internally) |
| AST-validated sandbox for LLM-written code | their AST validation layer | `auto-research-execution/references/sandbox.md` |
| Per-run knowledge base across categories (decisions / experiments / findings / literature / questions / reviews) | their Knowledge Base | `auto-research/references/state-contract.md` (same idea, file-system based) |
| Pause-and-resume across long-running pipelines | their `researchclaw attach/approve/reject` CLI | Our `--run-id` resume mechanism in `state-contract.md` |

### What we changed

- AutoResearchClaw has **23 stages across 8 phases**. We keep **4 stages** because each Claude Code skill is already an LLM-orchestrated unit with its own internal sub-steps; collapsing to 4 keeps the user's mental model simple. Their internal phase-decomposition lives inside our sub-skills as section ordering.
- Their MetaClaw cross-run learning (lessons-from-prior-runs injected as auto-skills) is **deliberately not included** in v1. It's powerful but adds a moving-parts problem (skill injection at runtime). Add later if the user wants it.
- They support 6 HITL levels (full-auto / gate-only / checkpoint / step-by-step / co-pilot / custom). We collapse to 2 (`autonomous` and default `interactive`) with mandatory hard-gates that override either. Easier to reason about.

## 4. Other prior art consulted (not directly borrowed but worth knowing)

- **`teddynote-lab/STORM-Research-Assistant`** — LangGraph reimplementation of STORM. Useful if you want to migrate this skill set onto LangGraph. The state-machine transitions there inform our `state-contract.md`.
- **`OpenReview API`** — used by AI-Scientist for novelty checking. We use it for *gap mining* (read negative reviewer comments to find unsolved real pain points).
- **`HuggingFace OpenReview` mirror** — fallback when OpenReview rate-limits.
- **`Semantic Scholar Academic Graph API`** — preferred citation source (free tier 100 req/5min unauthenticated, higher with API key).

## Quick decision log: why 4 stages, not 23

A 23-stage pipeline is correct for a turnkey product. For a Claude Code skill, fewer-larger stages let the LLM use its own reasoning between steps without having to context-switch through a brittle state machine. The risk of 4 stages is "LLM does too much in one stage and goes off the rails" — we mitigate via the explicit `state-contract.md` between stages and the integrity rules at every transition. The risk of 23 stages would be "user can never resume / debug / understand what stage X is doing" — worse for a skill that real humans must reason about.

## Where to read next

- For execution detail: `auto-research-execution/references/`
- For paper writing detail: `auto-research-writing/references/`
- For ideation detail: `auto-research-ideation/references/`
- For methods/math detail: `auto-research-method/references/`
