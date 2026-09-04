# Peer review — "Reading Is Not Reasoning, and Reasoning Is Not Robustness"

- **Manuscript:** `paper/solver-certificate-decomposition/final/paper.pdf` (11 pp, ICLR-style, double-blind)
- **Reviewer method:** `cognitive-core/.claude/skills/peer-review` (Stages 1–7), with every reported number
  re-derived from the released artifacts (`results/*.json`) rather than taken on trust.
- **Date:** 2026-09-04
- **Recommendation:** **Major revision.** Score ~5/10 (marginally below acceptance), confidence 4/5.
  The path to a clear accept is short and requires **no new model runs** — see Major 1.

---

## 1. Summary

The paper asks what a small language model actually does with a formally verified solver
certificate, and answers it with three sealed experiments on procedurally generated
rule-chaining panels scored by next-token likelihood over verified single-token candidates.
Its three moves are: (a) re-read a five-arm certificate factorial as a 2×2 of *answer
evidence* × *proof state*, showing the prespecified primary contrast was the diagonal and
therefore unattributable; (b) build a surface-matched invalid certificate (`broken_chain`)
that holds line count, line types, query-entity occurrence count, query-predicate presence
and token length fixed and destroys validity alone, yielding a +60.4pp validity component
against a +1.0pp surface component; and (c) sweep ten models on a three-class panel whose
*undetermined* items are certified by a forward-closure certifier validated at 23,240/23,240
against ProofWriter OWA.

The methodological instincts here are better than most of this literature: signal-detection
reporting alongside accuracy, per-item certification of underdetermination, hash-stamped
panels and per-response receipts, and — unusually — the authors report two of their own
design failures (a prespecified 15pp target that was arithmetically unreachable, and a
viability criterion a degenerate all-`Unknown` responder maximised) rather than quietly
repairing them.

**Verification note.** I re-derived every table and headline number from the released JSON.
All of them reproduce exactly: the 2×2 cells (91/96/176/167/191), the four edges
(+41.67/+36.98/+12.50/+7.81pp), the main effects (+22.4/+27.1pp), the "30% retained" figure,
the b15 decomposition (60.4 / 1.0 / 61.5pp, 98.3% share), every $d'$ under the loglinear
correction, the paired McNemar tables, and the certifier's 23,240/23,240 with a perfectly
diagonal confusion matrix. The bibliography is clean — 39 entries, all 39 cited, none
missing, and spot-checked attributions are accurate. Reproducibility is a genuine strength
of this submission, not a claim.

The problems are with **what is left out of the paper that is present in its own released
data**, and with two claims that outrun the design.

---

## 2. Major comments

### Major 1 — Experiment 3 ran five arms on ten models; the paper reports two, and the withheld arms overturn its substrate conclusion

`results/b16_analysis_v1.json` contains `none`, `irrelevant`, `conclusion_only`,
`proof_prefix` and `full` for **all ten models**. Table 5 and Figure 3 report only `none` and
`full`. The paper never states that the other three arms exist. (The 12,480 prompt count
implicitly discloses 5 arms × 192 × 10, but no reader will reverse-engineer that.)

This matters because the withheld arms contradict the paper's stated mechanism for
substrate failure. Balanced accuracy (%), from the released file:

| Model | none | irrelevant | conclusion_only | proof_prefix | full | Paper's verdict |
|---|---|---|---|---|---|---|
| Qwen2.5-0.5B | 35.4 | 34.9 | 41.1 | 43.2 | 63.5 | collapsed |
| OLMo-2-1B | 35.9 | 33.3 | 53.6 | 34.9 | 42.2 | collapsed |
| Llama-3.2-1B | 33.9 | 33.9 | 57.8 | 36.5 | 37.0 | collapsed |
| Qwen2.5-1.5B | 33.3 | 33.3 | 43.2 | 34.9 | 37.0 | collapsed |
| SmolLM2-1.7B | 33.3 | 33.3 | 45.3 | 39.6 | 69.3 | below floor |
| Qwen2.5-3B | 41.1 | 39.1 | **96.4** | 74.0 | 90.6 | viable |
| Llama-3.2-3B | 45.8 | 43.2 | 67.2 | 55.2 | 80.7 | below floor |
| Phi-4-mini | 44.8 | 39.6 | 68.2 | 71.9 | 90.6 | viable |
| Gemma-3-4B | 63.5 | 51.0 | **100.0** | 84.4 | 96.4 | viable |
| Qwen2.5-7B | 33.3 | 33.3 | **97.9** | 67.2 | 71.4 | **collapsed** |

The decisive row is Qwen2.5-7B. The paper's headline non-monotonicity claim — "the largest
model tested collapses while a 3B model does not", and the mechanistic gloss "an apparatus
cannot help an interface that cannot express three outcomes" — rests on this model's `full`
arm (min per-class recall 0.141, 62.0% `Unknown`). Under `conclusion_only` the same model has
**min per-class recall 0.938 and max label share 0.354**, i.e. it clears the paper's own
corrected viability floor by a wide margin and is the second-best model in the sweep at 97.9%
balanced accuracy. Its contradicted-class recall goes 0.938 → 0.141 *when the proof state is
supplied*. So Qwen2.5-7B is not an interface that cannot express three outcomes; it is an
interface that the proof state actively breaks. Same pattern, weaker, for Llama-3.2-3B
(contradicted recall 1.000 under none is not the issue; `full` = 0.422).

Three consequences:

1. **"Collapsed" is not a property of the model, it is a property of (model × arm).** The
   verdict column in Table 5 needs to say which arm it was computed on, and the
   `conclusion_only` verdicts need to be in the table.
2. **The "minimum viable interface size near 3B" claim is not supported as stated.** It is a
   floor for tolerating full certificates, not a floor for serving as an interface.
3. **You are sitting on the cross-model replication your paper needs.** Experiment 3's five
   arms *are* Experiment 1's 2×2 plus baseline, on ten models. Right now Experiments 1 and 2
   rest on a single checkpoint (Major 2); computing the 2×2 edges from b16 for all ten models
   turns that into a ten-model replication of the central decomposition, at zero additional
   compute. From the numbers above, `conclusion_only` > `proof_prefix` for 8 of 10 models, and
   `conclusion_only` ≥ `full` for 3 — which is a *stronger* and more general version of your
   Experiment 1 finding that the answer channel dominates.

**Required:** report all five arms for all ten models; recompute the viability verdicts
per-arm; either fold the ten-model 2×2 in as a replication of §5.1 or state explicitly why
you are not doing so. Until the withheld arms are in the paper, the omission reads as
selective reporting of exactly the arms that complicate the conclusion, which is the charge
the paper's own sealed-protocol apparatus exists to pre-empt.

### Major 2 — The mechanism claim rests on n = 1 checkpoint, at a different precision from the sweep that shows the effect is idiosyncratic

Experiments 1 and 2 — which carry the 98.3% validity share, the one-step depth cliff, and the
misleading-certificate result — use a single frozen Qwen2.5-3B **at 4-bit**. Experiment 3 uses
bfloat16 throughout, correctly, "so precision is not confounded with model identity". The
consequence is not drawn: the mechanism model and the Experiment-3 Qwen2.5-3B are not the same
artefact, so the "floor near 3B" story and the mechanism story are about two different
objects. §7 lists "a single model" under generalisation but never mentions quantisation, and
4-bit weight quantisation is known to move exactly the quantity being measured here
(next-token likelihood margins and criterion placement).

Experiment 3 also shows the arm-response profile is strongly model-specific and non-monotonic
— which is precisely the reason a single-checkpoint mechanism result should not be stated as
generally as the abstract states it ("$98.3\%$ of the state effect is inference over the
supplied lines").

**Required:** (a) add quantisation to the limitations, explicitly; (b) run the ten b15 arms on
the three viable bf16 models (Qwen2.5-3B, Phi-4-mini, Gemma-3-4B) — 5,760 prompts, cheap
relative to what is already spent — or scope every mechanism claim in the abstract and
conclusion to "one 4-bit 3B checkpoint".

### Major 3 — The 2×2's interaction is −29.2pp and is never reported; `full` is at ceiling, so the main effects are not identified

`b14_posthoc_2x2_reanalysis_v1.json` records `interaction: -0.2917`. The paper reports the
four edges and both main effects and never mentions the interaction, which is larger in
magnitude than either main effect. With `full` at 191/192 (99.5%) the +answer/+state cell is
at ceiling, so both "with the other factor present" edges (+12.5pp, +7.8pp) are compressed by
a floor-on-errors, and the averaged main effects are correspondingly deflated.

This directly undercuts the paper's most quotable secondary claim, "the answer literal retains
only 30% of its value once state is present" (12.50/41.67). That ratio is not a measurement of
channel redundancy; it is largely a measurement of how little headroom remains above
`proof_prefix` = 167/192. A design with `full` at 99.5% cannot separate "the channels are
redundant" from "the ceiling ate the effect".

**Required:** report the interaction; state that the 2×2 is ceiling-limited; either drop the
"30%" framing or replace it with a ceiling-aware quantity (e.g. proportion of *available*
headroom closed, or the same 2×2 on a harder panel where `full` is not at ceiling).

### Major 4 — "The model can detect when the chain is broken" is not established by this design

§7.1 states the model "can detect when the chain that would license it is broken". The data do
not separate that from the null hypothesis that the model simply fails to find a
one-step-completable pattern and falls back to its default label. From `b15_analysis_v1.json`:
`irrelevant` emits `No` on 100% of items, `broken_chain` on 99.5%, and the contrast between
them is +1/96 with p = 1. Every non-completable arm — `none`, `irrelevant`,
`same_entity_irrelevant`, `truncate_2`, `truncate_3` — lands on the identical point
(96/192, 0/96 entailed, $d' = 0.000$, $c = 2.565$). "Detected the break" and "found no pattern
to complete" predict the same response here, because the correct answer under a broken
certificate *is* the default label.

The `misleading` arm is evidence *against* the detection reading: a model that verified
validity would reject a certificate whose final rule is fabricated and absent from the theory,
and it follows it on 189/192 instead.

The clean discriminating experiment is already built. Your b15 `broken_chain` items are
certified *undetermined* under the displayed lines, and you have a three-class panel and
scorer (b16). On a three-class panel a validity-tracker should answer `Unknown` to
`broken_chain`; a pattern-completer should answer `No`. That is one arm on one panel.

**Required:** either run that arm, or weaken §7.1 and the conclusion to what the data support
— *the model completes a final inference when both premises are present and adjacent, and
does not do so otherwise* — and drop "detect", which is an attribution the design cannot make.

### Major 5 — Uncertainty on the 98.3% share, and Holm adjustment claimed but not reported

The validity share is a ratio of two paired differences reported to four significant figures
as a point estimate. You BCa the numerator (+60.4pp, [+49.0, +68.8]) but not the ratio. The
denominator's surface component is 1/96 with p = 1 and BCa [0.0, +3.1]pp, so the share's own
interval is materially wider than "98.3%" suggests — plausibly ~[93%, 100%]. Since 98.3% is
the number in the abstract, the title and the conclusion, it needs an interval.

Separately, §4.4 declares "Holm adjustment within declared families", and both analysis files
compute it (`holm_secondary`, `holm_adjusted_edge_family`, `holm_primary_across_models`), but
every p-value in the Results text and in Tables 2–4 is the **raw** exact-McNemar value (e.g.
§5.2 quotes 6.8×10⁻¹³ for the order contrast; the Holm value is 1.4×10⁻¹²). No conclusion
changes, but a paper whose thesis is measurement discipline should not claim an adjustment in
the Method and print unadjusted values in the Results. Table 2's four post hoc edges plus the
all-pairs sweep in the released file (10 pairs) also need their multiplicity stated.

### Major 6 — The certifier validation may be closer to tautological than "independent"

23,240/23,240 with a perfectly diagonal confusion and zero unusable theories is a striking
result, and the honest reading of a perfect score is that the check may not be independent:
ProofWriter's OWA labels are themselves produced by forward chaining over the same fragment
(Horn-like rules, literal antecedents, no negation-as-failure), so agreement partly measures
"my forward chainer agrees with their forward chainer". That is a genuine implementation check
— it would catch a coding bug — but it is weaker than the paper's framing ("an independently
labelled corpus") implies.

**Required:** say what class of error this validation can and cannot catch; add at least one
check with different failure modes (hand-constructed adversarial theories: cyclic rules, rules
whose antecedents are only derivable at depth > cap, theories deriving both an atom and its
negation, and — most importantly — a differential test against an off-the-shelf ASP/Datalog
engine on the *generated* nonce theories, which is where the certifier is actually used and
where ProofWriter offers no coverage at all).

### Major 7 — Undisclosed prior report of Experiment 1

Table 2 has a column headed "Reported originally", §4.1 refers to "the experiment we
reanalyse", and §6.2 discusses design errors of an experiment "we report rather than repair" —
but the paper never says where Experiment 1 was originally reported. The repository contains
`manuscript/grounded_state_repair_preprint_v1/manuscript.md`, a prior preprint of the same
programme whose abstract reports the identical b14 five-arm counts (91/96/176/167/191) and the
identical −0.047, p = 0.078 primary. Whether that document was ever posted, a reviewer cannot
tell from the submission, and the distinction is the difference between a legitimate
reanalysis-of-own-prior-work and an undeclared overlapping submission.

**Required:** state it explicitly, anonymised — "Experiment 1's per-arm results were reported
in an earlier unpublished/anonymised report by the authors (cited as [Anon]); this paper's 2×2
reading is new" — and, if it was posted, cite it. Note also that the prior report concluded
Qwen2.5-3B *failed* the open-world unknown gate, whereas Experiment 3 lists Qwen2.5-3B as one
of three viable substrates on the three-class panel. Different panels and precisions plausibly
explain it, but the paper should reconcile rather than leave it to a reader who finds both.

---

## 3. Minor comments

1. **§5.3, misleading contrast, unit mixing.** "The model scores 3 of 192, with $d' = -4.363$:
   `misleading − full` = −100.0pp" puts an all-items count and an entailed-subset contrast in
   one sentence. The −100.0pp is the entailed subset (`misleading_minus_full_entailed`); on all
   192 items it is −98.4pp. Say which.
2. **§5.3 undersells its own strongest evidence.** The class split is the argument: on
   contradicted items the model emits `Yes` on 93/96 (response distribution `Yes` 0.484,
   entailed_correct 0) — it overrides an otherwise near-total `No` prior specifically because
   the certificate told it to. That is far more compelling than "3 of 192" and it is one
   sentence.
3. **Figure 1 caption/figure mismatch.** The caption says "with the no-material baseline
   outside it"; the figure shows only the four cells. `none` = 91 is not drawn.
4. **Figure 1 float sizing.** `\includegraphics[width=\columnwidth]` inside a `figure*`
   spanning both columns — half the allocated width is blank. Use `\figure` or widen it.
5. **Figure 2, left panel mislabelled.** Titled "Accuracy" while the axis (correctly) reads
   "correct, entailed items (of 96)". Seven of ten bars are 0, so the panel is mostly empty;
   consider plotting the all-192 count alongside, or dropping the zero bars into a note.
6. **No uncertainty on any figure.** Given that reporting discipline is the paper's thesis,
   Figures 2 and 3 should carry the BCa intervals that the analysis files already contain.
7. **Figure 3 palette is not colourblind-safe.** Verdict is encoded red vs green — the single
   worst pairing for deuteranopia, and verdict is the figure's payload. Add a shape or hatch
   channel, or move to a safe palette.
8. **Tie-breaking in likelihood scoring is undefined.** `top_two_margin` records `min: 0.0` for
   both `none` and `irrelevant` in b14 — genuine ties between candidate tokens. With a
   two-candidate forced choice a tie is a coin flip that silently enters the accuracy count.
   State the rule and how many items hit it.
9. **Qwen2.5-3B and Phi-4-mini are byte-identical in Table 5** (90.6 / 71.9 / 42.7). Every
   reviewer will suspect a copy-paste error. It is a real coincidence — the confusion matrices
   are mirror images (Qwen misses 18 undetermined→`No`; Phi misses 18 contradicted→`Unknown`)
   — so add a footnote saying so, and consider printing the per-class recalls that distinguish
   them.
10. **Single seed for `shuffled`.** One seeded permutation supports "order matters" but not the
    effect size (+46.9pp), which is a property of one draw. Three to five seeds would cost
    almost nothing.
11. **One prompt template, no format variation.** §3.4 cites Zhao et al. and Zheng et al. on
    prompt- and token-prior sensitivity, then evaluates one four-line template. A paraphrase
    or label-swap arm (`Yes`/`No` → `True`/`False`) would test whether the decomposition itself
    is format-robust. At minimum, name this as a limitation — it currently is not one.
12. **Reproducibility Statement is duplicated.** Its two paragraphs restate each other almost
    sentence for sentence (receipts, standard-library audits, hash-stamped panels, 12,480 with
    zero failures). Merge.
13. **Duplicate `\usepackage`.** `microtype`, `nicefrac` and `cleveref` are each loaded twice
    (lines 24–29).
14. **Format / page budget.** The submission is built with `article` at 0.9in margins, not the
    ICLR style, per the header note. Body runs to ~9.5 pages before references. When the real
    style file is dropped in, expect to be over the 9-page limit — plan the cut now rather
    than at the deadline.
15. **§6.1's alternative reading deserves a control, not a caveat.** "A model that used a
    broken certificate as a pointer back into the theory would be performing inference of a
    different kind; our design does not exclude that reading." Since the theory is visible in
    every arm, this is testable directly: run `truncate_1` and `broken_chain` with the theory
    withheld. Two arms.
16. **Abstract precision.** "a minimum viable interface size near 3B" sits awkwardly beside
    Llama-3.2-3B (3.2B) failing the floor and Qwen2.5-3B (3.0B) passing. Size is also
    confounded with family, tokeniser and instruction-tuning recipe across the ten models; the
    paper says model is not a randomised factor, but the abstract still states the floor as a
    finding rather than a description.

---

## 4. Questions for the authors

1. Why were `irrelevant`, `conclusion_only` and `proof_prefix` omitted from Experiment 3's
   reporting? Was the omission a decision or an oversight?
2. Does the viability verdict for Qwen2.5-7B survive computing it on `conclusion_only`
   (min recall 0.938)? If not, what is the substrate claim?
3. How were ties in the two-candidate likelihood comparison resolved, and on how many items?
4. Was the b14 preprint (`grounded_state_repair_preprint_v1`) ever publicly posted?
5. The prior report says Qwen2.5-3B failed the open-world unknown gate; Experiment 3 lists it
   as viable. What accounts for the difference — panel, precision, or criterion?
6. On `broken_chain`, does the model's answer distribution differ from `irrelevant` in *any*
   measurable way (logit margin, criterion, per-item agreement)? A margin difference with an
   identical label distribution would be real evidence for detection.

---

## 5. Assessment

The core contribution — that the standard "same-shape irrelevant record" control does not rule
out answer reading, and that a surface-matched *invalid* certificate does — is correct,
non-obvious, cheap to adopt, and applies to every solver-, tool- and retrieval-augmented
system that reports an end-to-end gain. The `misleading` result (189/192) is the paper's most
consequential number and is cleanly obtained. The measurement discipline is exemplary in
places most submissions in this area are not, and I could reproduce every reported value from
the released artifacts, which is rare.

What holds it back is that the paper is more conservative in its claim boundaries than in its
reporting boundaries. It refuses, correctly and repeatedly, to upgrade a system-level effect
into a claim about the model's own reasoning — and then withholds three of five arms from
Experiment 3, omits the 2×2's dominant interaction term, and says the model "detects" a broken
chain on data that cannot distinguish detection from default-fallback. Majors 1, 3, 4 and 5
are all fixable from data already on disk or with a single additional arm; Major 2 needs one
modest run. With those addressed I would expect to accept.

**Recommendation: major revision.**
