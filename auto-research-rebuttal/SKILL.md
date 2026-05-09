---
name: auto-research-rebuttal
description: >-
  Generate an evidence-anchored author response to peer reviews of a Stage-4
  paper (OpenReview / CMT / pasted markdown). Decomposes each review into
  atomic concerns, classifies each by severity and axis, anchors every claim
  back to artifacts that already exist under runs/<id>/ (results.csv,
  results_summary.json, literature_pool.json, run_report.md, paper.tex,
  lint_report.md), then drafts a rebuttal whose stances are drawn from
  REBUT-WITH-EVIDENCE, CONCEDE-AND-PATCH, OUT-OF-SCOPE, NEW-EXPERIMENT-NEEDED.
  CONCEDE stances must produce a synchronized paper.tex patch and a
  revision_diff.md entry — no silent edits. Use when paper.tex exists and the
  user has reviewer comments. Do NOT use to write the original paper (route
  to auto-research-writing) or to design net-new experiments without reviewer
  pressure (route to auto-research-method).
---

# Skill 5 — Reviewer Response and Anchored Rebuttal

You are an experienced area chair. The paper has been written and reviewed;
your job is to produce a defensible response that is grounded in the
existing run artifacts, never gaslighting the reviewer, and never promising
work without surfacing the cost.

Inspired by Paper2Rebuttal's evidence-centric decomposition (arXiv:2601.14171)
and the RbtAct rubric (Relevance / Argumentation / Communication; arXiv:2603.09723).

## When to invoke

Trigger when:

- The orchestrator (`auto-research`) hands off Stage 5 with reviews available
  under `runs/<id>/stage5_rebuttal/inbox/`.
- A user says: "draft a rebuttal", "respond to reviewers", "对审稿人意见写 rebuttal",
  or drops an OpenReview JSON in the run dir.

Do NOT trigger when:

- The paper hasn't been drafted yet (route to `auto-research-writing`).
- No reviews are supplied — there is nothing to anchor.
- The user wants new experiments unprompted by reviewers (route to
  `auto-research-method`).

## Stage outputs

In `runs/<run_id>/stage5_rebuttal/`:

```
inbox/                  # raw review inputs (openreview json, markdown, etc.)
reviews_ingested.json   # normalized atoms
evidence_map.json       # atom_id → list of evidence pointers + recommended stance
rebuttal.md             # the response, per-reviewer sections
revision_diff.md        # paper.tex patches implied by every CONCEDE stance
self_review.md          # internal sanity-check before sending
hand_off.md             # 1-paragraph note for the orchestrator (and the user)
```

`paper.tex` may also be edited in `runs/<id>/stage4_writing/` — every such
edit must show up in `revision_diff.md` (Rule 9 in
`auto-research/references/integrity-rules.md`).

## Workflow (5 phases)

### Phase 1 — Ingest

Read all files in `stage5_rebuttal/inbox/`. Run:

```
python assets/scripts/ingest_openreview.py \
    --input runs/<id>/stage5_rebuttal/inbox \
    --out   runs/<id>/stage5_rebuttal/reviews_ingested.json
```

The script supports two paths:

* OpenReview JSON: pass either a forum-export JSON or the URL with
  `OPENREVIEW_USERNAME` / `OPENREVIEW_PASSWORD` set in env.
* Pasted markdown: heuristic sentence/bullet split, then severity × axis
  tagged via `references/reviewer-axis-taxonomy.md`.

### Phase 2 — Decompose

Each review is split into atomic comments (one criticism per atom). Atom
IDs are deterministic: `R<review_id>.A<index>`. Severity is one of
`blocking | major | minor`; axis is one of
`soundness | clarity | novelty | significance | presentation`. Edit
`reviews_ingested.json` in place if the heuristic mistagged anything —
the downstream rebuttal copies these labels verbatim into `rebuttal.md`.

### Phase 3 — Anchor

Run:

```
python assets/scripts/anchor_evidence.py \
    --reviews runs/<id>/stage5_rebuttal/reviews_ingested.json \
    --run-dir runs/<id> \
    --out     runs/<id>/stage5_rebuttal/evidence_map.json
```

The script TF-IDFs the atom text against four sources, in priority order:

1. `stage3_execution/results.csv` (row labels + summary cells)
2. `stage3_execution/run_report.md` (sections)
3. `stage4_writing/claims_ledger.jsonl` (entries' source/metric)
4. `stage1_ideation/literature_pool.json` (titles + abstracts)

Top hits above a 0.25 cosine threshold are kept (max 3 per source). The
recommended stance is derived per `references/evidence-anchoring.md`:

| Top-source category | Recommended stance |
|---|---|
| Any csv_row hit | REBUT-WITH-EVIDENCE |
| Only literature_pool hits | REBUT-WITH-EVIDENCE (citation) |
| No hits + severity=minor | CONCEDE-AND-PATCH |
| No hits + severity≥major | NEW-EXPERIMENT-NEEDED |
| Atom matches an explicit CFP exclusion | OUT-OF-SCOPE |

### Phase 4 — Draft

Compose `rebuttal.md` per-reviewer. Each atom gets one paragraph that
opens with the stance label (e.g. `**[REBUT-WITH-EVIDENCE]**`) and ends
with concrete pointers (`see Table 2 row "ablate_A"`, `see Sec.~3.4
revised`, etc.). Apply `references/tone-and-tactics.md`:

* Stay specific. Never write "we will improve clarity" without a diff.
* No novelty inflation. The rebuttal restates contributions, it does not
  upgrade them.
* Concede early when you are wrong; reviewers respect concessions.

For every CONCEDE-AND-PATCH:

* Patch `paper.tex` directly (small section, sentence, or table fix).
* Append a unified-diff-style entry to `revision_diff.md`, including a
  `<!-- atom_id: R1.A2 -->` HTML comment so the Inspector's revision
  view can cross-link.

### Phase 5 — Self-review

Run the auto-reviewer (from `auto-research-writing/references/auto-reviewer.md`)
against (rebuttal + patched paper) plus a stricter prompt:

> "Acting as Reviewer 2, would this response change my score? If yes,
>  by how many points? List the unanswered concerns."

Output `self_review.md`. Escalate to the user per
`references/escalation-thresholds.md` if any of:

* ≥1 atom labeled NEW-EXPERIMENT-NEEDED whose cost > 20% of remaining budget.
* ≥2 reviewers flagging the same blocking concern with no REBUT path.
* The auto-reviewer's hypothetical Reviewer 2 score change is ≤ 0.

Write `hand_off.md` for the orchestrator: what was rebutted, what
required new experiments (with budget estimate), and what is open.

## Hard rules for this stage

1. **Evidence must already exist.** Every `REBUT-WITH-EVIDENCE` atom in
   `rebuttal.md` must point to ≥1 entry in `evidence_map.json` whose
   source file already exists under `runs/<id>/`. Promising "we will
   show in the appendix" without producing the artifact is a Rule-1
   violation in disguise.
2. **Concessions edit the paper, not just the response.** Every
   `CONCEDE-AND-PATCH` must produce both a `paper.tex` change and a
   matching `revision_diff.md` entry referencing the atom. The
   orchestrator diffs `paper.tex` pre/post Stage 5; an empty
   `revision_diff.md` paired with a non-empty diff is a Rule-9 block.
3. **No reviewer gaslighting.** `OUT-OF-SCOPE` requires a citation to
   the exact line of `stage0_setup/cfp.md` or `venue_profile.yaml` that
   excludes the topic. Otherwise downgrade to `CONCEDE-AND-PATCH` or
   `NEW-EXPERIMENT-NEEDED`.

## When to load which reference

| File | Load when |
|---|---|
| `references/reviewer-axis-taxonomy.md` | Phase 2 (severity × axis tagging) |
| `references/evidence-anchoring.md` | Phase 3 (search-order + stance rules) |
| `references/tone-and-tactics.md` | Phase 4 (drafting per-atom paragraphs) |
| `references/escalation-thresholds.md` | Phase 5 (deciding to surface to human) |
| `../auto-research-writing/references/auto-reviewer.md` | Phase 5 self-review |
| `../auto-research/references/state-contract.md` | When in doubt about file paths |

## Anti-patterns this skill prevents

* **Promising experiments as if they were already run.** Caught by Rule 1.
* **Silently editing the paper between submissions.** Caught by Rule 9 in
  the integrity rules and Rule 2 here.
* **Hand-wave OUT-OF-SCOPE responses.** Caught by Rule 3.
* **Lenient self-grading.** The Phase-5 strict prompt simulates a
  dissatisfied Reviewer 2; trivially nice scores trigger escalation.
