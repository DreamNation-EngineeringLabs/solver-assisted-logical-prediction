# Peer review — round 3

- **Manuscript:** "What a Language Model Does with a Solver Certificate: An Answer-Evidence Decomposition Across Ten Models"
- **Verdict:** **accept, subject to ten copy-level fixes.** ~7.5/10. **No further experiments needed.**
- **Date:** 2026-09-07

## Majors — all six closed

Four were closed by running the experiment rather than rewording the claim.

| # | Point | Disposition |
| --- | --- | --- |
| 1 | Counts reconcile | New `receipt_census_v1.json` + `census_receipts_v1.py`; the paper says 18,840 responses / 20 model-runs, generated at compose time rather than typed. **Reviewer re-counted the receipts independently — exactly 18,840 / 20** |
| 2 | Detection tested on all three checkpoints, plus a new b17b `none`-arm baseline | Abstention falls against both references everywhere: −32.8 / −38.5 / −7.8pp vs `irrelevant`; −37.5 / −3.6 / −0.5pp vs `none` |
| 3 | Gemma's share on both baselines | 40.4% vs `irrelevant`, 51.4% vs `none`, with the 20-of-22 unaided overlap; §5.3 explicitly refuses the "most of it is surface overlap" reading |
| 4 | `tab:arms` is the full 10-arm × 3-checkpoint grid | §5.3 now reports the order-sensitivity non-replication (`shuffled` 14 / 12 / 86) |
| 5 | Ten-model mean fixed | +14.7 vs +28.5pp excluding the four degenerate responders, with "less than half" withdrawn by name |
| 6 | Introduction fully rewritten and consistent | The d′ = 0 claim scoped to the Qwen checkpoints, with Gemma's 22/96 called out |

## Minors — closed

Figure 1 draws `none` = 91 and annotates the interaction and ceiling; `fig:size`
uses hatch patterns so the viability categories survive colourblindness;
tie-breaking documented ("occurs twice" — **verified, exactly 2 zero-margin ties
in 5,760**); the `misleading` unit mixing and the 93/96 class split both fixed;
duplicate `\usepackage` gone.

---

## What remains: prose lagging the analysis

### The two that matter

1. **The abstract still asserts what §5.3 refuses.** "40.4% on another that
   exploits surface overlap heavily" against §5.3's "we make no claim that most
   of Gemma-3-4B's effect is surface overlap".
2. **The abstract quotes one checkpoint's detection delta on the reference §5.5
   calls incomparable.** 75.0% → 42.2% is Qwen-4bit vs `irrelevant`.

### Eight smaller

3. §4.1 still says "All three experiments" and never describes Experiment 4.
4. `tab:panels` caption says "four sealed panels" over a three-panel table.
5. §6.1's 40.4–98.6% range does not name its baseline.
6. §5.2's order claim is unscoped.
7. `fig:replication` was not regenerated and still tells the single-baseline story.
8. `fig:detection`'s caption is narrower than its own figure.
9. `tab:edges` is still in the appendix.

*(The review says "eight smaller" but enumerates seven; the eighth is not named.)*

---

## Framing suggestion

Gemma abstains on 1/192 with no record, so its **−0.5pp delta is a no-power
null, not a refutation**. The paper concedes this and then gives the right
argument as an addendum — Gemma abstains on 0/192 broken certificates while
completing 76. **Lead with that for Gemma**; it is stronger than any delta and
immune to baseline choice.
