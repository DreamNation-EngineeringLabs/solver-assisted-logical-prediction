# ICLR 2027 — submission guidelines

## Dates
Abstract 18 September 2026 (AOE) · Full paper 25 September 2026 (AOE)

## Length
**9 pages** of main text maximum. References, acknowledgements and appendices are
unlimited and do not count toward the limit. Figures and tables count.

## Format
Two-column ICLR style via `iclr2027_conference.sty`. 10pt. Do not alter margins,
font sizes or line spacing.

## Anonymity
**Double-blind.** No author names, affiliations, emails, funding sources or
acknowledgements in the submission. Do not include links that reveal identity —
use anonymised URLs for code and data. Self-citation in the third person only
("Prior work by X et al." not "our previous work").

## Mandatory sections
- Abstract
- Introduction
- Related Work
- Method
- Experiments
- **Limitations** — a dedicated section is expected
- Conclusion
- Reproducibility Statement
- **AI-Use Statement** — required for ICLR 2027; declare any use of LLMs in
  research or writing

## Reproducibility
A reproducibility statement is expected, describing data, code availability and
the steps needed to reproduce the reported numbers.

## Style requirements specific to this submission
- Report **d' and criterion alongside accuracy** wherever accuracy appears.
- Label every **post hoc** analysis as such at the point it is used, not only in
  a footnote.
- State **system-level** effects as system-level; never upgrade them to claims
  about the model's own reasoning.
- Every numeric claim must trace to `experimental_log.md`.
- Every figure must be a real render from `inputs/experiments/<slug>/figures/`.
