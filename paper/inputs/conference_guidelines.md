# ICLR 2027 — submission guidelines

> **Provenance.** Everything below the Format section was written by this
> pipeline before the venue published anything. The Length, Format, Abstract and
> Sections entries were checked against the official author guidelines and style
> files on 12 September 2026:
> `https://iclr.cc/Conferences/2027/AuthorGuidelines` and
> `iclr-2027-style-files.zip`, vendored in `paper/inputs/iclr2027/`. The Format
> entry said "two-column" for a week and was wrong; the paper was built that way
> until the style file was read. Check a claim here against the style file before
> trusting it.

## Dates
Abstract 18 September 2026 (AOE) · Full paper 25 September 2026 (AOE)

## Length
**9 pages** of main text maximum at submission, 10 for rebuttal and camera-ready.
Citations are unlimited and do not count. The Reproducibility Statement, the
AI-Use Statement and an Ethics Statement are each explicitly excluded from the
limit, and each should stay under a page. Figures and tables count.

## Format
**Single column.** `\documentclass{article}` plus `\usepackage{iclr2027_conference}`,
which sets the whole geometry itself: text 5.5in wide by 9in tall, 10pt on 11pt
leading, 0.5in odd/even side margin, no paragraph indent and a half-line
`\parskip`. It also supplies `\maketitle`, the abstract environment, the
small-caps section headings and the reviewer line-number rulers in the margins.
Bibliography style `iclr2027_conference.bst`, citations through `natbib`
(`\citet` in-sentence, `\citep` otherwise). Times is the preferred typeface.

Do not restate any of the style file's settings in the preamble and do not edit
the style file --- "tweaking the style files may be grounds for rejection". The
abstract **must be a single paragraph**. Place one line space before a figure
caption and after the figure, and around a table title.

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
