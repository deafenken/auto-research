# Notation Discipline

The single most common reason a method section gets reviewer complaints is inconsistent notation. The fix is mechanical: build a notation table, use it, never deviate.

## The notation table

Every symbol you intend to use, defined once. Place it in `method.md` at the start of the formal section. Update it when you add a symbol — never silently introduce one.

```markdown
| Symbol | Role | Domain | First appearance |
|---|---|---|---|
| $x \in \mathcal{X}$ | input example | $\mathbb{R}^d$ | §3.1 |
| $y \in \mathcal{Y}$ | label | $\{0, 1, \dots, K-1\}$ | §3.1 |
| $f_\theta : \mathcal{X} \to \mathbb{R}^K$ | model with parameters $\theta$ | — | §3.2 |
| $\mathcal{L}(\theta; x, y)$ | per-example loss | $\mathbb{R}_{\geq 0}$ | §3.2 |
| $\mathcal{D} = \{(x_i, y_i)\}_{i=1}^N$ | training set | — | §3.1 |
```

## Conventions (NeurIPS / ICLR style)

These match the de-facto standards in modern ML papers. Follow them unless the subarea has an established override.

### Vectors & matrices

- **Lowercase italic** for scalars: `$x$, $y$, $\alpha$, $\lambda$`.
- **Lowercase bold italic** for vectors: `$\boldsymbol{x}$, $\boldsymbol{w}$`. Or plain italic if context is unambiguous and you state so.
- **Uppercase bold** for matrices: `$\mathbf{W}$, $\mathbf{X}$`.
- **Uppercase italic** for tensors of rank ≥ 3: `$X \in \mathbb{R}^{B \times T \times D}$`.

### Sets & spaces

- **Calligraphic** for sets: `$\mathcal{X}, \mathcal{Y}, \mathcal{D}, \mathcal{F}$`.
- **Blackboard bold** for number systems: `$\mathbb{R}, \mathbb{R}^d, \mathbb{N}, \mathbb{Z}_{\geq 0}$`.
- **Uppercase Greek** for parameters of distributions: `$\Theta, \Sigma$`.

### Functions & operators

- Use `$\operatorname{softmax}$, $\operatorname{argmax}$` (not italic, not regular).
- Loss functions: `$\mathcal{L}, \ell$`. Use `$\mathcal{L}$` for full-dataset loss, `$\ell$` for per-example.
- Expectations: `$\mathbb{E}_{x \sim p}[\cdot]$`. Always specify the distribution.
- Norms: `$\|\cdot\|_2, \|\cdot\|_F$`. Specify which.

### Indices

- `$i, j$` for examples or indices.
- `$t$` for timestep / iteration.
- `$l$` for layer.
- `$h$` for attention head.
- `$k$` for class.
- `$n, N$` for sample size; `$d, D$` for dimensionality.
- `$b, B$` for batch.

Never reuse an index for two roles in the same section. If you need both an example index and a class index, use `$i$` and `$k$` not `$i$` and `$j$` (the latter is too easy to confuse).

### Distributions & parameters

- Data distribution: `$p_{\text{data}}$` or `$\mathcal{D}$`.
- Model distribution: `$p_\theta$`.
- Prior: `$p(\theta)$`. Posterior: `$p(\theta | \mathcal{D})$`.
- KL divergence: `$\operatorname{KL}(p \| q)$` (with `\|`).

### Probability vs. estimate

- Use `$\hat{y}$` for an estimate, `$y$` for ground truth.
- Use `$\theta^\ast$` for the optimum, `$\theta_t$` for the iterate at step `$t$`.

## Anti-patterns

- **Symbol reuse in the same equation.** `$\sum_i x_i \cdot x$` — is the second `$x$` the same as `$x_i$`? Reader gives up.
- **Implicit dimensions.** `$\mathbf{W} \mathbf{x}$` without saying `$\mathbf{W} \in \mathbb{R}^{m \times d}, \mathbf{x} \in \mathbb{R}^d$`.
- **Operators introduced mid-equation.** First time `$\odot$` appears, define it.
- **`$\sigma$` for two things.** The most common collision in ML: `$\sigma$` is sigmoid AND standard deviation. Pick one or rename.
- **`$\alpha, \beta, \gamma, \delta$` as four different "tuning" hyperparameters.** Distinguishable to you, opaque to the reader. Use names: `$\lambda_{\text{rec}}, \lambda_{\text{kl}}$`.
- **Bold/non-bold inconsistency.** `$\mathbf{x}$` in equation, `$x$` in text. Pick one.

## Concrete tensor shapes

For deep-learning papers, **always** state shapes explicitly when introducing a tensor. Reviewers read shape annotations as a sanity check.

Bad:

> Let `$Q, K, V$` be the query, key, and value matrices.

Good:

> Let `$Q \in \mathbb{R}^{B \times H \times T \times d_k}$, $K \in \mathbb{R}^{B \times H \times T \times d_k}$, $V \in \mathbb{R}^{B \times H \times T \times d_v}$` be the query, key, and value tensors, with batch size `$B$`, head count `$H$`, sequence length `$T$`, and per-head dimensionalities `$d_k, d_v$`.

## When to deviate from these conventions

- A subfield (e.g. theoretical RL) has its own well-established notation. Match it.
- The equation is so dense the standard convention makes it unreadable. Override locally with a "for this section, we use…" footnote.

Never deviate just because "I prefer X". Reviewers don't share your preferences.

## Sanity check before finalizing

Run this scan on `method.md`:

1. Every symbol used in equations appears in the notation table.
2. Every symbol in the table appears in at least one equation.
3. No symbol is overloaded (used for two distinct roles).
4. Every tensor's shape is stated at first introduction.
5. The notation table's "first appearance" column is accurate.

If any check fails, fix before sending to Stage 3.
