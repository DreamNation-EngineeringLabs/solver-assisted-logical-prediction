# Response to reviewers — round 2

- **Manuscript:** "What a Language Model Does with a Solver Certificate: An Answer-Evidence Decomposition Across Ten Models"
- **Review:** [`2026-09-07-solver-certificate-decomposition-peer-review-r2.md`](2026-09-07-solver-certificate-decomposition-peer-review-r2.md) — minor revision (up from major), 2 blocking, 3 substantive, 13 minors
- **Date:** 2026-09-07

Four of the reviewer's five substantive points were settled by running something
rather than rewording something, and three of those four moved a number against
us. The fifth — the count reconciliation — was the most serious defect in the
submission and we treat it that way below.

**What changed, in order of how badly we needed it pointed out.**

1. **The audit counts did not reconcile, and the reviewer's count was right.**
   The abstract said 18,816 scored responses and twelve model-runs; §4.3 and the
   Reproducibility Statement said 12,480; the released receipts held **17,112
   across 15 runs**. In a paper whose thesis is re-derivability this is the worst
   available error and there is no defence for it. Fixed structurally rather than
   by retyping: `scripts/census_receipts_v1.py` counts what is on disk, writes
   `results/receipt_census_v1.json`, and the composer substitutes the values at
   build time. A new run can no longer leave the manuscript describing the old
   corpus. With the round-2 experiments the figure is now **18,840 across 20
   model-runs**, and the supplementary zip's README derives it the same way.

2. **Gemma's validity share was confounded with its unaided competence.** The
   reviewer computed 51.4% re-baselined on `none`; we reproduce exactly that.
   Gemma-3-4B answers 22 of 96 entailed items with no certificate at all, and
   **20 of those 22** are also correct under `broken_chain`. The published 40.4%
   divides by the effect against `irrelevant`, which coincides with `none` on both
   Qwen checkpoints (both 0/96) and does not on Gemma. §5.3 now reports both and
   **explicitly declines** the "most of Gemma's effect is surface overlap"
   reading; on the conservative denominator the split is close to even. The
   divergence between baselines — which appears exactly when a substrate has
   unaided competence — is now stated as the finding, rather than either number.
   This also promotes §6.1's "pointer back into the theory" caveat from
   hypothetical to live, and it is labelled as such.

3. **The detection refutation was single-checkpoint and missing where it mattered.**
   b17 existed only for Qwen 4-bit while the Conclusion claimed "every
   checkpoint", and it had not been run on Gemma-3-4B — the one model that answers
   broken certificates correctly (58/96), and therefore the only one where
   "detects the break" and "fails to complete" make visibly different predictions.
   Run on all three. Abstention falls everywhere: −32.8, −38.5 and −7.8pp against
   `irrelevant`.

4. **The `none` arm the reviewer asked for changed how those deltas can be read**
   (minor 11, which turned out not to be minor). b17b adds a no-record arm under
   the same instruction and candidate set. The two references coincide on the
   4-bit checkpoint (79.7% vs 75.0%) and **diverge by 34.9pp at bfloat16**, where
   a same-shape irrelevant record raises abstention substantially over supplying
   nothing. A Δ measured against `irrelevant` is therefore not comparable across
   checkpoints. Against `none` the falls are −37.5, −3.6 and −0.5pp. We report
   both, and we now lead the argument with the composition evidence, which no
   baseline choice can move: Gemma abstains on **0 of 192** broken certificates
   while *completing* 76 of them, and on the 4-bit checkpoint `No` is 110/192
   under both `broken_chain` and `truncate_1` with only `Yes` separating them
   (1 vs 61).

5. **"Less than half" does not survive excluding the degenerate responders.**
   The reviewer's +14.7pp reproduces exactly. The ten-model mean averages over
   four models whose minimum per-class recall is 0.000 in *every* arm, three with
   negative state effects. §5.7 now reports both means and **withdraws the claim
   by name**; the qualitative point survives cleanly (answer +28.5pp vs state
   +14.7pp, and 8 of 10 individually).

6. **The Introduction was untouched v1 text.** It contradicted the abstract on
   six points, and §5.4 asserted validity tracking two paragraphs before §5.5
   refuted it. Rewritten. The `d′ = 0` claim is now scoped to the Qwen
   checkpoints with Gemma's 22/96 at d′ = 1.83 called out where it applies.

**Order-sensitivity also fails to replicate**, which the reviewer noted and we had
not: `shuffled` scores 14 and 12 of 96 on the Qwen checkpoints and **86** on
Gemma. §5.3 says so.

---

## Minors

| # | Point | Disposition |
| --- | --- | --- |
| 1 | §5.4 unit mixing (R1 minor 1) | Fixed — −98.4pp on all 192 items |
| 2 | §5.4 omits the class split | Added — `Yes` on **93 of 96** contradicted items, inverting a near-total `No` prior at c = 2.565 |
| 3 | Figure 1 caption/figure mismatch (R1 minor 3) | Figure rebuilt: `none` = 91 now drawn outside the square, and the interaction (−29.2pp) and ceiling annotated |
| 4 | `fig:arms` caption reads general | Scoped — "on this checkpoint; cf. §5.3" |
| 5 | Red/green palette (R1 minor 7) | `fig:size` now encodes verdict by **hatch as well as hue**; validated with a CVD checker |
| 6 | Tie-breaking undocumented (R1 minor 8) | Stated with its incidence: first candidate in declared order, **twice** in 5,760 responses |
| 7 | Single seed for `shuffled` (R1 minor 10) | Disclosed in §6.3 as a limitation, with the checkpoint-dependence that makes it matter |
| 8 | Prompt-format sensitivity unframed (R1 minor 11) | Added to §6.3 — b17 moves instruction and candidate set on byte-identical inputs |
| 9 | §5.7 self-reference bug | Fixed |
| 10 | Duplicate `\usepackage` (R1 minor 13) | Fixed — the composer inserted the tex_profile packages twice |
| 11 | b17 has no `none` arm | **Run.** See point 4 above; it changed the analysis |
| 12 | `tab:replication` terse headers | Moot — merged into `tab:arms` as a ten-arm × three-checkpoint grid |
| 13 | Title change is an improvement | Noted, kept |

---

## On the appendix placement

The reviewer asked whether pushing `tab:replication`, `tab:sdt` and
`fig:detection` to the appendix was a page-limit decision. It was, and it was the
wrong trade. All three are back in the body, paid for by cutting prose: Related
Work is 20% shorter without losing a citation, and the Introduction, Limitations
and Conclusion are tightened. `tab:arms` and `tab:replication` are now one table
that is smaller than either and strictly more informative. Main text is 9 pages
with no overfull boxes.

---

## New artifacts

| | |
| --- | --- |
| Runner | `scripts/prepare_and_run_b17b_none_baseline.py` |
| Analyses | `scripts/census_receipts_v1.py`, `scripts/analyse_b15_share_baselines_v3.py`, `scripts/analyse_b16_state_effect_v3_degenerate_exclusion.py`, `scripts/analyse_b17_three_class_replication_v2.py`, `scripts/analyse_b17_detection_both_baselines_v3.py` |
| Results | `results/receipt_census_v1.json`, `results/b15_share_baselines_v3.json`, `results/b16_state_effect_v3.json`, `results/b17_replication_v2.json`, `results/b17_detection_both_baselines_v3.json` |
| Design doc | `docs/cognitive-core/three_class_broken_chain_b17.md` |

Every one of these runs from a fresh unpack of the supplementary zip with no
network and no model weights; the snapshot builder refuses to produce the zip
unless all ten verification scripts pass from the clean copy.
