# Peer review, round 2 — "What a Language Model Does with a Solver Certificate"

- **Manuscript:** `paper/solver-certificate-decomposition/final/paper.pdf` (15 pp incl. appendix), retitled
  from "Reading Is Not Reasoning…"
- **Reviewer method:** `cognitive-core/.claude/skills/peer-review`, with every number re-derived from
  `results/*.json` and the raw receipts in `runs/cognitive_core/`.
- **Prior review:** `docs/reviews/2026-09-04-solver-certificate-decomposition-peer-review.md`
- **Recommendation:** **Minor revision** (borderline accept → accept). ~6.5/10, confidence 4/5.
  The science is now good and unusually honest. What blocks it is an editorial-integrity problem:
  roughly a third of the prose is stale v1 text that contradicts the new results, and the headline
  prompt count is wrong.

---

## 1. Response to round 1

All seven majors were addressed, and four of them with **new experiments that refuted the authors'
own claims**. Specifically:

| R1 major | Response | Verdict |
|---|---|---|
| 1. Exp-3 arms withheld | `b16_analysis_v2_allarms.json`; Table 5 now reports all five arms × ten models; new §5.6 retracts the size-floor claim and reframes viability as (model × arm), with Qwen2.5-7B as the worked case; new §5.7 computes the ten-model 2×2 | **Fully addressed, and then some** |
| 2. n = 1 checkpoint | `b15_replication_v1.json`: b15's ten arms re-run on Qwen2.5-3B bf16 and Gemma-3-4B; new §5.3 | **Addressed** (see New-2, New-3) |
| 3. Interaction / ceiling | §5.1 now reports −29.2pp and the 13.0pp headroom, and explicitly withdraws the "30% retained" redundancy reading | **Fully addressed** |
| 4. "Detects a broken chain" | New Experiment 4 (b17): three-candidate rescoring of the same items. Abstention *falls* 75.0% → 42.2%; `No` is 110/192 in both arms. §5.5 states "Detection is refuted, not merely unsupported" | **Fully addressed** (see New-4) |
| 5. Share interval / Holm | `b15_share_interval_v2.json` bootstraps the whole ratio: 98.3% BCa [94.4, 100.0]. Holm values now printed in §5.2. The file even records that v1's version string overclaimed Holm | **Fully addressed** |
| 6. Certifier validation | §3.3 now states the tautology limit in its own words, adds nine adversarial theories and a differential test against an independently written reference (ground instantiation + naive fixpoint) agreeing 192/192 on the generated panels, and claims implementation-error coverage only | **Fully addressed** |
| 7. Undisclosed prior report | §6.3 now discloses it anonymously and reconciles the conflicting unknown-gate verdict | **Fully addressed** |

I re-verified the new numbers independently. Everything checks: the ten-model means
(+8.7 / +21.6 / −15.9pp), 8-of-10 and 6-of-10 counts, the three degrading models, Gemma's
58/96 and 40.4% share, the bf16 98.6%, the b17 distribution, and the nine adversarial cases.
Bibliography is still clean (39/39 cited, no dangles). Running an experiment that kills your own
headline mechanism claim, and then leading the abstract with it, is the right behaviour and is
rarer than it should be.

Two round-1 concerns I can now retire on the evidence:

- **Near-tie artefacts.** I worried the b14 `top_two_margin` minima of 0.0 meant thin decisions.
  Checked in the b15 receipts: Gemma's `broken_chain` margins are a median 3.56 logits (4.13 on
  the items it gets right), Qwen's are 7.9. The 58/96 is not a coin flip. Tie-breaking is still
  undocumented (Minor 6) but is cosmetic.
- **Phi-4-mini / Qwen2.5-3B identical row.** Resolved by reporting all five arms — they now
  differ visibly (96.4 vs 68.2 on `conclusion_only`).

---

## 2. New major comments

### New-1 (blocking) — The Introduction, §2.2, §4 and the Reproducibility Statement are stale v1 text that contradicts the abstract and Results

The abstract has been rewritten honestly. The front matter has not been touched. A reviewer
reading front-to-back meets the retracted version of every claim before reaching the retraction:

| Stale text | Contradicted by |
|---|---|
| §1: "Three sealed experiments on frozen small models" | Abstract: "four sealed experiments" |
| §1: "so $98.3\%$ of the state effect is inference over the supplied lines rather than text matching" — unqualified | §5.3: 40.4% on Gemma; abstract: "how much … is genuine inference is *model-specific*" |
| §1: "And the tracking confers no robustness" | §5.5: there is no tracking to confer anything |
| §1 contribution (iv): "evidence that validity tracking is real, shallow, and offers no protection" | §5.5: "Detection is refuted, not merely unsupported" |
| §1 contribution (v): "a substrate-size floor from a ten-model sweep" | §5.6: "that is not a floor for serving as an interface" |
| §1: "the largest model tested collapses while a 3B model does not" | §5.6: Qwen2.5-7B is viable under `conclusion_only` (min recall 0.938) |
| §1: "Every arm without a near-complete supplied chain returns $d' = 0$, so the models studied do not reason unaided" | Gemma on b15: `none` = 22/96 entailed, $d' = 1.83$; `irrelevant` $d' = 0.62$; `broken_chain` $d' = 2.83$ |
| §2.2: "The state channel carries real validity information; it supplies no protection against a corrupted apparatus" | §5.5 (first clause is the refuted claim) |
| §4.1: "All three experiments…"; "The three sealed panels…"; scoring described for Experiments 1–3 only | Experiment 4 exists, is three-candidate, and is never described in Setup |
| §4.3: "In total $12{,}480$ prompts were scored" | Abstract: 18,816 |
| Reproducibility Statement: "all $12{,}480$ per-response receipts" (×2) | ditto; also omits the b15-replication, b17 and adversarial/differential artifacts |
| `tab:panels` caption + rows: "The three sealed panels…", no b17 row | b17 exists (it rescores b15's items, which is worth a row or a note) |
| §5.4: "the model demonstrably tracks whether a supplied derivation connects… Validity tracking is not verification" | §5.5, the immediately following subsection, refutes it |
| §6.1: "Breaking a certificate is diagnostic only because the model scores $0/96$ working from the theory alone" | True of Qwen; false of Gemma (22/96) |

§5.4 and §5.5 are the worst of these because they are adjacent: one asserts tracking, the next
refutes it, with no acknowledgement. Either fold §5.4 into §5.5 or rewrite §5.4's closing
paragraph so the corruption result stands on its own ("the architecture has no defence against a
wrong apparatus") without the tracking premise.

**Required:** one full pass over §1, §2.2, §4, §5.4, §6.1, the Reproducibility Statement and the
table captions, reconciling every claim against §5.3–§5.7. This is not a polish request — as it
stands the paper asserts and denies the same four propositions.

### New-2 (blocking) — The prompt and run counts in the abstract do not reconcile with the released receipts

The abstract claims "twelve model-runs and $18{,}816$ scored prompts, all re-derivable from
released receipts". Counting the released receipts:

```
b14  (results/b14_raw_model_calls_960.jsonl)                      960
b15  3 runs × 1,992 (10 prospective arms + 2 qualification arms) 5,976
b16  10 models × 960 (5 arms × 192)                              9,600
b17  3 arms × 192                                                  576
                                                        TOTAL  17,112
```

17,112, not 18,816 — a 1,704-prompt discrepancy. And the run count is 15 (1 + 3 + 10 + 1), or 14
distinct (checkpoint × panel) pairs; "twelve" is the *old* accounting (b14 + b15 + ten b16
models) carried forward unchanged. Meanwhile §4.3 and the Reproducibility Statement still say
12,480, which is the pre-revision total.

For a paper whose central methodological claim is that every number is re-derivable from sealed
receipts, an unreconcilable headline count is the single most damaging error available. Fix the
number, state the arithmetic somewhere a reader can check it (the table above, or a line in §4.3),
and say whether the 72 qualification-arm prompts per b15 run are inside or outside the total.

### New-3 — The detection refutation is single-checkpoint, but is stated as holding on every checkpoint

b17 exists only for `qwen2p5_3b_4bit` (one receipts directory, three arms). Yet:

- Abstract: "A three-candidate test refutes the reading that the model detects invalidity at all."
- Conclusion: "**Two findings do hold on every checkpoint.** The inference is one step deep, and
  it is not detection…"

The second sentence is not supported: detection was tested on one of three checkpoints. This is
the same error §5.3 exists to warn against, committed two pages later.

It also matters *which* checkpoint was left out. Qwen answers `broken_chain` correctly on 1/96 —
there is barely anything for a detection test to explain. Gemma answers it on **58/96**. The
detection question is at its most interesting exactly where the test was not run, and the two
predictions diverge sharply there: if Gemma's broken-chain successes are surface matching it
should answer `Yes`/`No` on the three-candidate panel; if it is doing certificate-cued inference
over the visible theory it should show a different pattern again.

**Required:** either run b17 on Gemma-3-4B and Qwen bf16 (576 prompts each — trivial), or scope
every detection statement to the one checkpoint and delete "on every checkpoint" from the
Conclusion.

### New-4 — Gemma's 40.4% share is confounded with unaided competence; re-baselined it is 51.4%

The decomposition baselines both components on `irrelevant`. For Qwen that is immaterial —
`none` and `irrelevant` are both 0/96. For Gemma it is not:

| Gemma-3-4B, b15, entailed /96 | |
|---|---|
| `none` (no record at all) | **22** |
| `irrelevant` | 2 |
| `broken_chain` | 58 |
| `truncate_1` | 96 |

Computed from the receipts, the per-item overlap is decisive: of the 22 items Gemma answers
correctly with **no certificate**, **20 are also correct under `broken_chain`** (2 `none`-only,
38 `broken_chain`-only). So roughly 22pp of the +58.3pp labelled "surface component" is
pre-existing unaided competence, not exploitation of the broken certificate's surface form.

Re-baselining on `none` rather than `irrelevant`:

```
total    = (96 − 22)/96 = +77.1pp
surface  = (58 − 22)/96 = +37.5pp
validity = (96 − 58)/96 = +39.6pp
share    = 39.6 / 77.1  =  51.4%
```

51.4%, not 40.4%. That changes the paper's sentence "on the strongest substrate in our sweep,
**most** of the effect is surface overlap" — on the `none` baseline it is a near-even split with
validity ahead. The 98.3% vs 40.4% contrast that carries §5.3, the abstract and the conclusion is
partly an artefact of baseline choice on a model with non-zero unaided competence.

This is also the point at which §6.1's "pointer back into the theory" caveat stops being
hypothetical. Gemma reasons unaided on 22/96, so for Gemma a broken certificate naming the query
predicate in a real rule plausibly acts as a retrieval cue into the visible theory — inference of
a different kind, not surface matching. The paper's own caveat now has a concrete instance and
should be promoted from a caveat to an analysis.

**Required:** report Gemma's `none` arm in §5.3 and `tab:replication`; report the share on both
baselines, or justify `irrelevant` as the baseline given non-zero `none`; and use the `none`/
`broken_chain` per-item overlap (already in the receipts) to say whether Gemma's behaviour is
surface matching or certificate-cued theory inference. Right now "surface exploitation" is a
label, not a finding.

### New-5 — §5.3 reports two of the replication's results and omits two that qualify claims made elsewhere

`b15_replication_v1.json` holds all ten arms for all three checkpoints. §5.3 reports
`broken_chain`, the share, and `misleading`. Two further claims made elsewhere in the paper do
not survive the replication and are not mentioned:

- **"Order matters" does not replicate.** §5.2: `truncate_1 − shuffled` = +46.9pp, "so the model
  is not reading a bag of statements." Gemma: 96 vs **86** = +10.4pp. Gemma very nearly *is*
  reading a bag of statements ($d'$ 5.13 vs 3.80), and the paper's order conclusion is
  Qwen-specific.
- **"$d' = 0$ without a near-complete chain" does not replicate** (see New-1): Gemma's `none`,
  `irrelevant` and `same_entity_irrelevant` give $d'$ of 1.83, 0.62 and 0.77.

What *does* replicate and is worth saying so: entity repetition contributes nothing (Gemma 3 vs
2), the depth cliff holds (`truncate_2`/`truncate_3` = 4/96 against `truncate_1` = 96/96), and
`misleading` is catastrophic everywhere.

Given that §5.3's own thesis is "the method generalises, the value does not", the natural artifact
is the full 10-arm × 3-checkpoint grid — already computed, one table. As written the paper
declines to generalise the one number it re-ran while continuing to generalise two claims the
same re-run contradicts.

### New-6 — §5.7's ten-model mean averages over four degenerate responders, and the "less than half" claim does not survive excluding them

§5.7's rhetorical payload is: "Experiment 1's state main effect of $+22.4$pp is not typical: the
ten-model mean is less than half of it." The mean is +8.7pp, which I reproduce exactly. But four
of the ten models — Qwen2.5-0.5B, OLMo-2-1B, Llama-3.2-1B, Qwen2.5-1.5B — have **minimum
per-class recall of 0.000 in every one of the five arms**. They are single-label responders, and
three of them return *negative* state main effects (−9.1, −4.9, −2.3pp). Differencing balanced
accuracy across arms for a responder that emits one label is not measuring a channel
contribution; it is measuring noise in a degenerate distribution. This is precisely the inference
§3.4 and §5.1 exist to forbid.

Excluding the four collapsed models, over the six that discriminate at all:

```
mean state main effect  = (14.8 + 12.8 + 27.3 + 14.6 + 3.6 + 15.1)/6 = +14.7pp
mean answer main effect = (30.5 + 24.7 + 23.7 + 37.0 + 34.4 + 20.8)/6 = +28.5pp
```

+14.7pp against Experiment 1's +22.4pp is **not** "less than half". The qualitative point — the
answer channel dominates, and a single-model state estimate is not characteristic — survives and
is if anything cleaner (28.5 vs 14.7 is a ~2:1 ratio on the non-degenerate set). The quantitative
framing does not.

**Required:** report both means, flag the four collapsed models as excluded from the second, and
restate the comparison in terms the non-degenerate set supports.

### New-7 — Primary results have been moved to the appendix

`tab:panels`, `tab:sdt`, `tab:replication`, `fig:replication`, `fig:detection`, `fig:arms` and
`fig:size` are all in Appendix A. That means §5.3 — the section carrying the paper's central
"it does not generalise" claim — has neither its table nor its figure in the body, and §4.1's
dataset table is three pages away from §4.1. `tab:sdt` is the evidence for §5.1's
degenerate-responder finding, which the paper calls one of its two measurement lessons.

If this is a page-limit squeeze, say so and cut prose instead: §2 is four subsections of related
work and could lose a third of its length without losing a citation. `tab:replication`,
`tab:sdt` and `fig:detection` carry primary results and belong in the body.

---

## 3. Minor comments

1. **§5.4 unit mixing persists** (R1 minor 1). "The model scores $3$ of $192$, with $d' = -4.363$:
   $\textsc{misleading} - \textsc{full} = -100.0$pp" still mixes an all-items count with an
   entailed-subset contrast. On all 192 items it is −98.4pp.
2. **§5.4 still omits its strongest evidence** (R1 minor 2). The class split is the argument: under
   `misleading` the model emits `Yes` on 93 of 96 *contradicted* items (response distribution
   `Yes` 0.484 with `entailed_correct` = 0), overriding an otherwise near-total `No` prior because
   the certificate told it to. One sentence, much more convincing than "3 of 192".
3. **Figure 1 caption/figure mismatch persists** (R1 minor 3). The caption says "with the
   no-material baseline outside it"; the figure still shows only the four cells, no `none` = 91.
   Now that §5.1 reports the interaction and the ceiling, the figure should carry them too — they
   are the section's main qualification and the figure is where a skimming reader stops.
   (The `figure*` → `figure` sizing fix from R1 minor 4 has landed.)
4. **`fig:arms` caption is now checkpoint-specific but reads general.** "Destroying validity alone
   removes almost the whole effect" is true of the plotted Qwen checkpoint and false of Gemma.
   Add "on this checkpoint; cf. §5.3".
5. **Red/green palette persists and now carries more load** (R1 minor 7). `fig:size` encodes three
   categories — viable / collapsed / below floor — as green / red / grey, with the two
   *substantive* categories being the red-green pair. Deuteranopic readers lose the figure's
   entire payload. Add hatching or a marker glyph. (`fig:replication` and `fig:detection` use
   blue/orange/green and are fine.)
6. **Tie-breaking still undocumented** (R1 minor 8). Now lower-stakes — margins are 3.5–8 logits
   in the arms that matter — but b14 does record `top_two_margin` minima of 0.0, so one sentence
   should state the rule and the count.
7. **Single seed for `shuffled`** (R1 minor 10) — still one seeded permutation, and the effect
   size is now known to be checkpoint-dependent (+46.9pp vs +10.4pp), which makes multiple seeds
   more valuable, not less.
8. **Prompt-format sensitivity is now measured but not framed as such** (R1 minor 11). b17 changes
   the instruction line and candidate set on byte-identical theories and certificates, and the
   response distribution moves enormously. That *is* a format-sensitivity result, and it supports
   the paper's own citation of Zhao et al. / Zheng et al. Worth one sentence in §6.3, which
   currently still lists no prompt-format limitation.
9. **§5.7 self-reference bug.** "(\cref{sec:tenmodel} is computed from the same receipts as
   \cref{tab:models})" — §5.7 cites itself. Drop the parenthetical or point it at §5.6.
10. **Duplicate `\usepackage`** (R1 minor 13) — `microtype`, `nicefrac` and `cleveref` are still
    each loaded twice.
11. **b17 has no `none` arm.** `irrelevant` (75.0% Unknown) is the abstention baseline, which is
    defensible, but a `none` arm would separate "a record is present" from "the three-candidate
    instruction" as the driver of that 75%. 192 prompts.
12. **`tab:replication` column header `brk`/`tr_1`** is terse to the point of obscurity in a table
    that is the paper's replication centrepiece. Spell them out.
13. **Title change is an improvement** — "An Answer-Evidence Decomposition Across Ten Models"
    describes what the paper now is, where the old title asserted two conclusions one of which has
    since been refuted. Good call.

---

## 4. Questions for the authors

1. How is 18,816 computed? I count 17,112 across the released receipts.
2. Was b17 run on Gemma-3-4B or Qwen bf16, or only on Qwen 4-bit?
3. Why is `irrelevant` rather than `none` the baseline for the surface component, given Gemma's
   `none` = 22/96? Does the share survive re-baselining (I compute 51.4%)?
4. Was Gemma's `shuffled` = 86/96 considered when leaving §5.2's order claim unqualified?
5. Is the ten-model mean state effect intended to include the four models with min per-class
   recall 0.000 in every arm?
6. Is the appendix placement of `tab:replication`, `tab:sdt` and `fig:detection` a page-limit
   decision?

---

## 5. Assessment

The round-1 review asked for seven things; the authors delivered all seven, ran four new analyses,
and let two of them overturn claims the previous draft led with. The abstract now opens by saying
the headline mechanism number does not generalise, and the paper's most confident section is the
one refuting its own prior interpretation. The certifier validation is now genuinely layered
(tautology limit stated, nine adversarial cases, independent-algorithm differential on the actual
nonce panels), the interaction and ceiling are disclosed, the share carries a ratio bootstrap, and
viability is correctly reframed as a property of (model × arm). Every number I checked reproduced
from the receipts. On substance this is now a good paper making a defensible, useful, and
unusually well-policed claim.

The gap is between the paper's analysis and its prose. Roughly a third of the text — the whole
Introduction, part of Related Work, the Setup, §5.4, §6.1, the Reproducibility Statement, two
table captions — is unrevised v1 material that asserts what §5.3–§5.7 refute, and the abstract's
own audit counts do not reconcile with the released artifacts. Those are the defects a reviewer
will read as carelessness on precisely the dimension the paper claims as its contribution. They
are also a single careful pass from fixed.

Three substantive items remain: the detection refutation should be run on Gemma or scoped to one
checkpoint (New-3); Gemma's share should be re-baselined on `none` and the surface-vs-cued-
inference question decided from the receipts (New-4); and the ten-model mean should exclude the
degenerate responders (New-6). None requires more than a few hundred additional prompts, and two
require none.

**Recommendation: minor revision.** With New-1 through New-6 addressed I would recommend
acceptance.
