# What a Language Model Does with a Solver Certificate

Decomposing what a language model does with a solver certificate.
**Target: ICLR 2027** (abstract 18 Sept 2026, paper 25 Sept 2026).

Deliverable: [`final/paper.pdf`](final/paper.pdf) — 16 pages: 9 of main text at
the venue's own geometry, references from p10, appendix from p12. 39 verified
citations, 6 figures, 6 tables.

## Findings

| | |
| --- | --- |
| The state effect is inference, not text matching | validity component +60.4pp vs surface +1.0pp — a **98.3% validity share** |
| Entity repetition explains nothing | +0.0pp (*p* = 1) with 4 mentions vs 0 |
| Inference depth is exactly one step | withholding two steps scores identically to supplying nothing |
| No resistance to a corrupted apparatus | the model follows a wrong-pointing certificate on **189 of 192** items, d′ = −4.36 |
| Minimum viable interface size ≈ 3B | 3 of 10 models viable; not monotonic in scale |

## Sources

Experiments live in the `solver-assisted-logical-prediction` submodule. Every
number in the paper traces to `results/*.json` there, and the claim-evidence gate
confirms it. Figures are rendered from those same files by `render/`.

## Rebuilding

```bash
uv run python solver-assisted-logical-prediction/paper/solver-certificate-decomposition/render/render_figures.py
uv run python solver-assisted-logical-prediction/paper/solver-certificate-decomposition/render/compose_paper.py
cd solver-assisted-logical-prediction/paper/solver-certificate-decomposition/final && tectonic -X compile paper.tex --outdir .
```

## Open

Human review has not happened. Specifically worth a read: whether the title
overreaches, whether §6.1 states depth-exactly-one plainly enough as a bound,
whether the two post-hoc labels (§5.1, §5.4) read as disclosure rather than
excuse, and whether §5.3 gives the corruption result the weight it deserves.

At exactly 9 pages, anything added needs something removed.
