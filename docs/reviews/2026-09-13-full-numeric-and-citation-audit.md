# Full numeric and citation audit — 13 September 2026

**Commit audited:** `38ec7e9` "Rebuild the paper single-column against the
official ICLR 2027 style file"
**Scope:** every number in the manuscript re-derived from the sealed panels,
answer authorities and receipts; every citation resolved live against Crossref
and DataCite; build integrity and internal consistency.
**Result:** **eight factual errors, four citation errors.** All twelve fixed.

---

## Method

Numbers were recomputed from `data/*/public/panel.jsonl`,
`data/*/sealed/authority.jsonl` and `runs/**/receipts/prospective-*.jsonl`
wherever possible, and from `results/*.json` only where the receipts do not
carry the intermediate. Nothing was taken from `paper/inputs/experimental_log.md`,
which is pipeline-authored. DOIs were resolved over the network:
`api.crossref.org` for the six publisher DOIs, `api.datacite.org` for the thirty
arXiv DOIs.

## What passed

| Checked | Result |
| --- | --- |
| 60 cells of `tab:arms` (10 arms × 3 checkpoints × count, d′) | exact |
| 60 cells of `tab:models` (12 models × 5 arms) | exact |
| 20 cells of `tab:sdt` (hits, FA, d′, c) | exact |
| `fig:factorial`: 5 cells, 4 edges, interaction, diagonal, p | exact |
| `fig:replication`, `fig:order`, `fig:detection`: every plotted value | exact |
| `tab:stimulus`: the 9-line record and all 10 arm descriptions vs the panel | byte-exact |
| Decomposition: +61.5 / +1.0 / +60.4pp, 98.3%, BCa, p, d′ drop | exact |
| Census 38,424 = sum over 8 runs; 5,760 prospective; **exactly 2** ties | exact |
| Certifier: 23,240/23,240, 10,440 undecided, 9 adversarial, 192/192 | exact |
| The 45-vs-2 direction test, recomputed from receipts + geometry | 45, 2, p = 1.604e-11 |
| `broken_chain` vs `truncate_1` surface match, all 192 items | 0 divergences |
| b17 "byte-identical inputs, one instruction line changed" | exactly 1 line differs |
| 40 citations / 40 bib entries, 0 orphans, 0 duplicates | clean |
| 36 DOIs resolved live; titles, first authors, years | see C1–C4 |
| Build: 0 overfull, 0 undefined, 10/10 labels, floats in citation order | clean |

The **45-vs-2 direction test** is worth a note: it is in the paper but no
released analysis script computes it. It re-derives from the receipts and
`public/geometry.jsonl` exactly, so the reproducibility claim holds, but
`verify.py` does not cover it. Candidate for a twelfth claim.

## Factual errors found

**F1 · §5.3 attributed Qwen's class split to Gemma-3-4B.** "Gemma-3-4B's
standing prior is `No` — under `none` it answers `No` to all 192 items, at
c = 2.565 — and under `misleading` it answers `Yes` on 93 of the 96 contradicted
items." All three facts are Qwen2.5-3B 4-bit's: Gemma scores 22/96 under `none`
and is wrong on all 192 under `misleading`, so 96, not 93. Introduced by the
compression pass in `38ec7e9`; the prior text said "This model's", vague but not
false by name. **Fixed:** attributed to the 4-bit checkpoint.

**F2 · §5.3 "clearing three other arms."** Qwen3-32B clears the 0.50 floor on
**seven** arms (0.677, 0.708, 0.594, 0.625, 0.823, 0.958, 0.802) and fails on
three (`full` 0.167, `misleading` 0.000, `none` 0.104). Three is the failing
count, attributed to the clearing side. r12 item 1. **Fixed:** "clearing it on
seven of the other nine arms" — which is the stronger statement.

**F3 · Limitations "eight cells of `tab:arms` sit on it."** Five do: Gemma
`truncate_1`, Gemma `misleading`, and `full` on all three checkpoints. Nothing
else reaches ±5.13. **Fixed:** five.

**F4 · §4 "`Yes`/`No` for the first two, three-class for the others."** From the
receipts: b18 and b20 are binary too, so four of the seven are `Yes`/`No`.
**Fixed:** split by whether the panel carries an undecidable class.

**F5 · Intro and Conclusion "none abstains on a broken one."** Under the
abstention rescoring the 4-bit checkpoint abstains on 81/192 broken certificates
and bfloat16 on 34/192; only Gemma abstains 0 times. The abstract ("the
strongest") and §5.3 ("the most capable of the three") scoped it correctly, so
the manuscript contradicted itself. **Fixed:** both now match the abstract.

**F6 · d′ = −5.12 against −5.13 for the identical statistic.**
`analyse_binary_certificate_factorial_b20.py` used a Winitzki `erfinv`
approximation; every other analysis uses `statistics.NormalDist`. r12 item 3.
**Fixed** with a superseding v2 analysis — see the b20 design doc's decision log.
The audit and `verify.py` now both gate d′.

**F7 · Limitations "scored through a fourth backend."** Both the b19 and b20
manifests read `transformers+cuda`; only the GPU differs (A100 vs H100). The
Conclusion's "two inference stacks" is right. r12 item 2. **Fixed:** the clause
is gone; §4 already says the scale check ran on rented H100s.

**F8 · Intro "on frozen small models."** The third robustness check runs at
32.8B and 70.6B. **Fixed:** "on frozen checkpoints from 0.5B to 70.6B."

## Citation errors found

**C1 · `macmillan1991detection` publisher.** The 1991 first edition is Cambridge
University Press; Lawrence Erlbaum published the 2005 second edition (checked
against OpenLibrary). **Fixed.**

**C2 · `team2024olmo` year.** DataCite gives publicationYear 2025 for
`10.48550/arXiv.2501.00656`; the entry said 2024. **Fixed:** 2025.

**C3 · Qwen3-32B had no citation.** Named three times; the only Qwen citation
was the Qwen2.5 technical report, a different family. **Fixed:** added
`yang2025qwen3` (arXiv:2505.09388, verified via DataCite) and cited at first use.

**C4 · `team2024qwen` author order.** "Yang An" reverses An Yang. **Fixed.**

## Also changed

- "a 4.6× ratio on the Qwen checkpoints" → 4.6–4.7× (4-bit 4.63, bfloat16 4.70).
- Intro "every arm without a near-complete chain returns d′ = 0" was false of
  `broken_chain`, which shows eight of nine lines at d′ = 0.41 → "the unaided arm
  and every arm withholding two steps or more."
- Title keeps "Fourteen Models"; §1 now says "thirteen of which the analysis
  interprets", which is r12 item 4's second option.
- **r12 item 5** taken at its free option: the Candidate-tokenisation limitation
  now bounds the exposure on the checkpoints the diagnostic does not cover, from
  released receipts — the validity control sits at 6.9–11.3 logits median with
  under 1% of responses within 0.5 of indifference; the sweep reaches 25.7–40.4%
  on SmolLM2-1.7B, Llama-3.2-3B and Llama-3.1-8B.
- `paper/refs.bib` and `paper/final/refs.bib` had drifted in whitespace; now
  identical.
- `final/paper.aux`, `.bbl`, `.out` untracked. The committed `.aux` was stale
  enough to still carry `tab:edges`, `fig:size` and `sec:corruption`.
- `paper/README.md` named a different pair of failed prespecified criteria than
  the paper does; it now names all three and says which two the abstract counts.

## Page budget

The fixes and the new limitation cost about thirteen lines, which had to come
back out of a manuscript already at exactly nine pages. It came from duplication
only, measured by recompile: the "property of (model × arm × runtime)" sentence
(stated in four other places), the `misleading`-arm definition restated from
§3.2 in §5.3, the depth-cliff numbers restated from §5.1 in Limitations, the
share figures restated in the Conclusion, "the theory is visible in every arm"
for the third time, and the abstention clause in the Conclusion — which the
abstract carries and whose removal also resolves F5's awkwardness. Two figures
were also trimmed, and `fig:detection`'s panel subtitles, which repeated numbers
§5.3 states in prose, were removed.

## After

Main text ends on page 9, 12 pages total. 0 overfull, 0 undefined, 40/40
citations, floats numbered in citation order and none after the bibliography,
`verify.py --all` 11/11, b20 audit 33/33, `final/` compiles standalone.

---

## Addendum, 15 September — two reporting errors the audit missed

Both raised by the author after the audit shipped. Both real; both verified
against `b15_analysis_v1.json` and `b14_posthoc_2x2_reanalysis_v1.json`.

**A1 · The abstract reversed the headline finding.** It read *"The share of the
state effect that survives destroying validity is 98.3%"*. The decomposition is
total state +61.5pp = surface +1.0pp + validity +60.4pp, and the validity share
is validity/total = 98.3%. That is the share **destroyed** when validity breaks.
What survives is the surface component, 1.0 of 61.5pp = **1.7%**. The
introduction (*"Breaking validity alone removes 98.3%"*), `tab:arms`' caption
and §5.1 all had it right; only the abstract was reversed, and it had been since
at least 11 Sept. **Fixed:** the abstract now matches the introduction.

**Why the audit missed it.** Every check I ran compared a printed number against
a recomputed number. 98.3% agreed with the data, so it passed. Nothing in the
method tested whether the *sentence carrying* a correct number asserted the
right direction. A value can be right and its claim inverted, and no
number-matching gate sees it. That is a hole in the audit procedure, not a
one-off slip.

**A2 · §5.1 put the wrong arm below the always-`No` baseline.** It read
*"`irrelevant` returns an identical 9/96 'Yes' rate in both classes at d' = 0.00,
below a trivial always-`No` strategy's 96/192"*. `irrelevant` scores **96/192 —
exactly the baseline**, not below it. The arm that falls below is `none`, at
91/192 and d' = -0.25. **Introduced by this audit's own page-budget pass**: the
clause used to follow *"The model answers `No` to 88% of items"*, which is the
`none` arm, and cutting that clause for space left "below" attached to
`irrelevant`. **Fixed:** `irrelevant` is now said to match the baseline exactly,
with `none` named as the arm below it — which is the stronger statement anyway,
an arm that equals the do-nothing strategy while discriminating nothing.

**Lesson for the roster.** A cut that removes a clause can change the subject of
the clause that follows it. Compression passes need a re-read of every sentence
adjacent to a deletion, not just a recompile and a page count.

---

## Second addendum, 15 September — the directional sweep

After A1 and A2, the whole class was swept properly: every directional,
comparative, superlative and quantifier claim in the manuscript that carries a
number — **68 sentences** — checked against the sealed data, not for whether the
number matches but for whether the assertion attached to it points the right
way. Three more failed, plus two lesser ones.

**A3 · §5.1 "a change in discrimination, not in criterion."** The criterion does
not hold still: it rises from **+1.14 to +2.36** between `truncate_1` and
`broken_chain`. Both statistics moved. What is true, and is the stronger
argument, is that **the false-alarm rate is 0 in both arms**, so the whole
collapse is in the hit rate, 59/96 to 1/96 — which a bias shift cannot produce,
because it would move both. **Fixed** to say that.

**A4 · §5.2 "it breaks three of ten models here."** The sentence equivocates on
"breaks". Its first half defines it as falling below the 0.50 floor
(Qwen2.5-7B, 0.938 → 0.141), and under that meaning proof state breaks **one**
of ten. Three is the count under the weaker meaning "lowers minimum per-class
recall" — and two of those three (Gemma 1.00 → 0.89, Qwen2.5-3B 0.91 → 0.72)
still clear the floor. **Fixed:** both facts stated, neither conflated.

**A5 · §1 "every arm withholding two steps or more return d′ = 0."**
`broken_chain` withholds the true steps 6 and 7 and returns d′ = 0.41.
Counterexample. **This predicate was introduced by the 13 Sept audit**, replacing
"every arm without a near-complete chain" — one loose predicate swapped for
another without checking the replacement against the arm table.

The exact predicate was available the whole time. On both Qwen checkpoints the
set of arms at d′ = 0 is *identical* to the set whose record never displays the
query's predicate: `none`, `irrelevant`, `same_entity_irrelevant`, `truncate_2`,
`truncate_3`. The Limitations already said so in passing. **Fixed** to the exact
predicate, which is both true and sharper.

**A6 · `tab:stimulus` caption "every surface cue of `truncate_1` survives."**
An unhedged universal. The four properties §3.2 enumerates hold on all 192
items, but character length is not among them and differs by up to 13 characters,
identical on only 17 of 192. The abstract hedges correctly ("every surface
property we could enumerate and audit"); the caption did not. **Fixed:** "every
audited surface cue".

**A7 · `paper/figures/captions.json`** claimed token length was held fixed, for
the `arm_decomposition` figure the paper does not include. Not a manuscript
error; a false claim in a repo file. **Fixed.**

### The replacement claims, verified

| Claim | Check |
|---|---|
| neither arm produces a false alarm | `truncate_1` 0, `broken_chain` 0 |
| the hit rate falls 59/96 → 1/96 | exact |
| proof state lowers recall on three of ten, takes one below the floor | 3 and 1 |
| {d′ = 0 on both Qwen} ≡ {never displays the query predicate} | sets identical |
| every audited surface cue survives | 0 divergences over 192 |

### What the other 63 confirmed

Among them, the ones most exposed to inversion: `irrelevant` = 96/192 equals the
always-`No` baseline while `none` = 91/192 falls below it; abstention falls 37.5
and 32.8 against `none` and `irrelevant` and rises 31.2 against `truncate_1`;
"the strongest" is Gemma, the only one of the three with non-zero unaided
competence; nothing below 3B clears the floor in **any** of the five arms (best
is SmolLM2 at 0.375); "on identical weights" holds — same repo, revision and
aggregate SHA-256 across mlx and CUDA; 70.6/4.3 = 16.4, so "sixteen times";
all four edges at p < 10⁻⁴; every rule displayed is a real theory rule on all
192 items.
