<!-- auto-research lint_report v1 {"counts": {"citations": {"BIB-MISSING": 1, "IRRELEVANT": 1, "SUPPORTS": 1}, "numbers": {"UNTRACED": 3, "VERIFIED": 1}}, "exit_code": 1, "generated_at": "2026-05-09T00:00:00Z", "linters_run": ["check_citations.py (judge=mock)", "trace_numbers.py"], "paper": "/home/winbeau/wenbiao_zhao/auto-research/auto-research-writing/assets/scripts/tests/fixtures/dirty_run/stage4_writing/paper.tex", "schema": "auto-research lint_report v1"} -->

# Lint Report — /home/winbeau/wenbiao_zhao/auto-research/auto-research-writing/assets/scripts/tests/fixtures/dirty_run/stage4_writing/paper.tex

## citation-bib-missing
- **paper.tex:L10:C53** — \cite{ghost2099} resolves to no entry in references.bib
  - context: `and report \textbf{73.4\%} on accuracy and \textbf{0.054} ECE. The earlier KL-regularised optimisation of \cite{kingma2014adam} gave us the right inductive bias for our reweighter. We also achieved 99.9\% on a private benchmark, surpassing the \textbf{42.7} score reported elsewhere. Section~3.1 explains. See [CITE] for the backbone. \end{document}`
  - key: ghost2099

## citation-relevance
- **paper.tex:L7:C4** — \cite{kingma2014adam} judged IRRELEVANT (conf=0.84)
  - context: `\documentclass{article} \begin{document} \section{Introduction} We extend reweighted scaling \cite{snell2024scaling} and report \textbf{73.4\%} on accuracy and \textbf{0.054} ECE. The earlier KL-regularised optimisation of [CITE] gave us the right inductive bias for our reweighter. We also achieved 99.9\% on a private benchmark, surpassing the \textbf{42.7} score reported elsewhere. Section~3.1 explains. See \cite{ghost2099} for the backbone. \end{document}`
  - judge: mock
  - key: kingma2014adam
  - paper_title: Adam: A Method for Stochastic Optimization
  - reason: context discusses reweighting; Adam abstract covers a different topic

## number-provenance
- **paper.tex:L5:C65** — UNTRACED numeric literal `\textbf{73.4\%}` (value=73.4)
  - context: `xtend reweighted scaling \cite{snell2024scaling} and report \textbf{73.4\%} on accuracy and \textbf{0.054} ECE. The earlier KL-regulari`
  - checked: claims_ledger,results_summary,results.csv,cited-abstract
  - kind: bold_pct
  - nearest_cite_keys: (none)
- **paper.tex:L9:C18** — UNTRACED numeric literal `99.9\%` (value=99.9)
  - context: `right inductive bias for our reweighter.  We also achieved 99.9\% on a private benchmark, surpassing the \textbf{42.7} score`
  - checked: claims_ledger,results_summary,results.csv,cited-abstract
  - kind: pct
  - nearest_cite_keys: (none)
- **paper.tex:L9:C64** — UNTRACED numeric literal `\textbf{42.7}` (value=42.7)
  - context: `also achieved 99.9\% on a private benchmark, surpassing the \textbf{42.7} score reported elsewhere. Section~3.1 explains. See \cite{g`
  - checked: claims_ledger,results_summary,results.csv,cited-abstract
  - kind: bold
  - nearest_cite_keys: (none)
