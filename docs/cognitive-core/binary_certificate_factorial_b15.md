# b15: validity vs surface overlap

**Question.** Of b14's +37pp proof-state effect, how much is tracking logical
**validity** and how much is **surface overlap** between certificate and query?

**Method.** Hold surface form fixed. Destroy validity alone.

**Status.** Panel sealed 2026-09-03. Runner not built. Single model.

---

## Why b15 exists

b14's `proof_prefix` withholds the answer but still contains the query subject
(4x) and the query predicate. A model that only checks word co-occurrence
reproduces every b14 number. b14 has no arm that separates the two accounts.

---

## Decision log

| # | Decision | Reason |
| --- | --- | --- |
| 1 | Primary contrast on **entailed items only** (n=96) | b14 receipts: contradicted items are at ceiling in every certificate arm and contributed **0 of 21** discordant pairs. Including them dilutes without adding information |
| 2 | Require a **same-sign d' drop**, not just accuracy | b14's `irrelevant` arm scored 50.0% with **d' = 0.00**. Accuracy on a balanced panel hides a biased responder |
| 3 | Detection target **15pp**, not 15pp-of-anything | b14 prespecified 15pp when its comparison arm left only 8.3pp of headroom. Here the range is ~65pp |
| 4 | Every contrast moves **one factor** | b14's primary was the 2x2 diagonal: it removed answer evidence and added state simultaneously, so its null attributed to neither |
| 5 | Added `full` (10th arm), 2026-09-03 | b14 put `full` (99.5%) far above `proof_prefix` (87.0%). Without it b15 has no ceiling and no difficulty check against b14 |
| 6 | **4-bit**, not bf16 | b15 rests on b14's 50.0%/87.0% anchors. Pinned to `4f83f8f1...`, the exact b14 snapshot -- **byte-identical weights**, verified 2026-09-03 |
| 7 | **No** `conclusion_only` arm | b14 already measured the answer channel. b15 interrogates the state channel |
| 8 | Qualification **demoted to a smoke check** | b14 passed this exact screen on these exact weights; b16 showed a direct-fact screen passes models that are degenerate on the real task |

---

## Ten arms

| Arm | Material | Added because |
| --- | --- | --- |
| `none` | nothing | b14 anchor |
| `irrelevant` | valid donor-entity chain | b14 anchor (lower) |
| `truncate_1` | chain, terminal literal omitted | b14's `proof_prefix`, renamed |
| `truncate_2` | last 2 literals omitted | b14 deleted only **one** line -- no dynamic range |
| `truncate_3` | last 3 literals omitted | same |
| `same_entity_irrelevant` | valid chain about the query entity, unrelated predicate | b14 confounded relevance with **entity repetition** (0x vs 4x) |
| **`broken_chain`** | surface-matched, logically invalid | **primary.** The arm that decides validity vs overlap |
| `misleading` | valid-looking chain to the **negation** | nothing tested corrupted solver output |
| `shuffled` | `truncate_1` lines, seeded reorder | chains are order-dependent, bags of words are not |
| `full` | complete chain | ceiling + b14 comparability |

Arm counts: v7 = 3, b14 = 5, the 2x2 read of b14 = 4 of those 5, b15 = 10.

---

## Worked example (a real sealed item)

Subject `Daelkruth`. Chain `vrakaeth -> vremmei -> pothli -> zaelbrom -> gakaem`.
**Query: `Daelkruth is gakaem.` Answer: Yes.**

Write the chain as `p0 -> p1 -> p2 -> p3 -> p4`, so the query asks about `p4`.

| Arm | What the model sees after "Solver record:" |
| --- | --- |
| `none` | *(nothing)* |
| `truncate_3` | `X is p0.` `All p0 are p1.` `X is p1.` `All p1 are p2.` |
| `truncate_2` | ... + `X is p2.` `All p2 are p3.` |
| `truncate_1` | ... + `X is p3.` `All p3 are p4.`  <- ends on the rule; **p4 named, literal withheld** |
| `full` | ... + `X is p4.` |
| `irrelevant` | same shape, **different entity**: `Brourvou is bidres. All bidres are tethgloul. ...` |
| `same_entity_irrelevant` | same entity, **different chain**: `Daelkruth is laergae. All laergae are razi. ...` -- p4 never appears |
| `broken_chain` | `truncate_1` with one link cut, see below |
| `misleading` | `truncate_1` + a **fabricated** rule flipping polarity + `X is not p4.` |
| `shuffled` | `truncate_1`'s eight lines in seeded random order |

**The two comparisons that carry the experiment:**

`truncate_1` (valid)
> Daelkruth is vrakaeth. All vrakaeth people are vremmei. Daelkruth is vremmei.
> All vremmei people are pothli. Daelkruth is pothli. **All pothli people are
> zaelbrom. Daelkruth is zaelbrom.** All zaelbrom people are gakaem.

`broken_chain` (invalid, everything else identical)
> Daelkruth is vrakaeth. All vrakaeth people are vremmei. Daelkruth is vremmei.
> All vremmei people are pothli. Daelkruth is pothli. **All lordrum people are
> ruthbeis. Daelkruth is ruthbeis.** All zaelbrom people are gakaem.

Only the bolded pair changes. `zaelbrom` is never established, so the final rule
cannot fire -- yet `Daelkruth` still appears 4x, `gakaem` still appears, the line
count and line types are identical, and every rule shown is a real theory rule.
The single false line is `Daelkruth is ruthbeis`.

`misleading` (valid-looking, points the wrong way)
> ... Daelkruth is zaelbrom. **All zaelbrom people are not gakaem. Daelkruth is
> not gakaem.**

Correct answer is still Yes. Follow the supplied state and you answer No.

`same_entity_irrelevant` vs `irrelevant` -- both valid, both lack `gakaem`, and
they differ **only** in whether the subject is the query entity:

| | subject mentions |
| --- | ---: |
| `irrelevant` (Brourvou) | 0 |
| `same_entity_irrelevant` (Daelkruth) | 4 |

---

## Sealed panel

`data/cognitive_core/binary_certificate_factorial_b15/`
seal_id `e2bcbc4a2331806cfb7a5a4abda890a18af714901497977cf1fedc7353f32db7`

192 items | 96 entailed + 96 contradicted | depth 4 | per-item nonce vocabulary

**Invariants, verified on all 192 items after sealing:**

| Arm | lines | subject mentions | query predicate |
| --- | ---: | ---: | ---: |
| `irrelevant` | 8 | **0** | 0/192 |
| `same_entity_irrelevant` | 8 | **4** | 0/192 |
| `truncate_3` | 4 | 2 | 0/192 |
| `truncate_2` | 6 | 3 | 0/192 |
| `truncate_1` | 8 | **4** | 192/192 |
| `broken_chain` | 8 | **4** | 192/192 |
| `misleading` | 9 | 5 | 192/192 |
| `shuffled` | 8 | **4** | 192/192 |
| `full` | 9 | 5 | 192/192 |

That table is the design:

- `irrelevant` vs `same_entity_irrelevant` -- differ **only** in entity repetition.
- `truncate_1` vs `broken_chain` -- differ **only** in whether the logic connects.
- `truncate_2`/`truncate_3` drop the query predicate entirely, so the ladder
  confounds depth with predicate presence. Read it against
  `same_entity_irrelevant`, never alone.

Shape partners enforced pairwise: `broken_chain`, `same_entity_irrelevant`,
`shuffled` -> `truncate_1`; `misleading` -> `full`.

---

## `broken_chain` construction

Break one link so the shown lines no longer reach the query, while preserving
every surface property.

| Preserved | Destroyed |
| --- | --- |
| subject count == `truncate_1` (audited per item) | the chain no longer connects |
| query predicate present in the final rule | one shown literal is false |
| line count and fact/rule/literal sequence | |
| every shown **rule** is a real theory rule | |

Certified on all 192 items: the displayed lines leave the query
**undetermined** under `cc_instruments.closure`.

**Caveat.** The full theory is visible in every arm, so the query stays derivable
from the theory regardless of certificate. Breaking the certificate is
diagnostic only because b14 established the model is at chance unaided. A model
using the broken certificate as a pointer back into the theory would be doing
inference of a different kind -- an interpretation caveat, not a control.

---

## Analysis

**Decomposition**

| Quantity | Contrast |
| --- | --- |
| total state effect | `truncate_1` - `irrelevant` (b14: +37.0pp) |
| surface component | `broken_chain` - `irrelevant` |
| **validity component** | **`truncate_1` - `broken_chain`** (primary) |

Reported per contrast: complete 2x2 paired table, exact two-sided McNemar (the
decision criterion), seeded 100,000-resample paired BCa. Validity share with a
bootstrap interval. d' and criterion per arm.

**Secondary, Holm-adjusted:** `truncate_1` - `shuffled`; `truncate_2` -
`truncate_1`; `truncate_3` - `truncate_2`.

**Prespecified verdicts**

| `broken_chain` lands | Verdict |
| --- | --- |
| within 5pp of `truncate_1`, primary ns | **surface overlap dominant** -- b14's effect is not inference |
| within 5pp of `irrelevant` | **validity tracking dominant** -- b14's effect is inference |
| between | **mixed** -- the validity share is the result |
| >5pp above `truncate_1` | construction fault; terminal |
| accuracy moves, d' does not | **criterion shift, not sensitivity** -- a bias result |

**Power.** n=96 entailed: 0.86 at 15pp, ~1.00 at 20pp, 0.58 at 10pp. Declared
target **15pp**; below that is indeterminate, not null. Range available ~65pp
(`irrelevant` 9.4% to `truncate_1` 74.0% within the entailed class).

---

## Execution

One persistent local supervisor process, stdout/stderr under the run directory.

**Qualification is a recorded smoke check, not a blocking gate** (decision 8).
36 depth-0 items, `direct` and `reordered` templates, 18 Yes / 18 No, separate
RNG stream so the prospective panel is bit-identical. Thresholds are still
computed and recorded (>=27/36 per template, >=12/18 per class, >=32/36
agreement); `--require-qualification` restores blocking behaviour.

Rationale: b14 ran this exact screen on these exact weights and passed (36/36,
33/36), and b16 established that a direct-fact screen says nothing about task
competence -- it passed 36/36 while the model was degenerate on the real panel.
Its value here is verifying the runtime path and preserving b14 comparability.

All ten receipt files must exist before the authority opens.
No retries, sweeps, substitutions, or automatic successors.

~1,920 prompts, ~30 min.

---

## Results (2026-09-03)

1,920 receipts, 0 digest failures, coverage exact. Qualification 36/36 direct,
35/36 reordered, 35/36 agreement -- a replication of b14's 36/36 / 33/36 on
byte-identical weights. `results/b15_analysis_v1.json`.

| Arm | all | entailed | d' | criterion c |
| --- | ---: | ---: | ---: | ---: |
| `none` | 96/192 | 0/96 | 0.000 | 2.565 |
| `irrelevant` | 96/192 | 0/96 | 0.000 | 2.565 |
| `same_entity_irrelevant` | 96/192 | 0/96 | 0.000 | 2.565 |
| `truncate_3` | 96/192 | 0/96 | 0.000 | 2.565 |
| `truncate_2` | 96/192 | 0/96 | 0.000 | 2.565 |
| **`truncate_1`** | 155/192 | **59/96** | **2.853** | 1.139 |
| `broken_chain` | 97/192 | 1/96 | 0.407 | 2.362 |
| `shuffled` | 110/192 | 14/96 | 1.527 | 1.802 |
| `misleading` | **3/192** | 0/96 | **-4.363** | 0.384 |
| `full` | 192/192 | 96/96 | 5.131 | 0.000 |

### Primary: `truncate_1` - `broken_chain` (entailed, n=96)

Paired table: 1 both, **58 truncate_1-only**, 0 broken_chain-only, 37 neither.
**RD +60.4pp, exact McNemar p = 6.9e-18**, BCa [+49.0, +68.8].
**d' drop +2.446** -- the required same-sign sensitivity drop holds.

### Decomposition

| Component | |
| --- | ---: |
| total state effect | +61.5pp |
| surface component | **+1.0pp** (p = 1) |
| **validity component** | **+60.4pp** |
| **validity share** | **98.3%** |

**VERDICT: validity tracking dominant.**

### Supporting contrasts (entailed)

| Contrast | Effect | p |
| --- | ---: | ---: |
| `same_entity_irrelevant` - `irrelevant` (entity repetition) | **+0.0pp** | 1 |
| `broken_chain` - `irrelevant` (surface overlap) | +1.0pp | 1 |
| `truncate_1` - `shuffled` (order) | +46.9pp | 6.8e-13 |
| `truncate_2` - `truncate_1` (one step deeper) | **-61.5pp** | 3.5e-18 |
| `truncate_3` - `truncate_2` | +0.0pp | 1 |
| `misleading` - `full` | **-100.0pp** | 2.5e-29 |

### Four findings

| # | Finding |
| --- | --- |
| 1 | **b14's state effect is validity tracking, not word matching.** 98.3% of it survives when surface form is held fixed and only the logic is broken. The surface component is +1.0pp, indistinguishable from zero |
| 2 | **Entity repetition explains nothing.** Mentioning the query entity 4x in a valid but irrelevant chain gives **0/96** -- identical to mentioning it 0x. The repetition confound is cleanly refuted |
| 3 | **Inference depth is exactly one step.** `truncate_2` scores 0/96, identical to `none`. The model completes the final step and cannot chain two. This is a cliff, not a slope |
| 4 | **The model follows corrupted solver output almost without exception.** `misleading` scores 3/192 with **d' = -4.363**. Handed a valid-looking certificate pointing the wrong way, it answers wrong 189 times out of 192 |

Five arms -- `none`, `irrelevant`, `same_entity_irrelevant`, `truncate_3`,
`truncate_2` -- return **identical** results: 96/192, 0/96 entailed, d' = 0.000,
c = 2.565. The model answers `No` to everything. Behaviour is binary: either the
supplied chain reaches one step from the answer, or the model is blind.

Finding 4 is the safety-critical one for the reasoning-substitute architecture.
Validity tracking is real but shallow, and it confers **no resistance** to a
corrupted apparatus.

---

## Interpretation

| Outcome | Means |
| --- | --- |
| Surface overlap dominant | b14's state effect is lexical. A substantive negative mechanism result, and a direct warning to any tool- or solver-augmented system inferring reasoning from accuracy gains |
| Validity tracking dominant | The frozen 3B tracks derivation validity in this envelope. Limited, system-level. Not repair, which stays untested |
| Mixed | Report the validity share; the ladder characterises how far the model carries a chain |

In all cases: system-level effects are not upgraded to mechanism claims, and high
accuracy with `full` material describes a faithful transcriber, not a reasoner.
