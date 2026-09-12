# Peer review r12 — solver certificate decomposition

**Commit:** `992d93f` "Review pass on the b20 addition: three fixes"
**Date:** 2026-09-11
**Since:** r11 at `23d63f5` (6 commits, +5,822 lines, 47 files)
**Verdict:** accept. Rubric held at **7/10**. Five items below, four of them one-line fixes.

---

## What changed

A new experiment, **b20**: the sealed b15 panel re-scored on Qwen3-32B and
Llama-3.3-70B on rented H100s. Plus a Table 1 float-placement fix and an
open-items reconciliation.

This is the most valuable addition since the re-baselining at r7. The standing
objection to the paper's one invariant finding was that corruption-following is
a small-model artefact — every checkpoint carrying it was ≤4.3B. b20 answers
that directly, and the answer is verified.

---

## Verified this round

All eleven `verify.py --all` checks pass, including the new `scale-corruption`.
Census now 38,424 across 36 model-runs; the arithmetic reconciles exactly
(34,584 + 2 × 1,920 for the two new ten-arm runs).

Every number in the new §5.3 paragraph, recomputed independently from the
receipts against `data/.../b15/sealed/authority.jsonl`:

| Claim | Paper | Derived |
|---|---|---|
| `misleading` correct | 0 / 192 | **0 / 192** ✓ |
| `full` correct | 192 / 192 | **192 / 192** ✓ |
| `broken_chain` correct | 191 / 192 | **191 / 192** ✓ |
| unaided (`none`) correct | 145 / 192 | **145 / 192** ✓ |
| no item within 0.5 logits | asserted | **min margin 0.812** ✓ (stronger than claimed) |
| Qwen3-32B `full` min per-class recall | 0.167 | **0.167** ✓ |
| Qwen3-32B scored-pair disagreement | 5 of 12 | **7/12 agree → 5 disagree** ✓ |
| Qwen3-32B agreement where confident | 12/12 | **12/12 on `truncate_1`** ✓ |
| Llama-3.3-70B pair agreement | 36 sampled verdicts | **12/12 × 3 arms = 36** ✓ |

Structure: 11 labels, zero undefined, zero orphaned; 39/39 bibliography; no `??`
in the PDF; em-dashes steady at 9; Table 1 now lands on p3 alongside the text
that cites it, with the measurement recorded in a source comment.

The honest exclusion of Qwen3-32B — "We record it and draw nothing from it" —
and the unprompted disclosure of the candidate-tokenisation limitation are both
the right calls, made without being asked.

---

## Items

### 1. `\textsc{full}` … "clearing it on three other arms" — the count is on the wrong side

§5.3, Qwen3-32B. Derived from `results/b20_analysis_v1.json`:

- **Clears** the 0.50 floor on **seven** arms: `broken_chain` 0.677,
  `irrelevant` 0.708, `same_entity_irrelevant` 0.594, `shuffled` 0.625,
  `truncate_1` 0.823, `truncate_2` 0.958, `truncate_3` 0.802.
- **Fails** on three: `full` 0.167, `misleading` 0.000, `none` 0.104.

Three is the count of *failing* arms. The sentence attributes it to the clearing
ones. The correct number strengthens the argument — one broken arm against seven
working ones is a sharper case for "measurement rather than the model" than
three would be.

### 2. "scored through a fourth backend" — it is the same second backend

Limitations, the scale-check paragraph. Both manifests read `transformers+cuda`:

```
multimodel_three_class_b19_cuda/*      transformers+cuda | NVIDIA A100-SXM4-40GB
binary_certificate_factorial_b20_cuda/* transformers+cuda | NVIDIA H100 80GB HBM3
```

Same stack, different hardware. The conclusion's "two inference stacks" is
correct, so the manuscript currently contradicts itself. Suggest "on a third
hardware configuration" or simply "on rented H100s", which §"Experimental Setup"
already says.

### 3. d′ = −5.12 is an artefact of a hand-rolled `erfinv`

`scripts/analyse_binary_certificate_factorial_b20.py:25-37` defines a Winitzki
polynomial approximation (`a = 0.147`) and uses it for d′. Its docstring says
"matching the b15 analysis" — but it is **the only script in the repo that does
not use `statistics.NormalDist`**; `analyse_b15_share_interval_and_holm_v2.py`,
`audit_cognitive_solver_assisted_v7_publication.py`,
`reanalyse_..._b14_posthoc_v1.py` and
`run_cognitive_solver_assisted_certificate_factorial_v8.py` all use the exact
inverse CDF.

Same loglinear formula, both ways, on hits = 0, fa = 96, n = 96:

```
approximation (as shipped) :  -5.124   → printed as -5.12
statistics.NormalDist      :  -5.1306  → -5.13
```

Nothing scientific turns on 0.007 of d′. But this is a manuscript whose pitch is
that every number re-derives from released receipts, and the printed value comes
from a different numerical primitive than every other d′ in the paper — while
the docstring asserts otherwise. `verify.py`'s `scale-corruption` check covers
the counts (exact integers) but not d′, so the verifier cannot catch it.

Fix: `from statistics import NormalDist`, delete `_erfinv`, reprint −5.13. The
"standard library only" property of the verifier is preserved.

### 4. The title counts a checkpoint the paper declines to interpret

Title, abstract, §1 and the conclusion now all say **fourteen models**. But
`tab:models` is sixty cells = twelve models × five arms (the verifier confirms
sixty), and §5.3 says of the fourteenth: *"Qwen3-32B is not interpretable here…
We record it and draw nothing from it."*

Thirteen is the number the paper actually draws on. After eleven rounds of
removing exactly this kind of gap between the front matter and the body, the
title is now the last place one survives. Either "Across Thirteen Models", or
keep fourteen and say "fourteen checkpoints, thirteen interpreted" once in §1.

### 5. The tokenisation audit is scoped to the two checkpoints that need it least

This is the substantive item.

The new limitation reassures on one checkpoint: *"on the checkpoint carrying the
scale claim the two pairs agree on all 36 sampled verdicts."* That is
Llama-3.3-70B. The other twelve — which carry every headline number — are not
addressed, and the Qwen3-32B case proves the failure mode is real, not
hypothetical.

The released receipts already settle most of this, at no GPU cost. Median
top-two margin and the share of responses within 0.5 logits, computed from
`prospective-*.jsonl`:

| Panel | Checkpoint | median margin | % < 0.5 logits |
|---|---|---|---|
| **b15** | `qwen2p5_3b_4bit` | 11.33 | **0.9%** |
| **b15** | `qwen2p5_3b_bf16` | 11.00 | **0.4%** |
| **b15** | `gemma3_4b_b15` | 6.88 | **0.5%** |
| b16 | `llama3p2_3b` | 0.75 | **32.6%** |
| b16 | `smollm2_1p7b` | 1.22 | 25.7% |
| b19 | `llama3p1_8b` | 0.63 | **40.4%** |
| b20 | `llama3p3_70b` (scale arms) | — | **0.0%** |

Two consequences, pulling in opposite directions:

**The headline numbers are safe, and the paper should say so.** The 98.3%
validity share, Gemma's 40.4/51.4%, the +22.4pp state effect and the 189/186/192
corruption result all live on b15 checkpoints sitting 7–11 logits from
indifference, with under 1% of responses anywhere near the boundary. That is a
far stronger statement than the one currently made, it covers the claims that
matter, and it is derivable from released receipts with no new compute.

**The exposure is in `tab:models`, where no caveat currently appears.**
`llama3p1_8b` has 40.4% of its scored responses within 0.5 logits — more
near-indifferent than Llama-3.3-70B's *worst* arm (`irrelevant`, 35.9%) and
unlike anything in the arms carrying the scale claim (0%). `llama3p2_3b` is at
32.6%. Both are in the non-degenerate set, so both feed the +14.7pp re-baselined
cross-model mean and sixty cells of `tab:models`.

And this cannot be closed from the artifact: the older receipts store
`candidate_token_scores` for the bare tokens only, and
`diagnose_qwen3_answer_position_b20.py` re-loads the model
(`--repo`, `--revision`). So it is GPU time, or an explicit scope statement.

Three ways to close it, in increasing cost:

1. **Free.** Add the margin table above to the limitation. It converts "we
   checked one checkpoint" into "the claims rest on checkpoints that are not
   near indifference, and here is the distribution" — and it names the two
   sweep checkpoints that are.
2. **Cheap.** Run the existing diagnostic on `llama3p1_8b` and `llama3p2_3b`
   only. Twelve sampled items each, three arms — the same protocol already
   applied to Qwen3-32B.
3. **Complete.** Re-score with both token pairs and report disagreement per
   checkpoint. Almost certainly not worth it given (1).

Worth noting that if some `tab:models` viability failures turn out to be scoring
artefacts, that *supports* the paper's own stated position — "viability is per
arm because it is a property of (model × arm × runtime), not of a model" — while
weakening the specific cells. The caveat costs the argument nothing.

---

## Rubric

| Dimension | Score | Note |
|---|---|---|
| Novelty | 4 / 5 | unchanged |
| Technical soundness | 5 / 5 | the scale result is clean and independently reproduced |
| Significance | 4 / 5 | materially improved: the invariant finding now survives to 70.6B |
| Experimental rigor | 5 / 5 | unchanged |
| Reproducibility | 5 / 5 | item 3 is a consistency defect, not a reproducibility one |
| Clarity | 5 / 5 | unchanged |

Soundness **4/4** · Contribution **4/4** · Presentation **4/4** ·
**Overall 7/10 — accept** · Confidence **5/5**

### Why still 7

At r11 I held at 7 on four structural grounds: one synthetic task family, models
to 14.7B, forced-choice single-token scoring, and a positive claim set of
instrument + non-transfer + one negative reliability result.

b20 removes the second of those — decisively. A checkpoint that solves 145/192
unaided and is wrong on 192/192 given one fabricated rule, at d′ ≈ −5.13 with no
item near the boundary, is not a small-model story.

But it sharpens the third. Forced-choice single-token scoring was a theoretical
liability at r11; Qwen3-32B makes it a documented one, with a real checkpoint
where the scored pair inverts against what the model would emit. That liability
is currently audited on two of fourteen checkpoints. Item 5 closes it, and the
free version of the fix is probably enough.

One removed, one sharpened, net zero. Fix items 1–4 and take option (1) on item
5, and 7 is comfortable rather than held.
