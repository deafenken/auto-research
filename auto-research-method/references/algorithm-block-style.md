# Algorithm Block Style

Conventions for the algorithm block (`Algorithm 1: Our Method`) that appears in the Method section. Reviewers read these blocks first to understand the actual procedure; if it's unclear or incomplete, the rest of the section gets less benefit-of-the-doubt.

## Default style: numbered + indented

For LaTeX, use the `algorithm` + `algpseudocodex` (or `algorithmic`) packages. Example:

```latex
\begin{algorithm}[t]
\caption{Verifier-Guided Decoding (VGD)}
\label{alg:vgd}
\begin{algorithmic}[1]
\Require Prompt $x$, base LM $\pi_\theta$, verifier $v_\phi$, beam width $B$, threshold $\tau$
\Ensure Decoded sequence $y_{1:T}$
\State $\text{cands} \gets \{ (\emptyset, 0) \}$ \Comment{(prefix, score)}
\For{$t = 1, \dots, T$}
  \State $\text{ext} \gets \emptyset$
  \For{$(y_{1:t-1}, s) \in \text{cands}$}
    \State $\mathcal{C}_t \gets \operatorname{topk}_B \pi_\theta(\cdot \mid x, y_{1:t-1})$
    \For{$y_t \in \mathcal{C}_t$}
      \State $\text{ext} \gets \text{ext} \cup \{ (y_{1:t-1} \oplus y_t,\, s + \log \pi_\theta(y_t \mid x, y_{1:t-1})) \}$
    \EndFor
  \EndFor
  \State $\text{scored} \gets \{ (y, s + \alpha v_\phi(y)) : (y, s) \in \text{ext} \}$
  \State $\text{cands} \gets \operatorname{topk}_B \text{scored}$ \Comment{Re-rank by combined score}
  \If{$\max_{(y,s) \in \text{cands}} v_\phi(y) > \tau$}
    \State \Return $\arg\max_{(y,s) \in \text{cands}} s$
  \EndIf
\EndFor
\State \Return $\arg\max_{(y,s) \in \text{cands}} s$
\end{algorithmic}
\end{algorithm}
```

## Required components

| Component | Convention | Why |
|---|---|---|
| `\Require` | List ALL inputs with types/domains | Reader can implement directly |
| `\Ensure` | Output description | Reader knows what to expect |
| `\State` | Numbered procedure steps | Easy to reference ("see Line 7") |
| `\Comment{}` | One-line clarifier | Demystifies a non-obvious step |
| `\caption{}` | Concise descriptive name | Appears in paper's algorithm index |
| `\label{}` | For cross-refs in the paper | "Algorithm \ref{alg:vgd} ..." |

## Style rules

### Variable names

Use the same symbols as in the math section. If the math uses `$\theta$`, the algorithm uses `$\theta$`, not `params`.

Numeric subscripts in algorithms are fine: `$y_t$`, `$y_{1:t-1}$`, `$\mathcal{C}_t$`.

### Hyperparameter visibility

Every hyperparameter that affects behavior must appear in `\Require`. Don't write `topk_B` without B being a Require'd parameter.

If you have many hyperparameters, group them into a config object: `\Require Config $\mathbf{c}$ with fields $B, \tau, \alpha, \dots$`. But individual hyperparameters used in the algorithm body should still be referenced explicitly.

### Computation cost annotations

When a step is expensive or has notable complexity, annotate:

```latex
\State $\mathcal{C}_t \gets \operatorname{topk}_B \pi_\theta(\cdot \mid x, y_{1:t-1})$
       \Comment{$\mathcal{O}(B \log V)$, requires LM forward pass}
```

This pre-empts "what's the actual cost?" questions.

### Loops & conditionals

Use `\For{...} \EndFor`, `\If{...} \Else \EndIf`, `\While{...} \EndWhile`. Keep nesting ≤ 3 deep — if you need 4 levels, factor out a sub-procedure.

### Sub-procedures

For methods with > ~25 algorithm lines, factor out helpers:

```latex
\Procedure{ReRank}{candidates, $\alpha$}
  \State $\text{scored} \gets \{ (y, s + \alpha v_\phi(y)) : (y, s) \in \text{candidates} \}$
  \State \Return $\operatorname{topk}_B \text{scored}$
\EndProcedure
```

Then call `\State $\text{cands} \gets \Call{ReRank}{\text{ext}, \alpha}$`.

## Anti-patterns

### Anti-pattern 1: the algorithm is just a paragraph in code form

Algorithm blocks should expose *structure* — loops, conditionals, dataflow. If your algorithm has no control flow, it's not an algorithm; it's an equation.

```latex
% BAD — this is an equation pretending to be an algorithm
\begin{algorithm}
  \State $y = f(x; \theta)$
  \State \Return $y$
\end{algorithm}
```

### Anti-pattern 2: silent assumptions

```latex
% BAD
\State $\text{cands} \gets \operatorname{topk}_B \pi_\theta(\cdot)$  % topk by what??
```

State the scoring function explicitly. The reader cannot guess.

### Anti-pattern 3: pseudocode with executable code

Don't paste Python in the algorithm block. Pseudocode reads at the level of math, not code. If you need to share runnable code, point to the appendix or supplementary.

### Anti-pattern 4: hidden initialization

```latex
% BAD
\State $\text{cands} \gets \text{cands} \cup \{...\}$  % what was cands initialized to?
```

Always show initial values.

### Anti-pattern 5: forgetting termination

Make sure every loop terminates and every recursion has a base case. Reviewers verify this.

## Pseudocode in `pseudocode.py` (Stage 2 hand-off, not paper)

In addition to the LaTeX algorithm block, write `runs/<id>/stage2_method/pseudocode.py` — a Python-flavored expression of the same procedure for Stage 3 to use as a starting point.

```python
# pseudocode.py — NOT runnable; for Stage 3 reference only.

def vgd(prompt, base_lm, verifier, beam_width=4, threshold=0.9, alpha=1.0, max_steps=128):
    """
    Verifier-Guided Decoding.

    Inputs:
        prompt: List[int]  — token IDs
        base_lm: callable(prefix) -> next-token logits, shape (V,)
        verifier: callable(prefix) -> scalar in [0, 1]
        beam_width: int
        threshold: float in [0, 1]
        alpha: float — weight on verifier score
        max_steps: int

    Output:
        List[int] — decoded token IDs
    """
    candidates = [(tuple(), 0.0)]  # (prefix, log-prob score)
    for t in range(max_steps):
        extended = []
        for prefix, score in candidates:
            logits = base_lm(prompt + list(prefix))
            top_token_ids = topk_indices(logits, beam_width)
            for tok in top_token_ids:
                extended.append((prefix + (tok,), score + log(softmax(logits)[tok])))

        scored = [(prefix, score + alpha * verifier(prompt + list(prefix)))
                  for prefix, score in extended]
        candidates = topk_by_score(scored, beam_width)

        # Early stop if any candidate is highly verified.
        if any(verifier(prompt + list(p)) > threshold for p, _ in candidates):
            best = max(candidates, key=lambda c: c[1])
            return list(best[0])

    return list(max(candidates, key=lambda c: c[1])[0])
```

The Python-flavored version makes Stage 3's job concrete. It does not need to be syntactically perfect — the goal is unambiguous semantics.

## Cross-references

The LaTeX algorithm block goes into `paper.tex` (Stage 4). The Python pseudocode goes into `runs/<id>/stage2_method/pseudocode.py` and is read by Stage 3. They should be semantically identical.
