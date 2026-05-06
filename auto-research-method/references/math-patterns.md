# Math Patterns — common derivations done right

A bank of standard mathematical patterns in CS/AI papers. Use these as templates so the math reads as conventional and trustworthy, not exotic and suspect.

For each pattern: when to use, the canonical form, common variants, and pitfalls.

## 1. Empirical risk minimization

**Use when:** stating any supervised learning objective.

```latex
\theta^\ast \in \arg\min_{\theta \in \Theta}
  \frac{1}{N} \sum_{i=1}^{N} \ell\big(f_\theta(x_i), y_i\big) + \lambda \, \Omega(\theta)
```

- `$\Omega(\theta)$` is the regularizer; explicit weight `$\lambda$`.
- Use `$\arg\min$` (with `\arg\min`), not `\argmin`.
- Use `$\in$` not `=` because the argmin may not be unique.

## 2. Stochastic gradient descent step

**Use when:** describing an optimizer.

```latex
\theta_{t+1} = \theta_t - \eta_t \, \nabla_\theta \mathcal{L}(\theta_t; \mathcal{B}_t)
```

- `$\eta_t$` is the learning rate at step `$t$` — explicit even if it's constant.
- `$\mathcal{B}_t$` is the minibatch.
- For Adam: write the full update, do not say "Adam optimizer was used" without the moment definitions.

## 3. Softmax & log-softmax

**Use when:** describing classification head, attention, policy.

```latex
\operatorname{softmax}(z)_k = \frac{\exp(z_k)}{\sum_{j=1}^{K} \exp(z_j)}, \quad k = 1, \dots, K
```

- Always use `$\operatorname{softmax}$` (roman, not italic).
- For numerical-stability claims, derive via subtracting `$\max_j z_j$`.

## 4. Cross-entropy loss

**Use when:** classification.

```latex
\ell_{\text{CE}}(z, y) = - \log \operatorname{softmax}(z)_y
              \;=\; - z_y + \log \sum_{j=1}^{K} \exp(z_j)
```

The right-hand-side form (log-sum-exp) shows the log-partition; preferred when later talking about temperature scaling.

## 5. KL divergence

**Use when:** distillation, RL, variational methods.

```latex
\operatorname{KL}(p \,\|\, q) = \sum_{x \in \mathcal{X}} p(x) \log \frac{p(x)}{q(x)}
```

- Use `\|` for the bar between distributions, not `|` (single bar = conditioning).
- Specify domain `$\mathcal{X}$`.
- For continuous: replace sum with `$\int$` and probabilities with densities.

## 6. Attention (scaled dot-product)

**Use when:** transformer or attention-based methods.

```latex
\operatorname{Attention}(Q, K, V) = \operatorname{softmax}\left( \frac{Q K^\top}{\sqrt{d_k}} \right) V
```

With shapes:

```latex
Q \in \mathbb{R}^{B \times H \times T_q \times d_k},\quad
K \in \mathbb{R}^{B \times H \times T_k \times d_k},\quad
V \in \mathbb{R}^{B \times H \times T_k \times d_v}
```

For masked attention add element-wise mask before softmax:

```latex
\operatorname{softmax}\left( \frac{Q K^\top}{\sqrt{d_k}} + M \right)
\quad \text{where } M_{ij} \in \{0, -\infty\}
```

## 7. Variational lower bound (ELBO)

**Use when:** VAEs, variational inference, certain RL formulations.

```latex
\log p_\theta(x) \;\geq\;
  \mathbb{E}_{q_\phi(z|x)} \big[ \log p_\theta(x | z) \big]
  - \operatorname{KL}\big( q_\phi(z|x) \,\|\, p(z) \big)
```

State both terms explicitly. Common error: dropping the prior term.

## 8. Policy gradient

**Use when:** RL, RLHF.

```latex
\nabla_\theta J(\theta)
  = \mathbb{E}_{\tau \sim p_\theta}
    \left[ \sum_{t=0}^{T} \nabla_\theta \log \pi_\theta(a_t | s_t) \, A_t \right]
```

Define the advantage `$A_t$` explicitly (TD residual? Generalized Advantage Estimate?).

## 9. Reparameterization trick

**Use when:** training models with continuous latent variables.

```latex
z = \mu_\phi(x) + \sigma_\phi(x) \odot \epsilon, \quad \epsilon \sim \mathcal{N}(0, I)
```

- `$\odot$` is element-wise (define it in notation table).
- `$\mu_\phi, \sigma_\phi$` are neural-network outputs; write their domains.

## 10. Contrastive loss (InfoNCE)

**Use when:** self-supervised representation learning.

```latex
\mathcal{L}_{\text{NCE}} = - \log
  \frac{\exp(\operatorname{sim}(z_i, z_j) / \tau)}
       {\sum_{k=1}^{2N} \mathbf{1}_{[k \neq i]} \exp(\operatorname{sim}(z_i, z_k) / \tau)}
```

- Define `$\operatorname{sim}$` (cosine? dot product?).
- `$\tau > 0$` is the temperature; state typical range.
- `$\mathbf{1}_{[\cdot]}$` is the indicator function — define it.

## 11. Diffusion forward / reverse

**Use when:** diffusion / score-based models.

Forward (noising):
```latex
q(x_t | x_{t-1}) = \mathcal{N}(x_t; \sqrt{1 - \beta_t} \, x_{t-1}, \beta_t I)
```

Reverse (model):
```latex
p_\theta(x_{t-1} | x_t) = \mathcal{N}\big(x_{t-1}; \mu_\theta(x_t, t), \Sigma_\theta(x_t, t)\big)
```

Always state the noise schedule `$\beta_t$` family (linear / cosine / etc.) when introducing.

## 12. Big-O complexity

**Use when:** complexity analysis.

```latex
\mathcal{O}(N^2 d) \quad \text{time, } \quad \mathcal{O}(N d) \quad \text{memory}
```

- Use `$\mathcal{O}$` (calligraphic) — `$O$` is also acceptable but be consistent.
- Always state: time vs memory vs communication.
- For attention specifically: `$\mathcal{O}(T^2 d_k)$` — and call out the term that dominates.

## 13. Generalization / PAC bounds

**Use when:** stating theoretical guarantees.

Generic form:

```latex
\mathbb{P}\Big[
  \mathcal{R}(\theta) \leq \hat{\mathcal{R}}(\theta) + B(N, \delta, \cdot)
\Big] \geq 1 - \delta
```

- `$\mathcal{R}$` = true risk; `$\hat{\mathcal{R}}$` = empirical risk.
- `$B$` = bound term, often involves `$N$` and a complexity measure.
- `$\delta$` = confidence parameter.
- *Always* state assumptions (i.i.d., bounded loss, etc.).

## 14. Convergence rate

**Use when:** stating optimization theory results.

```latex
\mathbb{E}\big[\|\nabla \mathcal{L}(\theta_T)\|^2\big] \leq \mathcal{O}(1 / \sqrt{T})
```

- Specify whether convex / non-convex / smooth / strongly-convex assumptions.
- Specify which iterate (`$\theta_T$` last? best? average?).

## How to compose patterns

A well-written method section is usually 3-5 of these stitched in order:

1. Problem setup (Pattern 1).
2. Standard objective (Patterns 2, 4).
3. Your modification (custom — but using same notation conventions).
4. Optimization detail (Pattern 2 with custom step).
5. Either complexity analysis (Pattern 12) or convergence claim (Pattern 14).

If your method needs a pattern not in this bank, add it here. Add to the bank, don't reinvent in-paper.

## Cross-reference

Pitfalls and common errors are in `math-pitfalls.md`. Read both files before writing equations.
