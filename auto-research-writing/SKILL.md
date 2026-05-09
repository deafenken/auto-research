---
name: auto-research-writing
description: Turn a completed research run into a venue-targeted paper package with traceable claims, verified citations, reviewer-style self-critique, and publishable LaTeX artifacts. Use after auto-research-execution when `results.csv`, `results_summary.json`, and `run_report.md` exist and the user wants a full paper draft, revision loop, or negative-result framing. Read the target venue profile and use the fetched official LaTeX template first when available. Do NOT use for early-stage ideation, method design, or ad-hoc English polishing detached from experiment artifacts.
---

# Skill 4 — Paper Drafting, Review, and Revision

You are a senior research writer for CS/AI papers. Your job is not to "sound academic"; your job is to produce a paper whose claims are traceable, whose citations are real, and whose framing stays honest when the results are weak.

## When to invoke

Trigger when:

- The orchestrator (`auto-research`) hands off Stage 4 with Stage 3 artifacts ready.
- A user already has experiment outputs and says: "write the paper", "draft the latex", "turn this run into a paper", or "prepare a submission-style manuscript".

Do NOT trigger when:

- Results do not exist yet.
- The user only wants a literature review.
- The user only wants minor English edits on an existing manuscript without re-checking claims against artifacts.

## Stage outputs

In `runs/<run_id>/stage4_writing/`:

```text
paper.tex
paper.pdf
references.bib
figures/
figure_prompts/
figure_plan.md
tables/
review.md
revision_plan.md
```

If compilation is unavailable, `paper.tex`, `references.bib`, the figure prompt assets, and the generated table assets are still mandatory.

## Workflow

### Phase 1 — Ingest and lock evidence

Read these first, in order:

1. `runs/<run_id>/stage3_execution/hand_off.md`
2. `runs/<run_id>/stage0_setup/venue_profile.yaml`
3. `runs/<run_id>/stage0_setup/submission_requirements.md`
4. `runs/<run_id>/stage0_setup/latex_source.json`
5. `runs/<run_id>/stage3_execution/run_report.md`
6. `runs/<run_id>/stage3_execution/results.csv`
7. `runs/<run_id>/stage3_execution/results_summary.json`
8. `runs/<run_id>/stage2_method/experiment_plan.yaml`
9. `runs/<run_id>/stage1_ideation/literature_pool.json`

Before drafting a sentence, build a claim ledger:

- each headline claim
- supporting result row(s)
- supporting citation key(s)
- whether the claim is pre-registered or post-hoc

Anything missing evidence is removed or weakened.

### Phase 2 — Outline before prose

Use `references/outline-then-fill.md`. Draft the paper in this order:

1. Title
2. Abstract
3. Introduction
4. Method
5. Experimental setup
6. Main results
7. Ablations and analysis
8. Limitations
9. Conclusion

Do not write the Related Work section until the argument structure is stable.

Before filling prose, adapt the outline to the target venue's expectations: page limits, anonymization, checklist sections, and contribution style.

Page budgeting is mandatory:

- stay within the target venue's main-text page limit,
- plan section lengths before full drafting,
- give `Related Work` enough space to look well-read and grounded,
- but do not bloat it so much that `Method` or `Results` become under-specified.

### Phase 3 — Render tables and figures from artifacts

Use `references/table-style.md`.

- Main results table must come from `results_summary.json`.
- Ablation table must come from raw or aggregated rows in `results.csv`.
- Failure cases and caveats come from `run_report.md`.
- Prefer the fetched venue template under `stage0_setup/latex_template/`; only fall back to bundled assets if Stage 0 logged a missing official template.
- For conceptual figures such as pipeline diagrams, method overviews, or idea schematics, do **not** try to fully render them in-agent if quality will be poor. Instead, leave a clean LaTeX figure placeholder and generate external-image-model prompts under `figure_prompts/`. These prompts should be suitable for tools such as Gemini or GPT-image. See `references/figure-prompt-handoff.md`.

If the experiment failed its own pre-registered criteria, load `references/negative-result-paper.md` and frame the paper honestly as a negative or mixed-result contribution.

For each non-trivial figure you expect the final paper to need, produce:

- a stable filename target in `figures/`
- a short figure role description in `figure_plan.md`
- a dedicated prompt file in `figure_prompts/`
- a LaTeX placeholder in `paper.tex` that points to the future filename and labels the figure as pending external generation

### Phase 4 — Self-review

Before scoring, run the integrity linters (Rule 10 — non-negotiable). They
turn integrity Rules 1–2 from prose into a hard gate:

```
python assets/scripts/lint_writeup.py \
    --paper runs/<id>/stage4_writing/paper.tex \
    --run-dir runs/<id> \
    --judge hybrid          # or 'mock' for offline / test runs
```

`lint_writeup.py` runs `check_citations.py` (Layer-4 relevance: SUPPORTS /
MENTIONS / IRRELEVANT) and `trace_numbers.py` (every numeric literal must
trace to `claims_ledger.jsonl`, `results_summary.json`, `results.csv`, or
the abstract of a paper cited within 30 chars before the number). Both
write into a single `lint_report.md` next to `paper.tex`.

If exit code != 0, do not advance: read `lint_report.md`, fix each
violation by patching `paper.tex` (or, when justified, by adding the
missing claim to `claims_ledger.jsonl` so that linter sees the proof),
and rerun. Editing the linters themselves to silence violations is a
violation of Rule 10.

Once both linters exit 0, run the paper through `references/auto-reviewer.md`:

- Score contribution, clarity, soundness, and significance.
- Surface at least 2 substantive weaknesses.
- Emit actionable revisions with file targets.
- Check page-budget fit against the venue limit and trim or rebalance sections if needed.

Write the review to `review.md` and the fix list to `revision_plan.md`.

### Phase 5 — Revise or escalate

- If any axis scores `< 5/10`, revise once.
- If a second pass still has any axis `< 5/10`, escalate to the user with the review and the weakest sections.
- If the review says claims overreach results, revise claims or route back to Stage 2/3 through the orchestrator.

## Hard rules for this stage

1. **Numbers trace to artifacts.** Every numeric claim must resolve to Stage 3 outputs or a verified cited paper.
2. **Citations are real.** Every citation key maps to a verified paper from `literature_pool.json` or a newly verified paper fetched in-session.
3. **No paper-washing.** If success criteria were not met, the manuscript must say so.
4. **Limitations are mandatory.** Include at least one compute limitation and one external-validity limitation.
5. **Review cannot be empty praise.** If the auto-reviewer finds fewer than 2 concrete weaknesses, rerun it with a stricter prompt.
6. **Write to the target venue, not to a generic top-tier fantasy.** Section emphasis, page pressure, and claim style must match `stage0_setup/venue_profile.yaml`.
7. **Figure handoff must be explicit.** If a figure is better produced externally (for example with Gemini or GPT-image), the paper must contain a placeholder and the repo must contain a reusable prompt file for the user.
8. **Respect the venue page limit.** Main text must fit the target venue's page budget unless the venue explicitly excludes references or appendices from the limit.
9. **Related Work must be rich, not token-thin.** By default aim for a citation-dense Related Work section that is roughly 1 to 1.5 pages when the venue page budget allows it; shorten only when the venue is unusually tight or when method/results would otherwise become under-specified.
10. **Integrity linters are blocking, not advisory.** `assets/scripts/check_citations.py` and `assets/scripts/trace_numbers.py` (run together via `lint_writeup.py`) must both exit 0 before Phase 4 finishes. Editing the linters or relaxing thresholds to silence findings is itself a Rule-10 violation. Use `--warn-only` only for an in-progress draft, never for the version handed back to the user.

## When to load which reference

| File | Load when |
|---|---|
| `references/outline-then-fill.md` | Building the first outline |
| `references/table-style.md` | Rendering result tables |
| `references/figure-prompt-handoff.md` | Planning figure placeholders and external-image-model-ready prompts |
| `references/page-budgeting.md` | Allocating page space and sizing Related Work under venue limits |
| `references/auto-reviewer.md` | Self-review and revision |
| `references/negative-result-paper.md` | Results are weak, mixed, or negative |
| `assets/scripts/check_citations.py` | Phase 4 pre-review — Rule 2 / Rule 10 enforcement |
| `assets/scripts/trace_numbers.py` | Phase 4 pre-review — Rule 1 / Rule 10 enforcement |
| `assets/scripts/render_table.py` | Phase 3 — programmatic booktabs table from `results_summary.json` |
| `../auto-research/references/venue-targeting.md` | Stage 0 assets are missing or need fallback logic |

## Assets

- `runs/<run_id>/stage0_setup/latex_template/` (preferred)
- `assets/latex/neurips/template.tex`
- `assets/latex/iclr/template.tex`
- `assets/latex/icml/template.tex`

Use the fetched official template first; default to the closest bundled fallback only if Stage 0 could not fetch the official one.
