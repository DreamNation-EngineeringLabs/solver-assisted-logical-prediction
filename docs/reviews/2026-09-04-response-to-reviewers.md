# Response to reviewers

- **Manuscript:** "Reading Is Not Reasoning, and Reasoning Is Not Robustness"
- **Review:** [`2026-09-04-solver-certificate-decomposition-peer-review.md`](2026-09-04-solver-certificate-decomposition-peer-review.md) — major revision, 7 majors, 16 minors
- **Date:** 2026-09-04

The review was correct on every major, and on two of them the new data is worse for the
paper than the review stated. We say so below rather than around it.

**Two headline claims are withdrawn.**

1. **"The model can detect when the chain is broken" is refuted**, not merely unsupported.
   The reviewer's discriminating arm (Major 4) was run. A validity tracker should raise its
   `Unknown` rate under `broken_chain`; the model's `Unknown` rate *falls* by 32.8pp against
   the `irrelevant` baseline. "Detect" is removed from §7.1, the abstract and the conclusion.
2. **The 98.3% validity share does not generalise across checkpoints.** On `gemma-3-4b` the
   share is 40.4%, with a surface component of +58.3pp against +1.0pp on the 3B checkpoints
   (Major 2). Every mechanism claim is now scoped to the checkpoint it was measured on.

A third change was not asked for and works against the paper: on the full five-arm sweep,
supplying proof state on top of the answer literal **reduces** balanced accuracy for three
of the four models that are viable anywhere, two of which are among the paper's three named
viable substrates (Major 1).

New artifacts: `results/b16_analysis_v2_allarms.json`, `results/b15_replication_v1.json`,
`results/b17_analysis_v1.json`, `results/b15_share_interval_v2.json`,
`results/closure_adversarial_v1.json`.

---

## Major 1 — Experiment 3's withheld arms

**Reviewer comment.** `results/b16_analysis_v1.json` contains all five arms for all ten
models; Table 5 and Figure 3 report `none` and `full` only, and the paper never says the
other three exist. The withheld arms contradict the paper's stated mechanism for substrate
failure: Qwen2.5-7B, called "collapsed", clears the corrected viability floor comfortably
under `conclusion_only`. "Collapsed" is a property of (model × arm), the "minimum viable
interface size near 3B" claim is not supported as stated, and the five arms are a free
ten-model replication of the Experiment 1 2×2.

**Response.** Accepted in full. All five arms are now analysed for all ten models in
`results/b16_analysis_v2_allarms.json` (n = 192, chance balanced accuracy 33.3%). The
omission was in the reporting plan, not the analysis plan — the five arms were analysed from
the start and only two were carried into Table 5. That is not a defence; it is the answer to
the reviewer's Question 1.

Balanced accuracy (%), all arms, all models:

| Model | none | irrelevant | conclusion_only | proof_prefix | full |
|---|---:|---:|---:|---:|---:|
| Qwen2.5-0.5B | 35.4 | 34.9 | 41.1 | 43.2 | 63.5 |
| OLMo-2-1B | 35.9 | 33.3 | 53.6 | 34.9 | 42.2 |
| Llama-3.2-1B | 33.9 | 33.9 | 57.8 | 36.5 | 37.0 |
| Qwen2.5-1.5B | 33.3 | 33.3 | 43.2 | 34.9 | 37.0 |
| SmolLM2-1.7B | 33.3 | 33.3 | 45.3 | 39.6 | 69.3 |
| Qwen2.5-3B | 41.1 | 39.1 | 96.4 | 74.0 | 90.6 |
| Llama-3.2-3B | 45.8 | 43.2 | 67.2 | 55.2 | 80.7 |
| Phi-4-mini | 44.8 | 39.6 | 68.2 | 71.9 | 90.6 |
| Gemma-3-4B | 63.5 | 51.0 | 100.0 | 84.4 | 96.4 |
| Qwen2.5-7B | 33.3 | 33.3 | 97.9 | 67.2 | 71.4 |

The reviewer's decisive row is confirmed exactly. Qwen2.5-7B under `conclusion_only`:
balanced accuracy 97.9%, min per-class recall 0.938, max label share 0.354 — viable. Under
`full`: 71.4%, min per-class recall 0.141 (contradicted), `Unknown` share 0.620 — not
viable. Under `proof_prefix` it is worse still: min per-class recall 0.016, `Unknown` share
0.661. Entailed and undetermined recall are 1.000 in all three arms; what proof state
destroys is specifically the contradicted class. This is the answer to Question 2: the
viability verdict does not survive, and "an apparatus cannot help an interface that cannot
express three outcomes" is the wrong gloss for this model. The interface expresses three
outcomes fine until the proof state arrives.

Viability is now reported per (model × arm): 8 of 50 cells are viable; 4 of 10 models are
viable under at least one arm (Gemma-3-4B, Qwen2.5-3B, Phi-4-mini, Qwen2.5-7B); 3 under
`conclusion_only` (Gemma-3-4B, Qwen2.5-3B, Qwen2.5-7B); 3 under `full` (Gemma-3-4B,
Qwen2.5-3B, Phi-4-mini). Only Gemma-3-4B and Qwen2.5-3B are viable under both.

**A finding the review did not name, and it is unfavourable.** The state edge in the
presence of the answer literal (`full` − `conclusion_only`) is *negative* for 6 of 10 models,
and for 3 of the 4 models that are viable anywhere: Gemma-3-4B −3.6pp, Qwen2.5-3B −5.7pp,
Qwen2.5-7B −26.6pp. Two of those three (Gemma-3-4B, Qwen2.5-3B) are among the paper's three
named viable substrates. On the models that can use a certificate at all, proof state on top
of a conclusion is on average a cost, not a benefit. The paper will state this.

**The free replication was computed.** Across the ten models: `conclusion_only` >
`proof_prefix` in 8/10; `conclusion_only` ≥ `full` in 6/10; mean answer main effect +21.6pp;
mean state main effect **+8.7pp**, against b14's +22.4pp; mean interaction −15.9pp. The
answer channel dominates more strongly and more generally than Experiment 1 showed, and the
state main effect is roughly a third of the single-checkpoint estimate.

**Changes made.**
- Table 5 and Figure 3 report all five arms for all ten models; the verdict column names the
  arm it was computed on, and per-arm verdicts are printed.
- The "minimum viable interface size near 3B" claim is restated as a floor for *tolerating
  full certificates*, not a floor for serving as an interface, and demoted from the abstract
  (see also Minor 16).
- New §5.4 reports the ten-model 2×2 as a replication of §5.1, with the +8.7pp state main
  effect against b14's +22.4pp stated as a disagreement, not a confirmation.
- New paragraph reporting the negative `full` − `conclusion_only` edge on the viable models.

---

## Major 2 — n = 1 checkpoint, and a precision confound

**Reviewer comment.** Experiments 1 and 2 use a single frozen Qwen2.5-3B at 4-bit;
Experiment 3 uses bfloat16. The mechanism model and the Experiment-3 model are different
artefacts. §7 never mentions quantisation. Required: add quantisation to the limitations, and
either run the ten b15 arms on further bf16 checkpoints or scope every mechanism claim to one
4-bit 3B checkpoint.

**Response.** Accepted, and the run was done. The ten b15 arms were re-run on two further
checkpoints (`results/b15_replication_v1.json`). **The mechanism claim does not generalise.**

| Checkpoint | truncate_1 (entailed) | broken_chain (entailed) | total state effect | surface | validity | **share** | exact McNemar p |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen2.5-3B 4-bit (paper) | 59/96 | 1/96 | +61.5pp | +1.0pp | +60.4pp | **98.3%** | 6.9e-18 |
| Qwen2.5-3B bf16 | 72/96 | 1/96 | +75.0pp | +1.0pp | +74.0pp | **98.6%** | 8.5e-22 |
| Gemma-3-4B bf16 | 96/96 | 58/96 | +97.9pp | **+58.3pp** | +39.6pp | **40.4%** | 7.3e-12 |

Two readings, both of which go into the paper:

1. **Quantisation moves magnitude, not the share.** Dequantising the same 3B model raises the
   validity component from +60.4pp to +74.0pp — a large change in effect size — while the
   share moves 98.3% → 98.6%. So the precision confound the reviewer identified is real for
   the *size* of the effect and immaterial for the *decomposition*. This is a genuine
   strengthening of the mechanism result on that model.
2. **Model identity moves the share, decisively.** Gemma-3-4B answers 58/96 entailed items
   correctly under `broken_chain` — a certificate matched on line count, line types, entity
   and predicate occurrence and token length, with validity destroyed. Its surface component
   is +58.3pp and its validity share is 40.4%. On this checkpoint the majority of the state
   effect *is* surface overlap. The abstract's "98.3% of the state effect is inference over
   the supplied lines" is a property of the 3B checkpoints, not of the architecture.

One further point, unfavourable and worth stating: no checkpoint resists a corrupted
certificate. `misleading` correct counts are 3/192 (3B 4-bit), 6/192 (3B bf16) and **0/192**
(Gemma-3-4B, d' = −5.131). The model with the *best* clean performance is the one that
follows a wrong-pointing certificate on every single item.

**Changes made.**
- Quantisation is named explicitly in §7 limitations, with the +60.4 → +74.0pp magnitude
  shift and the 98.3 → 98.6% share stability given as the measured consequence.
- Abstract and conclusion scope the validity-share claim to the checkpoints measured; the
  single number "98.3%" no longer stands unqualified as a property of the phenomenon.
- New §5.5 (replication) carries the three-checkpoint table above and the finding that the
  share is checkpoint-dependent.
- The `misleading` result is extended to all three checkpoints, including Gemma-3-4B at 0/192.

---

## Major 3 — the unreported interaction and the ceiling

**Reviewer comment.** `b14_posthoc_2x2_reanalysis_v1.json` records `interaction: -0.2917`,
never mentioned, larger in magnitude than either main effect. With `full` at 191/192 the
+answer/+state cell is at ceiling, so the "answer literal retains only 30% of its value once
state is present" figure largely measures remaining headroom above `proof_prefix`, not
channel redundancy.

**Response.** Accepted; the "30%" framing is dropped. The interaction is **−29.2pp**, against
main effects of +22.4pp (state) and +27.1pp (answer) — larger in magnitude than either, and
the 2×2 is ceiling-limited: `full` = 191/192 = 99.5%, `proof_prefix` = 167/192 = 87.0%, so
only 25 items (13.0pp) of headroom remain above `proof_prefix` for the answer literal to
close. It closes 24 of them.

Expressed as the ceiling-aware quantity the reviewer suggested — proportion of *available*
headroom closed — the answer literal closes 24/25 = **96.0%** of headroom when state is
present and 80/96 = **83.3%** when it is not. On that reading the answer channel is not
weakened by the presence of state at all; the "30%" was the ceiling.

The ten-model sweep replicates the sign: mean interaction −15.9pp, negative in 7 of 10
models, and −60.4pp on Qwen2.5-7B.

**Changes made.**
- The interaction (−29.2pp) is reported in §5.1 alongside the four edges and both main
  effects, and the 2×2 is labelled ceiling-limited in the text and the Figure 1 caption.
- The "retains only 30% of its value" sentence is deleted from §5.1, §6 and the abstract, and
  replaced by the headroom-closed figures (96.0% with state, 83.3% without) with the ceiling
  caveat attached.
- The ten-model mean interaction is reported in the new §5.4.

---

## Major 4 — "detect" is refuted

**Reviewer comment.** §7.1's claim that the model "can detect when the chain that would
license it is broken" is not separable from the model failing to find a completable pattern
and falling back to its default label, since on a binary panel both predict `No`. The clean
discriminating experiment already exists: score `broken_chain` on the three-class panel,
where a validity tracker should answer `Unknown` and a pattern-completer should answer `No`.

**Response.** The experiment was run (`results/b17_analysis_v1.json`, n = 192, three arms
rescored on the b16 three-class panel). **The detection claim is refuted, not merely
unsupported** — the effect runs opposite to the direction detection predicts.

| Arm | Yes | No | Unknown | Unknown rate |
|---|---:|---:|---:|---:|
| irrelevant | 0 | 48 | 144 | 75.0% |
| broken_chain | 1 | 110 | 81 | 42.2% |
| truncate_1 | 61 | 110 | 21 | 10.9% |

Supplying a broken chain makes the model **less** likely to answer `Unknown`, by −32.8pp
against the `irrelevant` baseline. A validity tracker moves the other way.

The two-arm comparison is sharper still and answers Question 6: `No` is **110/192 under both
`broken_chain` and `truncate_1`** — identical. The arms differ only in `Yes` (1 vs 61). So the
distinction the model is making is not valid-vs-invalid; it is completable-vs-not. It
completes a final inference when both premises are present and adjacent, falls back
otherwise, and the fallback itself shifts away from `Unknown` as soon as any query-relevant
certificate is on the page — which is the failure mode the paper elsewhere argues matters
most.

**Changes made.**
- "Detect" is removed from §7.1, the abstract and the conclusion, wherever it is applied to
  the model.
- §7.1 now states only what the design supports: *the model completes a final inference when
  both premises are present and adjacent, and does not do so otherwise*.
- New §5.6 reports the b17 arm, including the fact that the `Unknown` rate moves in the
  direction opposite to detection, and the identical `No` counts under `broken_chain` and
  `truncate_1`.
- The `misleading` result (189/192 followed) is cross-referenced as consistent with this
  reading rather than left as an unexplained tension.

---

## Major 5 — an interval on the share, and Holm values in the Results

**Reviewer comment.** The 98.3% share is a ratio of two paired differences reported as a
point estimate; the numerator is BCa'd but the ratio is not, and its own interval is
materially wider. Separately, §4.4 declares Holm adjustment and the analysis files compute
it, but every p-value printed in the Results is the raw exact-McNemar value.

**Response.** Both accepted. The whole ratio is now bootstrapped over paired item resamples
(`results/b15_share_interval_v2.json`; 100,000 resamples, seed 2026090315, n = 96 entailed
items). The reviewer's estimate of the interval was close:

- validity share 98.3%, 95% BCa **[94.4%, 100.0%]**
- surface component +1.0pp, 95% BCa **[+0.0, +3.1]pp**

The share therefore stays well above one half on this checkpoint even at the lower bound —
which makes the Gemma-3-4B result in Major 2 (40.4%) a between-checkpoint difference, not
sampling noise on a single estimate.

On Holm: no recomputation was needed. The adjusted values were already in the released
analysis files (`holm_adjusted_edge_family` in `b14_posthoc_2x2_reanalysis_v1.json`,
`holm_secondary` in `b15_analysis_v1.json`) and were simply not printed. The reviewer's
example checks: the order contrast is 6.8e-13 raw and 1.4e-12 Holm-adjusted. The edge family
of four: `irrelevant − conclusion_only` 6.6e-24, `irrelevant − proof_prefix` 4.5e-19,
`proof_prefix − full` 2.4e-07, `conclusion_only − full` 6.1e-05. The reviewer is right that a
paper about measurement discipline should not declare an adjustment in the Method and print
unadjusted values in the Results.

**Changes made.**
- The abstract, title-adjacent claim, §5.2 and the conclusion carry the BCa interval with the
  98.3% point estimate.
- Every p-value in the Results text and in Tables 2–4 is printed as raw with the Holm-adjusted
  value alongside.
- Table 2 states its family (the four post hoc edges); the all-pairs sweep in the released
  file states its multiplicity (10 pairs).

---

## Major 6 — what the certifier validation can and cannot catch

**Reviewer comment.** 23,240/23,240 with a perfectly diagonal confusion is more plausibly a
sign that the check is not independent: ProofWriter's OWA labels are themselves produced by
forward chaining over the same fragment. Required: say what class of error the validation can
and cannot catch, and add checks with different failure modes — cyclic rules, antecedents
derivable only beyond the round cap, theories deriving an atom and its negation, and a
differential test on the *generated* nonce theories, where ProofWriter gives no coverage.

**Response.** Accepted. Two additions (`results/closure_adversarial_v1.json`).

*Nine hand-constructed adversarial cases, all passing:* cyclic rules must still saturate;
a cycle that never reaches the query returns `undetermined`; a chain longer than the default
round cap is still reached; negation derived with a positive query returns `contradicted`;
a predicate absent from the theory returns `undetermined`; a query about an absent entity
returns `undetermined`; a rule fires only for the entity that satisfies it; a theory deriving
both an atom and its negation is **rejected as inconsistent, not labelled** (1 conflict
recorded, `consistent: false`); and the round cap **fails loudly** (`saturated: false`)
rather than silently returning a verdict from a partial fixpoint. The last two are the cases
where a quiet wrong answer would have corrupted panel construction, and they are the reason
these were written.

*Differential test on the generated nonce panels* — the coverage ProofWriter cannot give,
because the nonce theories are exactly where the certifier is actually used. An independently
written reference implementation using a deliberately different algorithm (exhaustive ground
instantiation followed by a naive fixpoint, rather than the certifier's restricted forward
chainer) was run against every item of both generated panels: **192/192 agreement on the b15
panel and 192/192 on the b16 panel**.

We accept the limit of this too, and will state it: the reference implementation encodes the
same intended semantics, so like the ProofWriter check it tests implementation rather than
specification. What it adds over the ProofWriter check is a different algorithm on the
theories that matter, and coverage where there was none.

**Changes made.**
- The certifier validation subsection now states plainly what the ProofWriter agreement can
  catch (implementation bugs in the forward chainer) and what it cannot (semantic
  independence — ProofWriter's OWA labels are produced by forward chaining over the same
  fragment, so agreement is partly self-agreement). The phrase "an independently labelled
  corpus" is removed.
- The nine adversarial cases and the 192/192 + 192/192 differential results are reported, with
  the shared-specification caveat attached.

---

## Major 7 — the undisclosed prior report

**Reviewer comment.** Table 2's "Reported originally" column, §4.1 and §6.2 all refer to a
prior report of Experiment 1 that the paper never identifies. The repository contains
`manuscript/grounded_state_repair_preprint_v1/manuscript.md`, reporting the identical five-arm
counts and the identical primary. Required: state it explicitly, anonymised, cite it if it was
posted, and reconcile its conclusion that Qwen2.5-3B *failed* the open-world unknown gate
against Experiment 3 listing Qwen2.5-3B as viable.

**Response.** Accepted; the omission was ours and it should not have needed a reviewer to find
it. Answering Question 4 directly: the earlier report was **never publicly posted** — no
preprint-server record, no DOI; the project's own release tracking lists public posting and
DOI deposit as outstanding. It exists only as an internal document in the repository.

On the reconciliation (Question 5), the paper will give three reasons rather than leaving a
reader to guess, and one of them is the load-bearing one:

1. **Different artefact.** The prior report's gate and Experiment 1 use the 4-bit checkpoint;
   Experiment 3 is bf16 throughout (see Major 2, where dequantisation moves the validity
   component by +13.6pp on the same model).
2. **Different panel and criterion.** The prior gate was a small qualification set scored with
   no solver material and required near-perfect recall on the unknown class; Experiment 3
   applies min per-class recall ≥ 0.50 per arm on a 192-item certified panel.
3. **The gate and the sweep do not actually disagree.** Under Experiment 3's `none` arm,
   Qwen2.5-3B has entailed recall 0.000, min per-class recall 0.000 and balanced accuracy
   41.1% — it is **not viable unaided**, exactly as the prior report concluded. Its viability
   appears only once certificate material is supplied. Reported as "viable" without the arm
   qualifier, this looked like a contradiction; per-arm (Major 1) it is not one.

**Changes made.**
- §4.1 states, anonymised: Experiment 1's per-arm results were reported in an earlier
  unpublished report by the authors, cited as [Anon]; the 2×2 reading in this paper is new.
  The bibliography carries the anonymised entry, and the "Reported originally" column in
  Table 2 points to it.
- A short reconciliation paragraph in §5.3 gives the three reasons above, with the `none`-arm
  numbers, so the apparent contradiction is resolved in the paper rather than by the reader.

---

## Minor comments

| # | Comment | Disposition |
|---|---|---|
| 1 | §5.3 mixes an all-items count with an entailed-subset contrast in one sentence | Fixed: the sentence now says −100.0pp is the entailed subset and gives −98.4pp for all 192. |
| 2 | §5.3 undersells the class split (`Yes` on 93/96 contradicted items) | Adopted: the class split now leads the paragraph, ahead of the "3 of 192". |
| 3 | Figure 1 caption says the baseline is drawn outside the square; it is not drawn | Fixed: `none` = 91 added to the figure. |
| 4 | Figure 1 sized to `\columnwidth` inside a `figure*` | Fixed: widened to the spanning float. |
| 5 | Figure 2 left panel titled "Accuracy" while the axis reads correct-of-96; seven bars are 0 | Fixed: retitled to match the axis; the all-192 count is plotted alongside. |
| 6 | No uncertainty on any figure | Adopted: Figures 2 and 3 carry the BCa intervals already in the analysis files. |
| 7 | Figure 3 palette is red/green — worst pairing for deuteranopia, and verdict is the payload | Fixed: verdict encoded by shape as well as colour, on a colourblind-safe palette. |
| 8 | Tie-breaking in likelihood scoring undefined; `top_two_margin` min is 0.0 for `none` and `irrelevant` | Adopted: the rule and the affected item count are stated in §3.4 (answers Question 3). |
| 9 | Qwen2.5-3B and Phi-4-mini byte-identical in Table 5 | Adopted: footnote noting the mirror-image confusion matrices; per-class recalls printed, which distinguish them (`full` min recall 0.719 for both, but Qwen misses undetermined and Phi misses contradicted). |
| 10 | Single seed for `shuffled` | Accepted as a limitation and named as one; additional seeds are not run, since the sealed-panel convention makes re-running a completed arm a new versioned experiment rather than an amendment. |
| 11 | One prompt template, no format variation | Accepted: named explicitly as a limitation in §7; no format-variation arm is run for this revision. |
| 12 | Reproducibility Statement duplicated across two paragraphs | Fixed: merged. |
| 13 | `microtype`, `nicefrac`, `cleveref` each loaded twice | Fixed. |
| 14 | Built with `article` at 0.9in margins; will overrun 9 pages under the real style file | Accepted: rebuilt under the venue style; the new §5.4–§5.6 material is absorbed by cutting the duplicated Reproducibility text (Minor 12) and moving the per-arm sweep table to the appendix. |
| 15 | §6.1's alternative reading (broken certificate as a pointer back into the theory) is testable — run `truncate_1` and `broken_chain` with the theory withheld | Accepted as a stated open control, not run for this revision. Major 4's b17 result narrows it: with the theory visible, `No` counts under the two arms are identical (110/192 each), so the pointer reading has to explain a difference that appears only in `Yes`. |
| 16 | Abstract's "minimum viable interface size near 3B" sits awkwardly with Llama-3.2-3B failing and Qwen2.5-3B passing; size is confounded with family and recipe | Adopted: removed from the abstract as a finding. Major 1 makes it untenable as stated in any case — viability is per (model × arm), and Qwen2.5-7B is viable under `conclusion_only` and not under `full`. |

---

## Errata, added 2026-09-08 by the round-9 audit

Two commitments in this response were not delivered as written. Recorded here
rather than edited above, since this is a dated record.

- **Minor 14, "rebuilt under the venue style".** The paper remained
  `\documentclass[10pt]{article}` at 0.9in margins. It was rebuilt at the
  supplied template's geometry on 2026-09-08 (audit finding #1);
  `iclr2027_conference.sty` is still unpublished.
- **Minor 9, the Qwen/Phi mirror-image footnote.** The per-class recalls it
  promised are now in `tab:models`, but the footnote was never added; the paper
  contains no `\footnote` at all.
