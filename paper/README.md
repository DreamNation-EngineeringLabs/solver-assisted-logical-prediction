# What a Language Model Does with a Solver Certificate

Decomposing what a language model does with a solver certificate.
**Target: ICLR 2027** (abstract 18 Sept 2026, paper 25 Sept 2026).

Deliverable: [`final/paper.pdf`](final/paper.pdf) — 10 pages: 8 of main text at
the venue's own geometry (cap is 9), references from p9, **no appendix**. 39
verified citations, 4 figures, 5 tables, every one of them in the main text.

Written to be read, not queried. The body is 3,466 words, down from 5,749: the
prose states the findings and the floats carry the detail, instead of narrating
every result and then tabulating it again. Six subsections in the whole paper,
down from 21. Results is three sections ordered as an argument — the instrument
works / almost nothing it returns transfers / what does not vary — and the 2×2
that is the contribution is a pull figure on page 1.

## Findings

| | |
| --- | --- |
| **The method is the contribution; what it returns is not** | Breaking validity alone removes **98.3%** of the state effect on one checkpoint and **40.4–51.4%** on another. We decline to generalise the value, ours included |
| No resistance to a corrupted apparatus | Given a fabricated final rule pointing the wrong way, all three checkpoints answer incorrectly on **189, 186 and 192 of 192**. This holds on every checkpoint |
| Reversing a rule and its premise costs accuracy | Holds on every checkpoint. Distance between them does not matter; direction does |
| Depth is one step — on the Qwen checkpoints | `truncate_2` scores identically to no certificate there, but 4/96 against 22/96 unaided on Gemma-3-4B. Checkpoint-specific |
| Abstention does not settle detection | The delta changes sign with the reference arm: it falls against `none`/`irrelevant`, rises against the surface-matched `truncate_1`. We draw no conclusion from it |
| Viability is a property of (model × arm × runtime) | Not of a model, and not a size floor: Llama-3.1-8B is degenerate in all five arms, and one model's verdict flips with the inference stack alone |
| Two prespecified criteria of our own failed | A single-class recall floor gamed by label collapse, and a 15pp target an arm at 91.7% could not reach |

## Sources

Experiments live in the `solver-assisted-logical-prediction` submodule. Every
number in the paper traces to `results/*.json` there, and the claim-evidence gate
confirms it. Figures are rendered from those same files by `render/`.

## Rebuilding

```bash
uv run python solver-assisted-logical-prediction/paper/render/render_figures.py
uv run python solver-assisted-logical-prediction/paper/render/compose_paper.py
cd solver-assisted-logical-prediction/paper/final && tectonic -X compile paper.tex --outdir .
```

## Layout

```
inputs/     idea.md · experimental_log.md · template.tex · conference_guidelines.md
drafts/     intro_relwork.tex · paper.tex      ← hand edits go here, not in final/
render/     compose_paper.py · render_figures.py
figures/    the selected renders + captions.json
final/      paper.tex · paper.pdf · refs.bib · figures/   ← the deliverable
```

`final/` is flat and self-contained: `paper.tex` refers to `figures/...` and
`\bibliography{refs}` with no parent traversal, so it compiles here and in a
sandboxed LaTeX editor. It is a **build output** — re-derive it with `render/`
rather than hand-editing, and put layout changes in `compose_paper.py`, which
rebuilds `drafts/paper.tex` from `intro_relwork.tex` on every run.

## Open

Nine rounds of review are done, plus a six-reviewer audit whose 52 findings are
all addressed, and a readability rewrite against Karpathy's paper-writing notes.
Nothing is in an appendix any more.

Three floats were dropped as strict duplicates of another: `fig:arms` (ten arms
on one checkpoint — `tab:arms` has all three), `fig:size` (ten models —
`tab:models` has twelve, with verdicts) and `tab:detection` (three deltas —
`fig:detection` carries the distribution). `render_figures.py` still builds them.

Two things outside the paper: the sealed-authority release decision, which is
irreversible once public, and `iclr2027_conference.sty`, which is unpublished and
will reflow every page when it lands.

At exactly 9 pages of body, anything added needs something removed.
