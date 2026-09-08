# Papers

Papers for this project. One directory per paper. Each is a self-contained paper-orchestra workspace, so
several can be in flight without colliding — the pipeline's own default is a
single top-level `workspace/`, which does not survive a second paper.

```
<project>/paper/<slug>/
├── inputs/          idea.md · experimental_log.md · template.tex ·
│                    conference_guidelines.md · experiments/<exp>/{results.json,code/,figures/}
├── outline.json     outline_reconciled.json · reconciliation_summary.md
├── figures/         the selected renders + captions.json
├── drafts/          intro_relwork.tex · paper.tex
├── final/           paper.tex · paper.pdf · refs.bib · figures/   ← the deliverable
├── render/          figure rendering and paper composition scripts
├── refs.bib         citation_pool.json · cross_verification_report.json
├── research_brief.md
└── provenance.json  input and output hashes
```

`final/` is flat and self-contained by design: `paper.tex` refers to
`figures/...` and `\bibliography{refs}` with no parent traversal, so it compiles
both here and in a sandboxed LaTeX editor.

## Conventions

- **Slug names the subject, not the venue.** Venues change; a resubmission
  should not need a new directory. The target venue lives in the paper's README
  and in `inputs/conference_guidelines.md`.
- **Figures are rendered from sealed results**, never drawn by a model. The
  figure-provenance gate strips anything it cannot trace to a real render, so
  `render/` scripts read `results/*.json` and retype no value.
- **`final/` is a build output.** Re-derive it by re-running the pipeline rather
  than hand-editing it; hand-edits belong in `drafts/` or the inputs.

## Index

| Paper | Target | Status |
| --- | --- | --- |
| [`solver-certificate-decomposition/`](solver-certificate-decomposition/) | ICLR 2027 | Body ends p9 at the template's own geometry; 16pp total. Nine review rounds; the round-9 audit's 52 findings are addressed bar one. `verify.py --all` 9/9. |


## Two rules the pipeline does not enforce

- **Scripts anchor on the paper directory**, never a fixed depth from the repo
  root — a paper that moves otherwise silently writes into the wrong tree.
- **Layout lives in `render/compose_paper.py`**, not in `drafts/paper.tex`. The
  composer rebuilds from `intro_relwork.tex`, so a hand-edited column switch or
  page trim is discarded on the next run.
