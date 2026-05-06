# Auto-Reviewer

Use this rubric after a full draft exists.

## Axes

- `contribution`: is there a real research claim beyond engineering cleanup?
- `clarity`: can a reviewer reconstruct the method and evidence quickly?
- `soundness`: do the experiments support the claims without hidden confounds?
- `significance`: would a top venue audience care?

Score each axis from `1` to `10`.

## Required output format

```markdown
Score: contribution X/10 | clarity X/10 | soundness X/10 | significance X/10
Overall: <accept | weak accept | borderline | weak reject | reject>

Strengths:
- ...

Weaknesses:
- ...

Required revisions before resubmit:
- [ ] file-or-section target + concrete fix
```

## Review discipline

1. Cite exact sections, tables, or figures when criticizing.
2. Surface at least 2 weaknesses. A review with fewer than 2 is invalid.
3. Prefer reviewer language: "claim unsupported", "baseline stale", "OOD evidence missing", "ablation confounded".
4. Check whether the paper hides a failed primary hypothesis inside a softer secondary claim.
5. If the work is mainly a negative result, judge whether that negative result is still informative and well-supported.

## Overall rating heuristic

- `accept`: all axes `>= 7`
- `weak accept`: no axis `< 6`, average `>= 6.5`
- `borderline`: average `>= 5.5`
- `weak reject`: any axis `< 5`
- `reject`: soundness `< 4` or contribution `< 4`
