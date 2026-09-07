# Experimental Log

Three sealed experiments. All panels are hash-stamped before scoring; the answer
authority opens only once every receipt exists; receipts carry a SHA-256 of
their own contents. Audits are stdlib-only so verification never depends on the
environment resolving.

---

## 1. Experimental Setup

All three experiments run on the same task family and the same scoring method;
only the panel, the arms and the model set differ.

**Datasets.** Four named panels, all sealed and hash-stamped:

| Dataset | Items | Classes | Used by |
| --- | ---: | --- | --- |
| `binary_certificate_factorial_b14` | 192 | entailed / contradicted | b14 |
| `binary_certificate_factorial_b15` | 192 | entailed / contradicted | b15 |
| `multimodel_three_class_b16` | 192 | entailed / contradicted / undetermined | b16 |
| `ProofWriter OWA` (depths 0,1,2,3,5) | 23,240 questions | entailed / contradicted / unknown | closure-certifier validation only |

The three sealed panels are post-training procedurally generated with per-item
nonce vocabularies and are disjoint from one another. ProofWriter OWA is public
and is used **only** to validate the forward-closure certifier against an
independently labelled corpus; no ProofWriter item is scored by any model here.

## 2. Raw Numeric Data

Consolidated from `inputs/experiments/<slug>/results.json`. Every value quoted
anywhere in this log or in the paper appears here.

### Scale

| Quantity | Value |
| --- | ---: |
| Experiments | 3 |
| Models scored | 12 model-runs (1 + 1 + 10) |
| Scored prompts, total | 12,480 |
| b14 receipts | 960 |
| b15 receipts | 1,920 |
| b16 receipts | 9,600 |
| Receipt digest failures | 0 |
| Closure-certifier validation | 23,240 / 23,240 (100.00%) |

### b14 — per arm (of 192) and signal detection

| Arm | correct | d' | criterion c |
| --- | ---: | ---: | ---: |
| none | 91 | -0.255 | 1.166 |
| irrelevant | 96 | 0.000 | 1.293 |
| conclusion_only | 176 | 3.519 | 0.806 |
| proof_prefix | 167 | 3.200 | 0.965 |
| full | 191 | 4.723 | 0.204 |

Edges: +41.67pp, +36.98pp, +12.50pp, +7.81pp. Main effects: state +22.40pp,
answer +27.08pp. Diagonal (prespecified primary) -4.69pp, p = 0.078. Answer
value retained when state present: 30.0%. Always-`No` baseline: 96/192 = 50.0%.

### b15 — per arm (entailed subset, n = 96) and signal detection

| Arm | all /192 | entailed /96 | d' |
| --- | ---: | ---: | ---: |
| none | 96 | 0 | 0.000 |
| irrelevant | 96 | 0 | 0.000 |
| same_entity_irrelevant | 96 | 0 | 0.000 |
| truncate_3 | 96 | 0 | 0.000 |
| truncate_2 | 96 | 0 | 0.000 |
| truncate_1 | 155 | 59 | 2.853 |
| broken_chain | 97 | 1 | 0.407 |
| shuffled | 110 | 14 | 1.527 |
| misleading | 3 | 0 | -4.363 |
| full | 192 | 96 | 5.131 |

Primary: +60.4pp, p = 6.9e-18, BCa [+49.0, +68.8], d' drop +2.446. Decomposition:
total +61.5pp, surface +1.0pp (p = 1), validity +60.4pp, validity share 98.3%.
Qualification: 36/36 direct, 35/36 reordered, 35/36 agreement.

### b16 — balanced accuracy (%) per model, chance = 33.3

| Model | params (B) | none | full | min per-class recall | max label share |
| --- | ---: | ---: | ---: | ---: | ---: |
| qwen2.5-0.5b | 0.5 | 35.4 | 63.5 | 0.0 | 61.5 |
| olmo2-1b | 1.0 | 35.9 | 42.2 | 0.0 | 91.1 |
| llama3.2-1b | 1.2 | 33.9 | 37.0 | 0.0 | 95.3 |
| qwen2.5-1.5b | 1.5 | 33.3 | 37.0 | 0.0 | 96.4 |
| smollm2-1.7b | 1.7 | 33.3 | 69.3 | 37.5 | 44.8 |
| qwen2.5-3b | 3.0 | 41.1 | 90.6 | 71.9 | 42.7 |
| llama3.2-3b | 3.2 | 45.8 | 80.7 | 42.2 | 49.5 |
| phi-4-mini | 3.8 | 44.8 | 90.6 | 71.9 | 42.7 |
| gemma-3-4b | 4.3 | 63.5 | 96.4 | 89.1 | 36.5 |
| qwen2.5-7b | 7.6 | 33.3 | 71.4 | 14.1 | 62.0 |

Viable substrates: 3 of 10. Prespecified threshold passed 8 of 10 and was
invalid. Undetermined recall in `full`: gemma-3-4b 89.1%, phi-4-mini 100%.

---

## 3. Revision data (added 2026-09-04, in response to peer review)

Peer review identified that three of Experiment 3's five arms were run but not
reported, that the mechanism result rested on a single checkpoint, and that the
"detects a broken chain" claim was not separable from default-fallback. All
three were addressed with the data below. Two headline claims did not survive.

### 3.1 Experiment 3, all five arms, all ten models

Balanced accuracy (%), chance 33.3. `results/b16_analysis_v2_allarms.json`.

| Model | B | none | irrelevant | conclusion_only | proof_prefix | full | Viable in |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen2.5-0.5B | 0.5 | 35.4 | 34.9 | 41.1 | 43.2 | 63.5 | none |
| OLMo-2-1B | 1.0 | 35.9 | 33.3 | 53.6 | 34.9 | 42.2 | none |
| Llama-3.2-1B | 1.2 | 33.9 | 33.9 | 57.8 | 36.5 | 37.0 | none |
| Qwen2.5-1.5B | 1.5 | 33.3 | 33.3 | 43.2 | 34.9 | 37.0 | none |
| SmolLM2-1.7B | 1.7 | 33.3 | 33.3 | 45.3 | 39.6 | 69.3 | none |
| Qwen2.5-3B | 3.0 | 41.1 | 39.1 | **96.4** | 74.0 | 90.6 | conclusion_only, proof_prefix, full |
| Llama-3.2-3B | 3.2 | 45.8 | 43.2 | 67.2 | 55.2 | 80.7 | none |
| Phi-4-mini | 3.8 | 44.8 | 39.6 | 68.2 | 71.9 | 90.6 | full |
| Gemma-3-4B | 4.3 | 63.5 | 51.0 | **100.0** | 84.4 | 96.4 | conclusion_only, proof_prefix, full |
| Qwen2.5-7B | 7.6 | 33.3 | 33.3 | **97.9** | 67.2 | 71.4 | conclusion_only |

**Viability is a property of (model x arm), not of the model.** Qwen2.5-7B under
`conclusion_only` reaches 97.9% with minimum per-class recall 0.938 and maximum
label share 0.354 — it clears the corrected floor comfortably and is the
second-best model in the sweep. Under `full` the same model is 71.4% with minimum
per-class recall 0.141. Its contradicted-class recall falls from 0.938 to 0.141
**when the proof state is supplied**.

Viable under `full`: 3 of 10. Viable under `conclusion_only`: 3 of 10. Viable
under at least one arm: 4 of 10.

**Supplying proof state actively harms three models** — Gemma-3-4B, Qwen2.5-3B
and Qwen2.5-7B — measured as the drop in minimum per-class recall from
`conclusion_only` to `full`. Two of those three were the paper's "viable
substrates".

### 3.2 Ten-model replication of the 2x2

Experiment 3's five arms are Experiment 1's answer-evidence x proof-state 2x2
plus a baseline, on ten models, at no additional compute.

| Quantity | Value |
| --- | ---: |
| Mean state main effect | +8.7pp |
| Mean answer main effect | +21.6pp |
| Mean interaction | -15.9pp |
| `conclusion_only` > `proof_prefix` | 8 of 10 models |
| `conclusion_only` >= `full` | 6 of 10 models |

The mean state main effect of +8.7pp is well below Experiment 1's +22.4pp, so
that value is not typical of the model set.

### 3.3 Cross-model replication of the mechanism (b15 on three checkpoints)

`results/b15_replication_v1.json`. Entailed subset, n = 96.

| Checkpoint | irrelevant | broken_chain | truncate_1 | total | surface | validity | **share** |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen2.5-3B 4-bit | 0 | 1 | 59 | +61.5pp | +1.0pp | +60.4pp | **98.3%** |
| Qwen2.5-3B bf16 | 0 | 1 | 72 | +75.0pp | +1.0pp | +74.0pp | **98.6%** |
| Gemma-3-4B | 2 | **58** | 96 | +97.9pp | **+58.3pp** | +39.6pp | **40.4%** |

**The 98.3% validity share does not generalise.** Gemma-3-4B scores 58 of 96 on
`broken_chain` — it exploits surface overlap heavily — and its share is 40.4%.
Across three checkpoints the share ranges 40.4% to 98.6%.

Quantisation is the smaller effect: bf16 versus 4-bit on the same model moves the
magnitude (`truncate_1` 72 versus 59) but barely moves the share (98.6% versus
98.3%).

**The corruption result replicates without exception.** `misleading`, of 192:
3 (4-bit), 6 (bf16), **0** (Gemma-3-4B), with d' of -4.36, -4.06 and -5.13. The
strongest substrate in the sweep is the most completely misled.

### 3.4 Does the model detect a broken chain? No (b17)

`results/b17_analysis_v1.json`. b15's `broken_chain` items rescored with three
candidates on the 4-bit checkpoint. Theories, certificates and queries are
byte-identical to b15; only the instruction line and candidate set change.

| Arm | Yes | No | Unknown | Unknown rate |
| --- | ---: | ---: | ---: | ---: |
| `irrelevant` (baseline) | 0 | 48 | 144 | 75.0% |
| `broken_chain` | 1 | 110 | 81 | 42.2% |
| `truncate_1` | 61 | 110 | 21 | 10.9% |

A validity tracker should answer `Unknown` to `broken_chain`, whose displayed
lines are certified undetermined. Instead the Unknown rate **falls** to 42.2%
from a 75.0% baseline, -32.8pp — the opposite direction. And `No` is 110 of 192
under **both** `broken_chain` and `truncate_1`; the arms differ only in `Yes`
(1 versus 61).

The model completes a final inference when it can and falls back when it cannot.
**Detection is refuted, not merely unsupported.**

### 3.4a Refuted on all three checkpoints (b17 replication)

`results/b17_replication_v2.json`. Round 2 caught that the above was one
checkpoint while the Conclusion claimed "every checkpoint" — and that it was
missing on gemma-3-4b, the only model that answers broken chains correctly
(58/96) and therefore the only one where the two hypotheses visibly diverge.

| Checkpoint | `irrelevant` | `broken_chain` | Δ | `truncate_1` |
| --- | ---: | ---: | ---: | ---: |
| qwen2.5-3b 4-bit | 144 (75.0%) | 81 (42.2%) | **-32.8pp** | 21 (10.9%) |
| qwen2.5-3b bf16 | 108 (56.2%) | 34 (17.7%) | **-38.5pp** | 12 (6.2%) |
| gemma-3-4b | 15 (7.8%) | **0** (0.0%) | **-7.8pp** | 0 (0.0%) |

### 3.4b The abstention floor (b17b), and why it changed the reading

`results/b17_detection_both_baselines_v3.json`. Round 2, minor 11 asked whether
`irrelevant` is the right reference, since a record is present in that arm. A
`none` arm under the same instruction and candidates separates the instruction
effect from the record effect. 192 items x 3 checkpoints.

| Checkpoint | `none` | `irrelevant` | `irrel.` - `none` | Δ vs `none` | Δ vs `irrel.` |
| --- | ---: | ---: | ---: | ---: | ---: |
| qwen2.5-3b 4-bit | 153 (79.7%) | 144 (75.0%) | -4.7pp | -37.5pp | -32.8pp |
| qwen2.5-3b bf16 | 41 (21.4%) | 108 (56.2%) | **+34.9pp** | **-3.6pp** | -38.5pp |
| gemma-3-4b | 1 (0.5%) | 15 (7.8%) | +7.3pp | **-0.5pp** | -7.8pp |

`irrelevant` is near-neutral on the 4-bit checkpoint and inflates abstention by
34.9pp at bfloat16, so a Δ against it is **not comparable across checkpoints**.
The direction holds against both references everywhere, so the refutation does
not depend on the baseline — but two of the three Δ-vs-`none` values are near
zero, and gemma-3-4b's -0.5pp is a **no-power null** (it abstains on 1 of 192
with no record at all), not a refutation in its own right.

The composition carries the argument instead, and no baseline choice moves it:

| Evidence | Value |
| --- | --- |
| gemma-3-4b `Unknown` under `broken_chain` | **0 / 192** |
| gemma-3-4b `Yes` under `broken_chain` — completing a chain that does not connect | **76** |
| qwen 4-bit `No`, `broken_chain` vs `truncate_1` | **110 / 110** — identical |
| qwen 4-bit `Yes`, `broken_chain` vs `truncate_1` | 1 vs 61 |

**Second, unlooked-for result.** b17 moves only the instruction line and
candidate set on byte-identical inputs and the response distribution shifts
enormously — a prompt-format sensitivity result, recorded as a limitation in
§6.3 rather than claimed as a finding.

### 3.5 Uncertainty on the validity share

`results/b15_share_interval_v2.json`. Bootstrapping the whole ratio over paired
item resamples, rather than the numerator alone: validity share 98.3%, **95% BCa
[94.4, 100.0]**; surface component +1.0pp, 95% [+0.0, +3.1]pp.

`results/b15_share_baselines_v3.json`. Round 2: the share divides by the effect
measured against `irrelevant`, which coincides with `none` on both Qwen
checkpoints (both 0/96) and does not on gemma-3-4b, which answers **22 of 96**
entailed items unaided — **20 of those 22** also correct under `broken_chain`.

| Checkpoint | vs `irrelevant` | vs `none` |
| --- | ---: | ---: |
| qwen2.5-3b 4-bit | 98.3% | 98.3% |
| qwen2.5-3b bf16 | 98.6% | 98.6% |
| gemma-3-4b | **40.4%** | **51.4%** |

Both are reported and the "most of Gemma's effect is surface overlap" reading is
declined. The divergence appears exactly when a substrate has unaided competence,
and that is the finding rather than either number.

`results/b16_state_effect_v3.json`. The ten-model mean state effect averages over
four responders with minimum per-class recall 0.000 in *every* arm, three with
negative state effects. Excluding them: state **+14.7pp**, answer **+28.5pp**,
against b14's single-model +22.4pp — so "less than half" is withdrawn.

`results/receipt_census_v1.json`. Scored responses are counted from disk rather
than typed: **18,840 across 20 model-runs**. The composer substitutes the census
at build time.

### 3.6 Holm-adjusted p-values

Computed in the analysis files and to be printed wherever the paper prints a
p-value. b15 secondary family: 1.04e-17 (`truncate_2` - `truncate_1`), 1
(`truncate_3` - `truncate_2`), 1.36e-12 (`truncate_1` - `shuffled`). b14 edge
family: 6.62e-24, 4.53e-19, 2.38e-07, 6.10e-05.

### 3.7 The 2x2 interaction and its ceiling

`b14_posthoc_2x2_reanalysis_v1.json` records an interaction of **-29.2pp**,
larger in magnitude than either main effect and not previously reported. `full`
at 191/192 = 99.5% leaves only **13.0pp** of headroom above `proof_prefix`, so
both "other factor present" edges are compressed and the averaged main effects
are deflated. The ratio 12.50/41.67 = 30% is therefore substantially a
measurement of remaining headroom rather than of channel redundancy.

### 3.8 Certifier: adversarial and differential tests

`results/closure_adversarial_v1.json`. The ProofWriter agreement
(23,240/23,240) is a weaker check than "independent" implies: those labels are
themselves produced by forward chaining over the same fragment, so the agreement
partly measures one chainer agreeing with another. It catches coding bugs; it
does not probe the failure modes that matter and gives no coverage of the
generated nonce theories.

Nine adversarial cases now pass: cyclic rules saturate; a cycle that never
reaches the query stays undetermined; a 40-step chain beyond the default round
cap is still reached; derived negation; predicate absent; entity absent; a rule
fires only for the satisfying entity; a theory deriving an atom and its negation
is **rejected rather than labelled**; and exceeding the cap reports
`saturated = False` rather than a wrong answer.

Plus a **differential test on the generated panels** against an independently
written reference implementation — exhaustive ground instantiation over the
Herbrand base with a naive fixpoint, a deliberately different algorithm:
**192/192 and 192/192** three-way agreement between certifier, reference and
sealed authority.

### 3.9 Prior report

Experiment 1's per-arm counts (91/96/176/167/191) and its primary contrast
(-0.047, p = 0.078) were reported in an earlier unpublished report by the same
authors. This paper's 2x2 reading, the response-bias finding, and everything in
Experiments 2 and 3 are new. That earlier report concluded the 3B checkpoint
failed an open-world unknown gate; Experiment 3 finds the same model family
viable on the three-class panel. The panels, the candidate set and the
quantisation differ between the two, which plausibly accounts for it.

---

---

# Experiment b14 — five-arm certificate factorial, reanalysed as a 2x2

## Setup

Frozen `Qwen2.5-3B-Instruct-4bit` (MLX snapshot `4f83f8f1…`). 192 items, binary
derivable queries, post-training procedurally generated with per-item nonce
vocabularies. Scored by direct next-token likelihood over verified single-token
`Yes` / `No` candidates; no free-text generation. Five matched arms, every item
in every arm, changing only the solver record: `none`, `irrelevant` (a valid
same-shape donor-entity derivation), `conclusion_only` (the derived terminal
literal), `proof_prefix` (the chain with the terminal literal withheld), `full`.

Executed under a single persistent supervisor process. All five 192-item receipt
files were written before the answer authority was opened. One attempt; no
retries, prompt sweeps or panel substitutions were authorised.

## Results

| Arm | Correct / 192 |
| --- | ---: |
| `none` | 91 |
| `irrelevant` | 96 |
| `conclusion_only` | 176 |
| `proof_prefix` | 167 |
| `full` | 191 |

The prespecified primary contrast, `proof_prefix` − `conclusion_only`, was
−4.7pp with exact two-sided McNemar *p* = 0.078 — reported as a null.

**Post hoc reanalysis (labelled as such).** The five arms form a 2x2 of *answer
evidence* x *proof state*, with `none` outside it as a no-material baseline. The
prespecified primary is the **diagonal** of that square: it removes answer
evidence and adds proof state simultaneously, so its null attributes to neither
factor. The four one-factor **edges**:

| Edge | Effect | Exact McNemar *p* | Reported originally? |
| --- | ---: | ---: | --- |
| add answer, no state present | +41.67pp | 1.7e−24 | no |
| add state, no answer present | +36.98pp | 1.5e−19 | secondary |
| add answer, state present | +12.50pp | 1.2e−07 | no |
| add state, answer present | +7.81pp | 6.1e−05 | secondary |

**State main effect +22.4pp. Answer main effect +27.1pp.** The answer literal
retains only 30% of its value once state is present.

**The baseline was misdescribed.** Splitting by class, the model answers `No` to
88% of items. Signal detection over the binary panel:

| Arm | hits /96 | false alarms /96 | d' | criterion c |
| --- | ---: | ---: | ---: | ---: |
| `none` | 9 | 14 | −0.26 | +1.17 |
| `irrelevant` | 9 | 9 | **0.00** | +1.29 |
| `conclusion_only` | 80 | 0 | +3.52 | +0.81 |
| `proof_prefix` | 71 | 0 | +3.20 | +0.97 |
| `full` | 95 | 0 | +4.72 | +0.20 |

`irrelevant` scored 50.0% — apparent chance — with an identical 9/96 `Yes` rate
in both classes, i.e. **zero discriminative sensitivity**. A trivial always-`No`
strategy scores 96/192; `none` scored 91 and `irrelevant` 96, at or below it.

The contradicted class sits at ceiling in every certificate arm and contributed
**0 of the 21 discordant pairs** in the primary contrast. Effective n was 96.

## Baselines

`none` (no solver material) and `irrelevant` (valid proof, wrong entity) are the
two baseline arms. Both return d' ≈ 0. The trivial always-one-label strategy
(96/192 = 50.0%) is the reference against which arm accuracy must be judged.

## Figures

`b14/figures/factorial_2x2.png` — the four cells with all four one-factor edges
and the prespecified diagonal, values read from `results.json`.

## Notes & Limitations

The reanalysis is **post hoc** and must be labelled so; it does not reopen or
re-run the sealed experiment. Every number is re-derived from the 960 raw
receipts by `reanalyse_…_posthoc_v1.py`, which reconstructs the answer key from
the class token in each `task_id` and hard-asserts that the reconstruction
reproduces all five published per-arm counts before reporting.

The original protocol prespecified a 15pp primary effect while its comparison
arm reached 91.7%, leaving 8.3pp of headroom — the target was arithmetically
unreachable. b14 recorded no proof depth and so cannot stratify its failures.
Task ids encoded the semantic class, so the authority was reconstructible from
the public panel.

## Decisions

- Read the factorial as a 2x2 and report the edges; demote the diagonal to a
  footnote carrying the headroom arithmetic.
- Report d' and criterion alongside accuracy everywhere, because accuracy on a
  balanced panel with a biased responder is uninterpretable.
- Do not re-run: the reanalysis is a different reading of sealed data.

---

# Experiment b15 — validity versus surface overlap

## Setup

Same model, **byte-identical weights** — pinned to `4f83f8f1…`, the exact
snapshot recorded in the frozen b14 runner, verified still to resolve and to
equal the repo head — so b14's anchors carry over without a weights caveat.

192 fresh items (96 entailed / 96 contradicted), depth 4 by construction,
per-item nonce vocabulary, disjoint from every prior panel. **Ten matched arms.**
The full theory is visible in every arm; only the solver record changes.

| Arm | Solver record | lines | query-entity mentions | query predicate |
| --- | --- | ---: | ---: | :---: |
| `none` | nothing | 0 | 0 | — |
| `irrelevant` | valid donor-entity chain | 8 | **0** | no |
| `same_entity_irrelevant` | valid chain about the **query entity** toward an unrelated predicate | 8 | **4** | no |
| `truncate_3` | chain cut three steps short | 4 | 2 | no |
| `truncate_2` | chain cut two steps short | 6 | 3 | no |
| `truncate_1` | chain with the terminal literal withheld (= b14's `proof_prefix`) | 8 | **4** | yes |
| `broken_chain` | surface-matched, logically invalid | 8 | **4** | yes |
| `misleading` | valid-looking chain with a fabricated final rule establishing the negation | 9 | 5 | yes |
| `shuffled` | `truncate_1`'s lines in seeded random order | 8 | **4** | yes |
| `full` | complete chain including the terminal literal | 9 | 5 | yes |

**`broken_chain` construction.** One intermediate link is cut so the displayed
lines no longer reach the query, while every surface property is preserved:
subject occurrence count matched to `truncate_1` and audited per item, query
predicate still present in the final rule, identical line count and
fact/rule/literal type sequence, token length matched within tolerance. Every
*rule* shown is a real theory rule; exactly one derived literal is false.
Certified on all 192 items by forward-closure saturation to leave the query
**undetermined**.

Shape partners are enforced pairwise: `broken_chain`, `same_entity_irrelevant`
and `shuffled` against `truncate_1`; `misleading` against `full`.

The primary contrast is evaluated on the **entailed subset (n = 96)**, declared
before the run, because b14 showed the contradicted class contributes no
discordance. A validity claim additionally requires a same-sign d' drop; an arm
that moves accuracy while leaving d' unchanged has moved criterion, not
sensitivity, and is reported as a bias result.

Delivery qualification was run as a recorded smoke check, not a blocking gate:
36/36 direct, 35/36 reordered, 35/36 agreement — a replication of b14's 36/36 /
33/36 on the same weights.

## Results

1,920 receipts, 0 digest failures, coverage exact.

| Arm | all /192 | entailed /96 | d' | criterion c |
| --- | ---: | ---: | ---: | ---: |
| `none` | 96 | 0 | 0.000 | 2.565 |
| `irrelevant` | 96 | 0 | 0.000 | 2.565 |
| `same_entity_irrelevant` | 96 | 0 | 0.000 | 2.565 |
| `truncate_3` | 96 | 0 | 0.000 | 2.565 |
| `truncate_2` | 96 | 0 | 0.000 | 2.565 |
| **`truncate_1`** | 155 | **59** | **2.853** | 1.139 |
| `broken_chain` | 97 | 1 | 0.407 | 2.362 |
| `shuffled` | 110 | 14 | 1.527 | 1.802 |
| `misleading` | **3** | 0 | **−4.363** | 0.384 |
| `full` | 192 | 96 | 5.131 | 0.000 |

**Primary — `truncate_1` − `broken_chain`, entailed subset.** Paired table: 1
both correct, 58 `truncate_1`-only, 0 `broken_chain`-only, 37 neither.
**+60.4pp, exact two-sided McNemar *p* = 6.9e−18**, seeded 95% paired BCa
[+49.0, +68.8]. **d' drop +2.446** — the same-sign requirement is met.

**Decomposition (entailed):**

| Component | Effect |
| --- | ---: |
| total state effect (`truncate_1` − `irrelevant`) | +61.5pp |
| **surface component** (`broken_chain` − `irrelevant`) | **+1.0pp**, *p* = 1 |
| **validity component** (`truncate_1` − `broken_chain`) | **+60.4pp** |
| **validity share** | **98.3%** |

**Supporting contrasts (entailed):**

| Contrast | Effect | *p* |
| --- | ---: | ---: |
| `same_entity_irrelevant` − `irrelevant` (entity repetition) | **+0.0pp** | 1 |
| `truncate_1` − `shuffled` (line order) | +46.9pp | 6.8e−13 |
| `truncate_2` − `truncate_1` (one step deeper) | **−61.5pp** | 3.5e−18 |
| `truncate_3` − `truncate_2` | +0.0pp | 1 |
| `misleading` − `full` | **−100.0pp** | 2.5e−29 |

Five arms — `none`, `irrelevant`, `same_entity_irrelevant`, `truncate_3`,
`truncate_2` — return **identical** results: 96/192, 0/96 entailed, d' = 0.000,
c = 2.565. Behaviour is binary: either the supplied chain reaches one step from
the answer, or the model is blind.

## Baselines

`irrelevant` is the lower anchor (0/96 entailed, d' = 0.000); `truncate_1` the
upper anchor (59/96, d' = 2.853). Both replicate b14's corresponding arms on a
fresh panel with the same weights. `full` (96/96) is the ceiling and the
panel-difficulty check against b14.

## Figures

`b15/figures/arms.png` — twin panels, entailed accuracy and d' per arm, sharing
arm order, with the decomposition beneath. Values read from `results.json`.

## Notes & Limitations

One model, one task family, and an inference depth of exactly one step — the
depth result is a hard bound on how the mechanism finding may be described.

The full theory is visible in every arm, so the query remains derivable from the
theory regardless of certificate. Breaking a certificate is diagnostic only
because the model scores 0/96 working from the theory alone. A model using the
broken certificate as a pointer back into the theory would be performing
inference of a different kind; this is an interpretation caveat, not a
controlled alternative.

`truncate_2` and `truncate_3` drop the query predicate out of the certificate
entirely — it lives in the final rule — so the depth ladder confounds depth with
predicate presence and must be read against `same_entity_irrelevant`.

A tenth arm, `full`, was added before any data collection as a ceiling and
comparability anchor; recorded in the seal.

## Decisions

- Primary on the entailed subset only, declared in advance.
- Require a same-sign d' drop for any validity claim.
- Detection target 15pp against a ~65pp expressible range — the b14 headroom
  error is not repeated.
- Every contrast moves exactly one factor; no diagonals.
- 4-bit, pinned to b14's exact snapshot, so anchors transfer without caveat.
- `conclusion_only` omitted: b14 already measured the answer channel.
- Qualification demoted to a smoke check — b14 passed this screen on these
  weights, and a direct-fact screen was shown to pass models that are degenerate
  on the real task.

---

# Experiment b16 — ten models, three classes

## Setup

192 items balanced 64 entailed / 64 contradicted / 64 **undetermined**, depth 4,
per-item nonce vocabulary. Undetermined items are made by withholding a
chain-closing rule and then certifying by forward-closure saturation that
neither the query nor its negation appears in the closure — formally
underdetermined, not merely hard. Three response candidates `Yes` / `No` /
`Unknown`, direct likelihood scoring.

**Closure certifier validated first**, against ProofWriter's open-world test
splits at depths 0, 1, 2, 3 and 5 — an independent corpus labelled by a
different implementation: **23,240 / 23,240 questions, 100.00%**, zero unusable
theories, perfectly diagonal confusion, including 10,440 undetermined. No item
enters the panel without a certification record.

**Five arms** as in b14. For undetermined items, `conclusion_only` states that
neither polarity is derivable, `proof_prefix` gives closure coverage with the
saturation status withheld, and `full` adds that status.

**Ten models**, streamed one at a time: download a pinned revision, record the
weight manifest **before deleting anything**, score all arms, write receipts and
a completion marker, delete. Peak disk is one model. Resumable by completion
marker. bf16 throughout, so precision is not confounded with model identity.

**Deliberate protocol change: no gate blocks the run.** Under a
reasoning-substitute framing, delivery *is* the capability under test, so a model
that cannot emit a verdict reliably is a finding about substrate viability, not
a reason to exclude it. All ten models scored the full panel. Tooling failures
(tokeniser incompatible, will not load) would be excluded and are not findings —
the eligibility screen found none: 10/10 load, prefill, and tokenise all three
candidates as single distinct tokens.

## Results

10/10 models, 50/50 receipt files, 9,600 receipts, 0 digest failures.

**The prespecified threshold was invalid.** Declared in advance: ≥80%
undetermined recall in `full` means the model relays non-determination. **8 of 10
passed.** But it is a single-class recall measure, and a model answering
`Unknown` to everything maxes it while discriminating nothing — four models do
exactly that (62–96% `Unknown`; three never emit `No` at all). This is b14's
`No`-bias trap, mirrored. **Replaced post hoc** by **minimum per-class recall ≥
0.50**, a floor on every class that collapse cannot game.

| Model | B | none | full | min recall | max label share | corrected verdict |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| qwen2.5-0.5b | 0.5 | 35.4 | 63.5 | 0.0 | 61.5 | collapsed |
| olmo2-1b | 1.0 | 35.9 | 42.2 | 0.0 | 91.1 | collapsed |
| llama3.2-1b | 1.2 | 33.9 | 37.0 | 0.0 | 95.3 | collapsed |
| qwen2.5-1.5b | 1.5 | 33.3 | 37.0 | 0.0 | 96.4 | collapsed |
| smollm2-1.7b | 1.7 | 33.3 | 69.3 | 37.5 | 44.8 | below floor |
| **qwen2.5-3b** | 3.0 | 41.1 | **90.6** | 71.9 | 42.7 | **viable** |
| llama3.2-3b | 3.2 | 45.8 | 80.7 | 42.2 | 49.5 | below floor |
| **phi-4-mini** | 3.8 | 44.8 | **90.6** | 71.9 | 42.7 | **viable** |
| **gemma-3-4b** | 4.3 | 63.5 | **96.4** | 89.1 | 36.5 | **viable** |
| qwen2.5-7b | 7.6 | 33.3 | 71.4 | 14.1 | 62.0 | collapsed |

Balanced accuracy, %. Chance = 33.3. **Viable substrates: 3 of 10.**

Supplying full solver material takes viable models from at or near chance to
80–96% balanced accuracy on a three-class task that includes abstention.

An earlier three-class screen had found 0/12 on unknown and framed it as
possibly architecture-level. **It does not generalise**: gemma-3-4b reaches 89.1%
and phi-4-mini 100% undetermined recall.

## Baselines

`none` per model is the substrate's floor and the competence measurement.
Chance balanced accuracy is 33.3% on the three-class panel; the always-one-label
strategy also scores exactly 33.3% balanced accuracy, which plain accuracy would
hide.

## Figures

`b16/figures/size_curve.png` — dumbbells from `none` to `full` per model,
ordered by parameter count, coloured by viability, with the chance line marked.
Values read from `results.json`.

## Notes & Limitations

Model is not a randomised factor; between-model comparisons are **descriptive**,
reported as a size curve, never as a significance claim about scale.

An undetermined `proof_prefix` cannot contain the query predicate — the solver
has nothing about it — while entailed and contradicted prefixes do. Undetermined
items therefore offer fewer surface cues, and a surface-matching model will look
worse there for reasons unrelated to abstention. Per-arm entity-mention counts
are recorded so this is analysable rather than discovered later.

The replacement criterion is post hoc. Both verdicts are retained in the results
file; the invalid one is not deleted.

## Decisions

- Merge substrate viability and non-determination into one panel; class
  stratification separates the questions in analysis.
- No gate blocks the run; the `none` arm is the competence measurement.
- Separate tooling failure from behavioural failure, declared before the screen.
- Balanced accuracy as the headline scalar, not accuracy.
- Opaque task ids: the class lives only in the authority file, unlike b14.
- Depth fixed and recorded per item, so failures can be stratified.
- 192 items rather than 288 — 0.91 power at 20pp, and the expected effect was
  large.
