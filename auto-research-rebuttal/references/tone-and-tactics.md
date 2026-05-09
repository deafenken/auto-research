# Tone and Tactics for `rebuttal.md`

Style guide for Phase 4 drafting. The point is to produce something a
real area chair would read without rolling their eyes.

## Per-venue defaults

* **OpenReview venues (ICLR, NeurIPS Main, ACL ARR)** — public, indexed
  by reviewers' future co-authors. No sarcasm, no all-caps, no "we
  respectfully submit". Be terse and specific.
* **CMT venues (NeurIPS Track datasets/benchmarks, CVPR)** — private to
  ACs and reviewers; you can reference unpublished ablations as long as
  they exist in `runs/<id>/`.
* **Workshop and journal venues** — match the existing thread's tone.
  If the reviewer wrote 2 sentences, your atom-level response should be
  one sentence with a pointer.

## Per-stance template

`REBUT-WITH-EVIDENCE`:
```
**[REBUT-WITH-EVIDENCE]** <restate concern>. <one-sentence rebuttal>.
See <pointer> (e.g. Table 2 row "ablate_A": metric drops 2.1pp, matching
our success criterion).
```

`CONCEDE-AND-PATCH`:
```
**[CONCEDE-AND-PATCH]** Agreed — <restate>. We have updated <Sec.~X.Y> to
<new sentence/clarification>; see `revision_diff.md` (atom R1.A2).
```

`OUT-OF-SCOPE`:
```
**[OUT-OF-SCOPE]** This concern would require <topic>, which the
<venue> CFP explicitly excludes ("<verbatim quote>", cfp.md L42). We
have added a one-line note to Limitations (Sec.~6) so future readers
are not misled.
```

`NEW-EXPERIMENT-NEEDED`:
```
**[NEW-EXPERIMENT-NEEDED]** We do not currently have <X>. Estimated
cost: <Y GPU-hours>. We can deliver <deliverable> by <date> if the AC
agrees; otherwise we will treat this as a Limitation (Sec.~6).
```

The bracketed stance label is mechanical — it lets the Inspector's
rebuttal view filter and colour-code without re-parsing prose.

## Tactics that age well

1. **Quote the reviewer.** A two-line quote up front anchors your reply
   to the actual concern, not your reading of it.
2. **Cite your own table.** A row name plus a metric is more convincing
   than a paragraph of prose.
3. **Concede the smallest unit possible.** "Yes, in Sec.~3.4, the second
   sentence is misleading" is better than "Yes, the related work is weak".
4. **Limit speculation.** Don't say "the reviewer may have meant" — ask.

## Tactics that age badly

* "We thank the reviewer for the comprehensive review" stuffed into
  every reply — pads length without adding evidence.
* "Will be added in the camera-ready" without an accompanying
  `revision_diff.md` entry — Rule 2 violation here.
* Reframing weaknesses as future work without a budget. The plan
  already has a budget; promise within it.
* Inflating contributions ("we provide a fundamentally new view"). The
  paper hasn't changed; promotional language now will read worse to
  the AC than to the reviewer.
