# Peer review, round 6 — "What a Language Model Does with a Solver Certificate"

- **Manuscript:** commit `d147d93`, 14 pp incl. appendix
- **New since r5:** `90ec906` (verify.py, abstract, §3–5 clarity), `c6dac46` (b18 + b19),
  `d147d93` (shrink to 9 pages)
- **Recommendation:** **Minor revision** — down from r5's accept, and the reason is narrow: the
  two new studies are strong and raise the science, but the reporting added **two wrong printed
  numbers** and left several bolded claims stale against the new data. Rubric unchanged at
  **7/10**; the added experiments and the reporting slips offset.

---

## 1. What's new, and it's substantial

Not "a couple of changes". Two new studies, 34 model-runs, 34,584 responses (up from 20/18,840),
and a self-service verifier.

**`scripts/verify.py`** — 7 named claims, each recomputed *from the receipts and the sealed
authority* rather than read out of an analysis JSON, printed beside the manuscript's value. I ran
`--all`: **all 7 pass** (census, corruption, cross-model, detection, gemma-share, state-effect,
validity-share). This is the strongest reproducibility affordance I have seen on a submission of
this kind — it converts "re-derivable in principle" into a one-minute check.

**b18 — permutation study (§5.3, "Not adjacency, but direction").** 8 permutations per item on
three checkpoints plus an identity arm. Three results, all verified:
- The identity arm reproduces b15 `truncate_1` **192/192 on all three checkpoints** — a real
  internal-consistency check, not a formality.
- Order effect ranges: 41.7–50.0pp (Qwen 4-bit), 60.4–63.5 (bf16), 6.25–13.5 (Gemma). Each
  checkpoint's published single-seed value falls inside its own range (46.9, 62.5, 10.4). My
  standing single-seed objection is now closed with a distribution.
- **The paper's own adjacency claim is refuted.** Accuracy by gap between the final rule and its
  premise is flat (18.1% at gap 1 vs 24.0% at gap 7, 4-bit); what matters is *direction* —
  rule-after-premise 26.8/22.4/94.9% vs rule-before 5.8/4.8/84.9%, paired within item 45 vs 2,
  p = 1.6×10⁻¹¹. §5.3 says outright "§6.1 said so and was wrong", and §6.1 is correctly rewritten
  to "the rule follows the premise it fires on".

**b19 — scale extension + second runtime.** 11 models on `transformers`+CUDA, adding Qwen2.5-14B
and Llama-3.1-8B. The Qwen harm ladder (0.000, 0.000, −0.219, −0.688, +0.062 from 0.5→14.7B) shows
the degradation peaks mid-range and vanishes at the top — refuting the reading that proof state is
more dangerous for bigger interfaces.

**Backend comparison — the most novel thing in the paper now.** Same sealed panel, same weights,
two inference stacks. Eight of the nine models that load agree on 95.5–99.7% of responses with no
verdict moving; **Phi-4-mini's `full` arm is viable under mlx and not under CUDA**, reproduced on
two GPUs and two library versions. "Viability is a property of (model × arm × runtime)" is a
genuinely useful, genuinely uncomfortable finding for anyone publishing per-model capability
verdicts, and I have not seen it made this cleanly elsewhere.

---

## 2. Two factual errors — must fix

**§6.3, "Inference runtime":**

1. **"(0.719 against $0.203$ minimum per-class recall)".** Phi-4-mini's CUDA `full` minimum
   per-class recall is **0.219** (`{No: 0.21875, Unknown: 1.0, Yes: 1.0}`), confirmed in both
   `b19_scale_extension_v1.json` and `b16_backend_comparison_v1.json` (`cuda_min_recall: 0.219`).
   **0.203 is the harm delta**, 0.219 − 0.016, stored as `state_harm_min_recall`. A different
   quantity has been substituted for the one the sentence names.
2. **"nine of ten models agree on 95.5–99.7% of responses with no verdict moving — but
   Phi-4-mini's…".** The comparison contains **nine** models, not ten; the tenth is Gemma-3-4B,
   which is the model that "will not load under the second stack". Of the nine, **eight** agree in
   the 95.5–99.7% band; **Phi-4-mini agrees on only 87.9%** (116 flips of 960). As written the
   sentence places Phi-4-mini in the "tenth" slot and suppresses the 87.9%, which *is* the
   magnitude of the runtime effect. Correct form: "of the nine models that load under both stacks,
   eight agree on 95.5–99.7% with no verdict moving; Phi-4-mini agrees on 87.9% and its `full` arm
   is viable under one stack and not the other. Gemma-3-4B will not load under the second stack at
   all."

Neither error is in the analysis — the JSONs are right and `verify.py` passes. Both are in the
prose, which is the same failure mode as rounds 2–4 and the reason I am not recommending accept
outright.

---

## 3. The runtime finding is under-reported relative to its billing

It is the abstract's headline ("model × arm × runtime") and lives in one Limitations paragraph.
Three facts belong with it, all in the released data:

- **Phi-4-mini's `full` balanced accuracy moves 90.6 → 74.0** on identical weights. The paper
  quotes only the recall pair; the 16.7pp accuracy swing is the number a reader will react to.
- **The flips are not all near-ties**: `max_mlx_margin_among_flips` is **3.0 logits** for
  Phi-4-mini. That forecloses the obvious dismissal ("it's just tie-breaking noise") and should be
  stated.
- **Gemma-3-4B has no runtime replication**, because it will not load — and Gemma is the
  checkpoint carrying the 40.4/51.4% share and the entire "does not generalise" argument. Name it.
  A reader is entitled to know that the model bearing the paper's most-qualified claim is the one
  the robustness check cannot cover.

Given that this is arguably now the paper's most transferable contribution, consider promoting it
out of Limitations into a short Results subsection. It would also earn contribution a point.

---

## 4. Claims left stale against the new data

1. **§5.7 still bolds "Viability is a property of (model × arm)"** while the abstract says
   **(model × arm × runtime)**. Contribution (v) in §1 repeats the two-factor version.
2. **"Supplying proof state degrades three of ten models"** (§5.7, bolded, and contribution (v))
   is the mlx figure. On CUDA `degraded_by_proof_state` is **two of eleven** (Qwen2.5-3B,
   Qwen2.5-7B) — Gemma, the third, is absent from that run. Say which runtime the count is from.
3. **The scale-ladder paragraph says "family, tokenizer and recipe fixed, only scale varying"** —
   but the ladder is computed on **CUDA** while `tab:models` directly above it is **mlx/MPS**. The
   backend varies too, relative to the table the sentence claims to extend. (MPS harm for 3B/7.6B
   is −0.187/−0.797 against the quoted CUDA −0.219/−0.688 — the paper's own §6.3 is the reason
   this matters.)
4. **§6.2 says "Two analyses are post hoc"**; there are now three self-corrections — the E1 2×2
   reading, the E3 viability criterion, and the adjacency characterisation §5.3 retracts.
5. **§4 Setup introduces neither robustness study**, neither new model (14.7B, 8B), nor the second
   stack, while the abstract advertises "four sealed experiments and two robustness studies" and a
   runtime factor. Same class of staleness as rounds 2–4, in a new location.

---

## 5. Two b19 results omitted, both cutting against a size story

- **Llama-3.1-8B is degenerate in every arm** — minimum per-class recall **0.000** across all
  five, with `full` at 66.7% balanced accuracy. An 8B model that collapses while a 3B model clears
  every arm is the strongest single datum against a size floor, and it is not mentioned anywhere.
- **Qwen2.5-14B clears no arm** (`conclusion_only` 0.422, `full` 0.484, `viable_in: []`) despite
  82.8% `full` balanced accuracy. "The harm is *absent* at the top" reads as "14B works"; by the
  paper's own floor it does not. Both facts strengthen "not monotonic in scale" — there is no
  reason to leave them out.

---

## 6. Smaller items

1. **"Distance does nothing" has no inferential statistic**, and rests on badly unequal cells:
   gap 1 is 39/216 (18.1%), gap 7 is **6/25** (24.0%), so the gap-7 CI spans roughly 9–45%. The
   *direction* claim is properly tested (paired, p = 1.6×10⁻¹¹); the distance null is asserted.
   Either test it or state it as "no monotone trend across these bins" with the n's shown.
2. **"Requires the rule to follow its premise" over-reads Gemma.** Rule-after/before is a ~4.6×
   ratio on the Qwens (26.8/5.8, 22.4/4.8) but **94.9/84.9** on Gemma — a 10pp modulation on a high
   base. §1 and the Conclusion list it among findings that "hold on every checkpoint": the
   *direction* holds everywhere, the *requirement* does not.
3. **§5.3: "the published $+46.9$pp falls inside the resulting range on every checkpoint."** True
   per checkpoint (46.9 ∈ [41.7, 50.0]; 62.5 ∈ [60.4, 63.5]; 10.4 ∈ [6.25, 13.5]) but the sentence
   names only the 4-bit value, which lies outside the other two ranges. Reword to "each
   checkpoint's published value falls inside its own range".
4. **Neither robustness study has a table or a figure.** b18's gap profile is 7 bins × 3
   checkpoints in the JSON and gets two numbers in prose; b19 is 11 models × 5 arms and gets five
   inline numbers. b17/b17b earned a `tab:panels` row last round for exactly this reason — b18 and
   b19 have no row either.
5. **Round-5 typo not fixed:** `fig:replication` caption, line 1014, "…manages unaided**. the** two
   denominators coincide". Still the only lowercase-after-period in the file.

**Verified clean:** `verify.py --all` 7/7; census 34,584 / 34 runs reproduces
(18,840 + 5,184 b18 + 10,560 b19); zero orphan floats; bibliography 39/39 with no dangles; no
undefined references in the rendered PDF; 14 pp.

---

## 7. Rubric

| Dimension | Weight | r5 | r6 | Change |
|---|---|---|---|---|
| Novelty | Critical | 3.5/5 | **4/5** | ↑ The runtime-moves-a-verdict finding is new and transferable; the gap-vs-direction dissociation is a sharper mechanistic result than "adjacency" |
| Technical soundness | Critical | 5/5 | **5/5** | Held. b18's identity arm reproduces b15 192/192; the direction claim is paired-tested; `verify.py` recomputes from receipts |
| Significance | High | 3.5/5 | **4/5** | ↑ "Per-model capability verdicts are runtime-dependent" bears on how this whole literature reports results |
| Experimental rigor | High | 5/5 | **5/5** | Held. Two robustness studies, both of which refuted a claim the paper had made |
| Reproducibility | Mod.–High | 5/5 | **5/5** | Held at the ceiling; `verify.py` is above it |
| Clarity | Moderate | 4/5 | **3/5** | ↓ Two wrong printed numbers, five stale claims, two prose-only studies with no float |

| Venue dimension | r5 | r6 |
|---|---|---|
| Soundness (1–4) | 4 | **4** — errors are in the prose, not the analysis |
| Contribution (1–4) | 3 | **3** — would be 4 with the runtime finding promoted and corrected |
| Presentation (1–4) | 3 | **2** — now the binding constraint |
| **Overall (1–10)** | 7 | **7** |
| Confidence (1–5) | 4 | **5** — the verifier let me check the claims directly |

---

## 8. Assessment

The science went up and the prose went down, and they cancel. b18 and b19 are exactly the right
two studies to have run: one closed my single-seed objection *and* refuted the paper's own
adjacency claim in the same pass; the other refuted the reading that proof state is worse for
larger models, and turned up a methodological result — that a per-model viability verdict can flip
on the inference stack alone, at margins up to 3 logits — which is more broadly useful than
anything else in the paper. `verify.py` is the right answer to "is this really re-derivable".

Against that, §6.3 now prints a harm delta where it says minimum per-class recall, and miscounts
the runtime comparison in a way that hides its own effect size and obscures that the uncovered
model is the one the paper's central qualification rests on. Five claims elsewhere still describe
the pre-b19 world, including two bolded ones and a contribution bullet. And the two studies that
carry this round arrive with no table, no figure, and no mention in Setup.

Every one of these is a half-hour of editing, and none touches an analysis. But two wrong printed
numbers is a minor revision, not an accept — particularly in a paper whose thesis is that people
should check their numbers.

**Recommendation: minor revision.** Fix §2 (both errors), reconcile §4, then this is an accept
again, and a stronger one than at r5.
