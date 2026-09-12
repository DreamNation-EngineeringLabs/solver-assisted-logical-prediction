# What a Language Model Does with a Solver Certificate

Decomposing what a language model does with a solver certificate.
**Target: ICLR 2027** (abstract 18 Sept 2026, paper 25 Sept 2026).

Deliverable: [`final/paper.pdf`](final/paper.pdf) — 12 pages: **9 of main text**,
which is the cap exactly, then the Reproducibility and AI-Use statements and the
references, none of which count. Built against the official
`iclr2027_conference.sty` (vendored in `inputs/iclr2027/`): **single column**,
5.5in by 9in, 10pt on 11pt, reviewer rulers in the margins. 39 verified
citations, 4 figures, 5 tables, **no appendix** — every float is in the main
text.

**b20, the scale check** (11 Sept 2026) takes the corruption result past the
small-model reading: Llama-3.3-70B answers `full` 192/192 and solves 145/192
with no certificate at all, and is wrong on **all 192** misleading items at
d' = -5.12. Design doc:
[`docs/cognitive-core/binary_certificate_factorial_b20.md`](../docs/cognitive-core/binary_certificate_factorial_b20.md).

Two tables exist to answer a first-time reader's questions before the argument
starts. **Table 1** shows a real sealed item verbatim: the theory, the query, the
`full` derivation numbered line by line, and what each of the ten arms does to
it — so `truncate_1`, the word-matching test and the corrupted arm are visible
rather than described. `verify.py stimulus` checks those printed lines against
the sealed panel. **Table 2** names the four experiments and the two robustness
checks and says in one line what each does.

Written to be read, not queried. The body is ~3,100 words, down from 5,749: the
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
cd solver-assisted-logical-prediction
uv run python paper/render/render_figures.py     # renders, then publishes into figures/ and final/figures/
uv run python paper/render/compose_paper.py      # writes drafts/paper.tex
cp paper/drafts/paper.tex paper/final/paper.tex
cd paper/final && tectonic -X compile paper.tex --outdir .
```

`render_figures.py` now does the copying itself and asserts that the four figures
marked included in its `SELECTED` map are exactly the four the manuscript
`\includegraphics`. Figures are sized to their print width, so nothing is
rescaled at `\includegraphics` time.

## Layout

```
inputs/     idea.md · experimental_log.md · template.tex · conference_guidelines.md
inputs/iclr2027/   the venue's own .sty and .bst, unmodified, with PROVENANCE.md
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

A fourth was dropped in the single-column rebuild: `tab:edges`, whose five
effects are the arrow labels of `fig:factorial`. Its two unique columns — the
exact McNemar p per edge, and which contrasts the original paper reported —
moved into the sentence in §5.1 that used to cite it.

One thing outside the paper: the sealed-authority release decision, which is
irreversible once public and is now due at submission rather than camera-ready.

At exactly 9 pages of main text, anything added needs something removed. The
deficit is measured by recompiling, never estimated: `pdftotext -layout` on the
built PDF, then check which page the Reproducibility Statement starts on. It
must be page 10, with nothing above it.
