# Pre-conversion snapshot — 12 September 2026

The manuscript as it stood immediately before the two-column → single-column
rebuild against the official `iclr2027_conference.sty`, kept so the old PDF can
be opened without a checkout.

| File | What it is |
| --- | --- |
| `paper.pdf` | 11 pages, two columns, body ending p9. Built to `paper/inputs/conference_guidelines.md`, which said "two-column ICLR style" and was pipeline-authored fiction |
| `paper.tex` | the generated manuscript for that PDF |
| `compose_paper.py`, `render_figures.py` | the composer and figure renderer that produced it |
| `intro_relwork.tex` | the preamble and first two sections, `\documentclass[10pt]{article}` + `geometry` |
| `conference_guidelines.md` | the wrong guidelines file, kept as the evidence |

Git history is the real record — this directory is a convenience, not a
dependency. Nothing in the build reads it. Delete it once the submission is in.

The rebuild is described in `PAPER-CRAFT.md`, "The one under it: conforming to a
guidelines file nobody at the venue wrote".
