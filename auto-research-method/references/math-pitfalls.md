# Math Pitfalls

Specific patterns of broken math that show up in LLM-generated method sections. Run through this list before finalizing equations.

## 1. Dimension mismatch

**Symptom.** An equation that doesn't type-check.

```latex
% BROKEN
\mathbf{h} = \mathbf{W} \mathbf{x} + \mathbf{b},\quad
  \mathbf{W} \in \mathbb{R}^{d_h \times d_x},\;
  \mathbf{x} \in \mathbb{R}^{d_x},\;
  \mathbf{b} \in \mathbb{R}^{d_x}
% Wait — b should be in R^{d_h} if h is in R^{d_h}.
```

**Fix.** Type-check every linear operation manually. State all shapes.

## 2. Silent broadcasting

**Symptom.** Element-wise operation where the operands are stated as having different ranks.

```latex
% BROKEN
\mathbf{Z} = \mathbf{X} + \boldsymbol{\beta},\quad
  \mathbf{X} \in \mathbb{R}^{B \times D},\;
  \boldsymbol{\beta} \in \mathbb{R}^{D}
% This works in numpy via broadcasting but should be written explicitly.
```

**Fix.** State broadcasting if used:

```latex
\mathbf{Z}_{i,d} = \mathbf{X}_{i,d} + \beta_d \quad \forall i, d
```

Or pre-expand:

```latex
\mathbf{Z} = \mathbf{X} + \mathbf{1}_B \boldsymbol{\beta}^\top
```

## 3. Conditional vs joint distribution confusion

**Symptom.** Using `$p(x, y)$` when you mean `$p(x | y)$`, or vice versa.

```latex
% Common in RL papers
\nabla J(\theta) = \mathbb{E}_{p_\theta(\tau)} [\nabla \log p_\theta(\tau) R(\tau)]
```

Make explicit: is `$p_\theta(\tau)$` the joint over actions and states, or the conditional given the start state? It changes the gradient.

## 4. Loss vs. negative log-likelihood sign

**Symptom.** Forgetting to flip the sign somewhere.

```latex
% Cross-entropy is - log p(y|x)
% Maximum likelihood is max log p(y|x)  <==>  min - log p(y|x)
```

The minus sign is not optional. Reviewers do not forget this.

## 5. Expectation over the wrong distribution

**Symptom.** `$\mathbb{E}_{p}$` where it should be `$\mathbb{E}_{q}$`.

In RL, the policy gradient is over `$\mathbb{E}_{\tau \sim p_\theta(\tau)}$`. If you write `$\mathbb{E}_{\tau \sim \pi^\ast}$`, you're computing a different quantity. Importance sampling correction needed if the distributions differ.

Always be explicit:

```latex
\mathbb{E}_{x \sim p_{\text{data}}}[\cdot]   % over the data distribution
\mathbb{E}_{x \sim p_\theta}[\cdot]          % over the model distribution
\mathbb{E}_{x \sim q_\phi(x|c)}[\cdot]       % over a learned distribution conditioned on c
```

## 6. KL divergence direction

**Symptom.** Using `$\operatorname{KL}(p \| q)$` when you mean `$\operatorname{KL}(q \| p)$`.

These are NOT symmetric. They have different optimization properties:

- `$\operatorname{KL}(p_{\text{data}} \| p_\theta)$` = mode-covering (forces `$p_\theta$` to cover all modes of data).
- `$\operatorname{KL}(p_\theta \| p_{\text{data}})$` = mode-seeking (concentrates `$p_\theta$` on one mode).

Maximum-likelihood training does the former. RLHF KL penalty often does the latter.

## 7. Softmax temperature missing

**Symptom.** A softmax in your method that is silently `$\tau = 1$` when other parts of the system use `$\tau \neq 1$`.

```latex
% You wrote:
p_k = \frac{\exp(z_k)}{\sum_j \exp(z_j)}
% But your decoder uses temperature 0.7 in inference.
```

If temperature matters for your method, write it:

```latex
p_k = \frac{\exp(z_k / \tau)}{\sum_j \exp(z_j / \tau)}, \quad \tau > 0
```

## 8. Gradient through a stop-grad operator

**Symptom.** Claiming a gradient flows through what is actually a stop-gradient (e.g. the target network in RL, the EMA in self-supervised learning).

```latex
% BROKEN — implies gradient through both arguments
\mathcal{L} = \| f_\theta(x) - f_{\theta'}(x') \|^2

% CORRECT — show the stop_grad
\mathcal{L} = \| f_\theta(x) - \operatorname{sg}\big[ f_{\theta'}(x') \big] \|^2
```

Define `$\operatorname{sg}$` (stop-gradient) in the notation table.

## 9. Log of probability when probability can be 0

**Symptom.** `$\log p$` in a setting where `$p$` is allowed to be exactly 0.

For categorical distributions over a finite support, this is fine because `$p_k > 0$` for all `$k$` after softmax. For mixtures, masked outputs, or hard-attention, you may have `$p = 0$` somewhere → `$\log p = -\infty$` and gradients explode.

Either prove `$p > 0$` always, or add `$\log(p + \epsilon)$` and state `$\epsilon$`.

## 10. Sample size in a "law of large numbers" claim

**Symptom.** Asserting empirical mean `$\to$` true mean without N being large enough.

If you train on N=128 examples and write "by the law of large numbers, our empirical risk approximates the true risk," reviewers will ridicule.

LLN requires `$N \to \infty$` and is a *limit*. For finite N, use concentration bounds (Hoeffding, Bernstein) and state the deviation.

## 11. Big-O hiding the bad term

**Symptom.** `$\mathcal{O}(N \log N)$` when one of the constants depends on something that grows.

```latex
% BROKEN
% Method is O(N log N) where N is sequence length.
% But the constant has a factor of d^2 (model dimension), and d is huge.
```

Either write `$\mathcal{O}(d^2 N \log N)$`, or switch to "for fixed d, our method is $\mathcal{O}(N \log N)$".

## 12. Norm without subscript

**Symptom.** `$\|\cdot\|$` with no subscript.

This is usually `$L_2$` by convention, but conventions vary by field. Always subscript on first appearance and then drop only if the section is short.

```latex
\|x\|_2  % Euclidean
\|x\|_1  % L1 / Manhattan
\|x\|_\infty  % max
\|A\|_F  % Frobenius
\|A\|_{op}  % operator norm
```

## 13. Assumption stated post-hoc

**Symptom.** Theorem 1 holds. *Then later:* "We assume the loss is convex."

The convexity is a major assumption that decides whether the theorem applies. State all assumptions upfront, in the theorem statement.

```latex
% GOOD
\textbf{Theorem 1.} Assume:
(A1) f is L-smooth and convex.
(A2) gradient noise has bounded variance \sigma^2.
Then SGD with step size \eta = 1/L satisfies ...
```

## 14. Integer vs. real-valued mismatch

**Symptom.** Writing `$x \in \mathbb{R}^d$` when `$x$` is actually a sequence of token IDs (integers).

For an LLM input, `$x \in \{0, 1, \dots, V-1\}^L$` where `$V$` is vocab size. Or use `$x \in \mathcal{V}^L$` and define `$\mathcal{V}$`.

## 15. Probability vs. log-probability sloppy

**Symptom.** Adding probabilities when you should be multiplying, or vice versa.

```latex
% BROKEN
p(y_1, y_2 | x) = p(y_1 | x) + p(y_2 | x)
% Should be:
p(y_1, y_2 | x) = p(y_1 | x) \cdot p(y_2 | x, y_1)  % chain rule
```

In log space:

```latex
\log p(y_1, y_2 | x) = \log p(y_1 | x) + \log p(y_2 | x, y_1)
```

The above is also frequently broken: people drop the conditioning on `$y_1$` in the second term.

## Sanity checks before finalizing

For each equation:

1. **Type-check.** All operands have compatible shapes (after broadcasting if used).
2. **Sign-check.** Loss is non-negative. Log is well-defined. Gradients flow where you say they do.
3. **Substitution-check.** Replace each symbol with a concrete shape (e.g. `$d=128, T=512$`) and trace through. Does the math still make sense?
4. **Unit-check.** If your method is in physical units, do they cancel correctly?
5. **Edge-case check.** What happens at `$T = 1$`? At `$N = 0$`? At `$\tau = 0$`?

If any check fails: rewrite the equation. Do not paper over with "see appendix."
