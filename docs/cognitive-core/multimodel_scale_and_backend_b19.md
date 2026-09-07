# b19: the sweep on a second backend, and the ladder past 7.6B

| | |
| --- | --- |
| Question 1 | Experiment 3 stops at 7.6B because mlx-lm on Apple Silicon does. Does the (model x arm) story continue upward? |
| Question 2 | Moving to CUDA means a second inference stack. Do the two agree? |
| Status | Run 2026-09-07 on a rented A100-40GB; 11 of 12 models scored, 1 failed to load |
| Verdict | **Scale trend refuted.** **Backends disagree enough to move one verdict.** |

---

## Why question 2 came first

Across b16's 9,600 MLX responses, **298 (3.1%) have an argmax margin below 0.1
logits** and the 1st percentile is 0.000 -- comfortably inside the range where
bf16 kernel differences between Metal and CUDA can flip a decision. A table
mixing MLX rows with CUDA rows would not be measuring one thing, so the existing
ten were re-scored on CUDA before anything new was added.

## Decision log

| # | Decision | Reason |
| --- | --- | --- |
| 1 | Re-score the sealed ten on CUDA before adding models | The 3.1% near-tie rate made backend agreement an empirical question, not an assumption |
| 2 | Scoring code copied verbatim from the frozen b16 runner | Same prompt bytes, single-token check, argmax and receipt fields, so the only difference is the backend |
| 3 | Hard assertion that all parameters are on CUDA in bf16 | A silent CPU fallback still produces receipts -- slowly, and in a different numerical regime |
| 4 | New `[[scale_model]]` registry table | Keeps the sealed ten untouched |
| 5 | Everything re-run on the A100 after the L4 | The L4 had torch 2.9.1+cu129 and the A100 2.11.0+cu128. Having just found the backend can move a verdict, letting torch versions vary inside the CUDA set would plant a second confound in the same place |
| 6 | Sourced from mlx-community bf16 mirrors | Eight of the original ten came from there; consistent provenance rather than a new pattern mid-table |
| 7 | Per-model failure handling | A model that will not load is a provenance result, not a reason to abandon an unattended sweep |

---

## Result 1: the backends disagree, and once decisively

Receipt-level agreement on the sealed panel, 960 responses per model:

| Model | agree | flips | largest MLX margin among flips | verdict moved |
| --- | ---: | ---: | ---: | --- |
| llama3.2-1b | 99.69% | 3 | 0.06 | no |
| qwen2.5-1.5b | 99.58% | 4 | 0.06 | no |
| olmo2-1b | 99.48% | 5 | 0.03 | no |
| llama3.2-3b | 98.54% | 14 | 0.06 | no |
| smollm2-1.7b | 98.54% | 14 | 0.06 | no |
| qwen2.5-7b | 98.23% | 17 | 0.25 | no |
| qwen2.5-0.5b | 96.46% | 34 | 0.44 | no |
| qwen2.5-3b | 95.52% | 43 | 0.63 | no |
| **phi-4-mini** | **87.92%** | **116** | **3.00** | **YES** |

Phi-4-mini's `full` arm is **viable under MLX (min per-class recall 0.719, 90.6%
balanced accuracy) and not under CUDA (0.203, 73.4%)**. Median flip margin 0.25
logits, max 3.0 -- not near-ties. It reproduced on **two GPUs and two torch
versions** (L4/2.9.1+cu129 and A100/2.11.0+cu128), so it is MLX vs transformers,
not numerical noise.

`models.toml` sources phi-4-mini from upstream `microsoft/Phi-4-mini-instruct`
because mlx-community had only quantised builds, so mlx-lm converted a
partial-RoPE architecture itself. One of the two implementations is wrong; we do
not claim which.

**Consequence:** viability is a property of (model x arm x **runtime**).

## Result 2: gemma-3-4b will not load under transformers

`mlx-community/gemma-3-4b-it-bf16` is an MLX conversion whose tensor
names/shapes do not match transformers' Gemma3
(`ignore_mismatched_sizes=False ... state dict report`). Eight of ten mirrors
round-trip; one does not. **A table cannot simply be moved between backends even
in principle**, without re-sourcing weights.

## Result 3: the scale trend does not exist

Within b16's range the harm looked like it grew with size (-0.19 at 3B, -0.11 at
4.3B, -0.80 at 7.6B). Extending the **Qwen2.5 within-family ladder** -- family,
tokenizer and recipe fixed, only scale varying:

| Size | harm (min per-class recall, `conclusion_only` -> `full`) |
| ---: | ---: |
| 0.5B | +0.000 (degenerate) |
| 1.5B | +0.000 (degenerate) |
| 3.0B | -0.219 |
| **7.6B** | **-0.688** <- peak |
| **14.7B** | **+0.062** <- no harm |

**The harm peaks in a mid-range band and is absent at the top.** 7.6B was a peak,
not the start of a trend. This vindicates §5.6's existing hedge that "the effect
is not monotonic in scale", written when the range stopped at 7.6B -- and it
would have caught us had we upgraded that sentence into a scale claim.

Llama-3.1-8B, added at the same time, is **degenerate under both arms** (min
per-class recall 0.000): an 8B instruction-tuned model that cannot express three
classes at all.

---

## Artifacts

| | |
| --- | --- |
| Runner | `scripts/run_multimodel_three_class_b19_cuda.py` |
| Analyses | `scripts/compare_b16_backends.py`, `scripts/analyse_scale_extension_b19.py` |
| Results | `results/b16_backend_comparison_v1.json`, `results/b19_scale_extension_v1.json` |
| Receipts | `runs/cognitive_core/multimodel_three_class_b19_cuda/<key>/` |
| Registry | `models.toml`, table `[[scale_model]]` |

Panel and authority are b16's, unchanged and unsealed-from -- b19 scores the same
sealed items through a different runtime.

## Out of scope

- Which of mlx-lm and transformers is *correct* for phi-4-mini. Establishing that
  needs a reference implementation of that architecture, which we did not build.
- Models above 14.7B. A100-80GB quota was refused and the run was dropped rather
  than reaching for quantisation, which would collide with the paper's own
  quantisation limitation.
- Re-sourcing gemma from upstream `google/gemma-3-12b-it` etc., which is gated.
