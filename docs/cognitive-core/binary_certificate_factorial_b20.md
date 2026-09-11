# b20 — does the corruption failure survive scale?

**Status: complete, 2026-09-11.** Three checkpoints scored on the sealed b15
panel. Receipts under `runs/cognitive_core/binary_certificate_factorial_b20_{cuda,edge0}/`.

## Why

The paper's one invariant finding is that no checkpoint resists a corrupted
apparatus: given a certificate whose fabricated final rule establishes the
query's negation, all three answer incorrectly on 189, 186 and 192 of 192.

Every checkpoint behind that number is **at most 4.3B**, so the obvious
objection is that it is a small-model artefact that scale removes. The r11
reviewer named "models to 14.7B" as one of four structural reasons the paper
sits at 7 rather than 8.

The existing data already points the other way. Gemma-3-4B is the most capable
of the three on every measure available and is the one that scored 192/192
wrong. Competence rose; verification did not appear. But three checkpoints under
4.3B cannot settle what happens at 70B.

## Design

**No new panel.** The sealed b15 items are re-scored, byte-identical prompts,
so this is a re-scoring in the b19 sense rather than a new experiment. The
answer authority is never read by any runner.

**Arms.** All ten on CUDA; `full` and `misleading` only on edge0, where
streaming-MoE inference costs ~18 s per item and ten arms would take 9.6 hours.

**Prespecified reading, fixed before the numbers were seen.** The corruption
contrast is an absolute count and needs no denominator, so it is interpretable
at any competence level. The validity share is not: it divides by
(`truncate_1` − `irrelevant`), and a model with high unaided competence drives
that denominator toward zero. **Any checkpoint failing the min-per-class-recall
≥ 0.50 floor under `full` is reported as non-viable and its corruption number is
not interpreted**, on the same grounds Experiment 3 uses.

## Checkpoints

| key | params | why |
| --- | --- | --- |
| `qwen3_32b` | 32.8B dense | extends the within-family Qwen ladder past 14.7B |
| `llama3p3_70b` | 70.6B dense | extends the Llama ladder past 8.0B; the scale point |
| `edge0_35b_a3b` | 35B total, ~3B active | separates active from total parameters, which no dense checkpoint can |

Both CUDA checkpoints are ungated standard-format safetensors rather than
mlx-community mirrors: b19 recorded that gemma-3-4b's MLX conversion could not
be loaded by the transformers stack.

## Results

| checkpoint | viable under `full`? | `misleading` correct | d′ |
| --- | --- | ---: | ---: |
| `llama3p3_70b` | yes, min recall 1.000 | **0/192** | −5.12 |
| `edge0_35b_a3b` | yes, min recall 0.635 | 79/192 | −1.28 |
| `qwen3_32b` | **no**, min recall 0.167 | 70/192 | not interpreted |

**Llama-3.3-70B is the load-bearing result.** It is perfect on `full` and
`truncate_1` (192/192, d′ = +5.12), scores 191/192 under `broken_chain`, and
solves 145/192 with no certificate at all. A single fabricated rule inverts
every one of 192 items at d′ = −5.12, with no item near the decision boundary.

The corruption failure therefore does not attenuate with scale. It is total at
70B, on a checkpoint that demonstrably does not need the certificate.

## What this does NOT show

- **Not a verification result.** `broken_chain` 191/192 is not evidence that the
  model detected the break. The full theory is visible in every arm and this
  checkpoint scores 145/192 unaided, so it may simply have ignored a useless
  record and solved from the theory. The b15 design is diagnostic for detection
  only where unaided competence is zero, which is not the case here.
- **The validity share is undefined for these checkpoints.** Unaided competence
  collapses the denominator, exactly as prespecified above.
- **Instruction compliance is not separated from verification failure.** Every
  prompt opens `Use only the supplied logical facts, rules, and solver record`,
  so "did not check" is entangled with "was told to use it" — and a larger model
  follows instructions better. Separating them needs one changed instruction
  line on the same panel. Not run here.
- **`qwen3_32b` is not interpreted.** It collapses to answering Yes to 91.7% of
  items under `full` while remaining viable under `irrelevant`, `truncate_1` and
  `broken_chain`. That is the same shape as Qwen2.5-7B, but Qwen3 is a hybrid
  thinking model scored here without a chat template, so a format artefact is not
  excluded. Deciding it needs the unconstrained top-k tokens at the answer
  position; until then it is recorded, not reported.
- **One checkpoint at this scale, one task family, one prompt shape.**

## Decision log

- **2026-09-11** — Ran on Modal (H100) rather than GCP, which had not approved
  the quota request. Recorded in each manifest: GPU name, count, torch version.
- **2026-09-11** — Scored all ten arms on CUDA even though only two are needed
  for the corruption contrast: the model is resident anyway and the marginal
  cost is seconds, so the full arm set is cheaper to collect now than to re-run.
- **2026-09-11** — edge0 limited to two arms on runtime grounds, recorded above.
  Its `complete.json` is deliberately absent because the run is partial.
