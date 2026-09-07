# b17 / b17b: does the model detect a broken chain, or fail to complete one?

**One question the binary design could not answer.**

| | |
| --- | --- |
| Question | Under a broken certificate, does the model *recognise* the break, or merely fail to find a pattern to complete? |
| Why b15 cannot say | On a binary panel both predict the **same response**. The correct answer under a broken certificate *is* the model's default label |
| Discriminating move | Rescore the same items with a third candidate, `Unknown` |
| Status | b17 sealed and run on 3 checkpoints 2026-09-04/07; b17b (`none` arm) run on the same 3 on 2026-09-07 |
| Verdict | **Detection refuted** on every checkpoint, against both abstention baselines |

---

## Why it needed its own experiment

b15 reported a $98.3\%$ validity share and the natural reading was that the model
tracks whether a supplied derivation connects. Peer review, round 1, major 4
pointed out that the binary design cannot support that reading: every
non-completable b15 arm lands on the identical point ($96/192$, $0/96$ entailed,
$d' = 0.000$, $c = 2.565$), which both hypotheses predict.

| Hypothesis | Predicts under `broken_chain`, three candidates |
| --- | --- |
| Validity tracker | `Unknown` — the displayed lines do not settle the query |
| Pattern completer | its default label — nothing changed for it |

The b15 `broken_chain` items are already certified **undetermined** under their
displayed lines, so a third candidate is the correct scoring of them.

---

## Design

Panel derived from b15 with **only** the instruction line and candidate set
changed. Theories, certificates and queries are byte-identical; the change is
recorded in the seal.

| | b15 | b17 |
| --- | --- | --- |
| Instruction | `... Answer exactly Yes or No.` | `... Answer exactly Yes, No, or Unknown.` |
| Candidates | `Yes`, `No` | `Yes`, `No`, `Unknown` |
| Arms | ten | `irrelevant`, `broken_chain`, `truncate_1` |

`truncate_1` is the positive control: a completable chain should still yield
`Yes`. `irrelevant` fixes the default under three candidates.

**b17b** adds a fourth arm, `none`, under the same instruction and candidates.

---

## Decision log

| # | Decision | Reason |
| --- | --- | --- |
| 1 | Derive from b15 rather than generate a new panel | The claim under test is about *those* items. A new panel would confound the question with item variation |
| 2 | Assert the b15 prompt prefix before swapping it | If the b15 prompt shape ever changed, a silent mis-splice would produce a plausible but wrong panel |
| 3 | Task ids `b15-` → `b17-` | Same items, different experiment; the ids must not collide in a shared results tree |
| 4 | No `displayed_lines_verdict` in the b17b authority | No certificate is displayed in a `none` arm, so there is nothing to certify |
| 5 | b17b as a **new script**, not an edit to the b17 runner | The b17 runner is frozen and hash-recorded. Repo norm: add a version, never edit a completed one |
| 6 | Run all three b15 checkpoints, not just the primary | Round 2 caught that a single-checkpoint refutation was being described as holding "on every checkpoint" — and that it was missing on gemma-3-4b, the one model that answers broken chains correctly (58/96) and therefore the only one where the two hypotheses visibly diverge |

---

## Results

### b17 — three checkpoints, `irrelevant` baseline

`Unknown` responses of 192 per arm.

| Checkpoint | `irrelevant` | `broken_chain` | Δ | `truncate_1` |
| --- | ---: | ---: | ---: | ---: |
| qwen2.5-3b 4-bit | 144 (75.0%) | 81 (42.2%) | **−32.8pp** | 21 (10.9%) |
| qwen2.5-3b bf16 | 108 (56.2%) | 34 (17.7%) | **−38.5pp** | 12 (6.2%) |
| gemma-3-4b | 15 (7.8%) | **0** (0.0%) | **−7.8pp** | 0 (0.0%) |

Detection predicts a **rise**. Every checkpoint falls.

### b17b — the `none` arm, and why it mattered

Round 2, minor 11 asked whether `irrelevant` is the right reference, since a
record is present in that arm. It conflates two causes of the baseline rate: the
three-candidate instruction itself, and the presence of a query-irrelevant
record. `none` separates them.

| Checkpoint | `none` | `irrelevant` | `irrelevant` − `none` | Δ vs `none` | Δ vs `irrelevant` |
| --- | ---: | ---: | ---: | ---: | ---: |
| qwen2.5-3b 4-bit | 153 (79.7%) | 144 (75.0%) | −4.7pp | −37.5pp | −32.8pp |
| qwen2.5-3b bf16 | 41 (21.4%) | 108 (56.2%) | **+34.9pp** | **−3.6pp** | −38.5pp |
| gemma-3-4b | 1 (0.5%) | 15 (7.8%) | +7.3pp | **−0.5pp** | −7.8pp |

**The reviewer was right to ask.** `irrelevant` is near-neutral on the 4-bit
checkpoint and inflates abstention by 34.9pp at bfloat16, so a Δ measured
against it is **not comparable across checkpoints**. Against the conservative
reference two of the three falls are small.

### What the refutation actually rests on

The direction holds against both references on all three checkpoints, so the
refutation does not depend on the baseline. But two of the three Δ-vs-`none`
values are near zero, and on gemma-3-4b — which abstains on 1 of 192 with no
record at all — the −0.5pp is a **no-power null, not a refutation**. The delta
cannot carry the argument there.

The response *composition* can, and it is immune to baseline choice:

| Evidence | Value |
| --- | --- |
| gemma-3-4b `Unknown` under `broken_chain` | **0 / 192** |
| gemma-3-4b `Yes` under `broken_chain` — completing a chain that does not connect | **76** |
| qwen 4-bit `No` under `broken_chain` vs `truncate_1` | **110 / 110** — identical |
| qwen 4-bit `Yes` under `broken_chain` vs `truncate_1` | 1 vs 61 — the only thing separating the arms |

The model completes when it can and falls back when it cannot. It is not sorting
certificates into valid and invalid.

---

## A second result, unlooked-for

b17 changes only the instruction line and candidate set on byte-identical
theories and certificates, and the response distribution moves enormously. That
is a **prompt-format sensitivity** result as much as a detection result, and it
is consistent with the prompt- and option-order effects the paper already cites.
Recorded as a limitation in §6.3 rather than claimed as a finding, since it was
not the designed contrast.

---

## Artifacts

| | |
| --- | --- |
| Runners | `scripts/prepare_and_run_b17_three_class_broken_chain.py`, `scripts/prepare_and_run_b17b_none_baseline.py` |
| Analyses | `scripts/analyse_b17_three_class_replication_v2.py` (three checkpoints), `scripts/analyse_b17_detection_both_baselines_v3.py` (both references) |
| Results | `results/b17_analysis_v1.json`, `results/b17_replication_v2.json`, `results/b17_detection_both_baselines_v3.json` |
| Panels | `data/cognitive_core/three_class_broken_chain_b17/`, `data/cognitive_core/three_class_none_baseline_b17b/` |
| Receipts | `runs/cognitive_core/three_class_broken_chain_b17/<key>/`, `runs/cognitive_core/three_class_none_baseline_b17b/<key>/` |

`analyse_b17_three_class_replication_v2.py` guards against calling one
checkpoint a replication: `replicates` is false unless at least two ran.

---

## Out of scope

- Whether a model *could* detect invalidity given training for it. This measures
  frozen checkpoints under a scoring change, nothing more.
- Whether the effect survives on models outside the b15 set. Three checkpoints,
  two families.
- Disentangling the instruction change from the candidate-set change. b17 moves
  both at once; separating them needs a fourth condition we did not run.
