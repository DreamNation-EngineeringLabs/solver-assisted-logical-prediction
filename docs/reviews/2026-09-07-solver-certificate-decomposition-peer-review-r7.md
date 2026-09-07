# Peer review, round 7 — "What a Language Model Does with a Solver Certificate"

- **Manuscript:** commit `cbb078f`, 15 pp (body ends p10; refs; appendix)
- **Recommendation: ACCEPT.** One word in two places, plus one float-placement call. No new data
  needed. Rubric **7/10**, and contribution now earns the point I withheld at r6.

---

## 1. Round-6 items: all fixed, and fixed precisely

**Both factual errors corrected.**
- Phi-4-mini's CUDA `full` minimum per-class recall now reads **$0.219$** (was 0.203, which was the
  harm delta). Verified against `b16_backend_comparison_v1.json` (`cuda_min_recall: 0.219`) and
  `b19_scale_extension_v1.json`.
- The runtime comparison count is right: "covers **nine of the ten** models… **Eight of the nine**
  agree on $95.5$–$99.7\%$… **Phi-4-mini does not.** It agrees on $87.9\%$ — $116$ flips of $960$."
  All four numbers verified (agreements span 95.52–99.69%; phi4 0.8792, `n_flips` 116).

**The runtime finding is promoted to §5.8, "The runtime is a factor"** — out of Limitations, as a
Results subsection, carrying every fact I asked for:
- balanced accuracy $90.6\%$ against $74.0\%$ on identical weights (verified: 90.62 / 73.96);
- "The flips reach $3.0$ logits, so this is not tie-breaking noise" (verified:
  `max_mlx_margin_among_flips` 3.0);
- Gemma-3-4B named as the uncovered model, with the consequence stated outright — "the checkpoint
  carrying the $40.4$–$51.4\%$ share… is the one model this check cannot cover — so the share
  itself has no runtime replication, and we do not claim one."

That last sentence is the paper at its best: it identifies that its own most-qualified claim is the
one its new robustness check cannot reach, and says so without being asked twice.

**All five stale claims closed.** §5.7 now reads "(model × arm) — and, by §5.8, of the runtime
too", and "degrades three of ten models **here**… On the CUDA re-scoring the same measure gives two
of eleven, which is the runtime factor of §5.8 again rather than a different finding." Contribution
(v) is rewritten to "a sweep over eleven models showing viability to be a property of (model × arm
× runtime) — including one model whose verdict changes with the inference stack alone." The scale
ladder now says "the whole ladder on one runtime". §6.2 says "**Three** analyses are post hoc".
§4.1 gains a paragraph introducing both robustness studies, the second stack (`transformers` on an
A100 vs `mlx-lm`) and the two added models; `tab:panels` gains a `b18` row and a "`b16` on a second
stack" row.

**Both omitted b19 results are in, with a new `tab:scale`** (0.5–14.7B plus Llama-3.1-8B; every
cell verified against `b19_scale_extension_v1.json`). Llama-3.1-8B is called "**degenerate in every
arm**… the strongest single datum against a size floor", and Qwen2.5-14B "clears no arm either
($0.422$ and $0.484$) despite $82.8\%$, so 'absent at the top' must not be read as '14B works'."
The table caption makes the same point independently.

**Every smaller item fixed too.** §5.3 now gives all three permutation ranges and adds the
unequal-cell caveat verbatim — "that last cell is $6$ of $25$ and we draw no trend from it". The
Gemma over-read is corrected in its own paragraph: "The direction of that effect holds on all three
checkpoints, but its size does not: a $4.6\times$ ratio on the Qwen checkpoints is a $10$pp
modulation on Gemma-3-4B, which is near ceiling throughout. So ordering is not a *requirement*
everywhere." §6.1 is rewritten to match ("reversing the final rule and its premise costs accuracy
on every checkpoint, while separating them does not"). The `fig:replication` caption typo is gone.

**Mechanically clean:** `verify.py --all` **7/7**; zero orphan floats; no lowercase-after-period
anywhere; bibliography 39/39 with no dangles; no undefined references in the PDF.

---

## 2. Remaining

### 2.1 One word, two places — §1 and the Conclusion contradict §5.3

§5.3 now says explicitly: "**ordering is not a *requirement* everywhere** — what generalises is
that reversing the pair costs accuracy, not that the model cannot proceed without it." §6.1 was
updated to match. §1 and the Conclusion were not:

- §1: "Three results do hold everywhere: the inference is one step deep and **requires** the final
  rule to *follow* the premise it fires on"
- Conclusion: "The inference is one step deep, and **requires** the rule to follow its premise."

This is the front-matter-lags-the-body pattern from rounds 2–4, and this time the sentence §5.3
wrote to forbid it is two pages away. Gemma answers correctly on $84.9\%$ of rule-before items —
"requires" is false there on the paper's own numbers.

Suggested: "…is one step deep, and is degraded when the final rule precedes the premise it fires
on" — which is what holds on all three checkpoints and is what §5.3 and §6.1 now say.

### 2.2 `tab:arms` was displaced to the appendix

At r5 the ten-arm × three-checkpoint grid with both validity-share rows was in the body. It is now
at line 1019 in the appendix, while the new `tab:scale` (6 rows) took a body slot. But `tab:arms`
is the table §5.2 quotes its primary contrast from and the one §5.4's entire "which baseline"
argument rests on — both of the paper's central quantitative claims. The body now holds
`fig:factorial`, `tab:detection`, `tab:models` and `tab:scale`; `tab:arms`, `tab:edges`, `tab:sdt`,
`tab:panels` and four of five figures are in the appendix.

If the page budget forces a choice, `tab:arms` should displace `tab:scale` rather than the reverse
— the scale extension is a bounding result and reads fine from its five inline numbers; the
decomposition grid does not. §2 remains four subsections of related work and is still the cheaper
cut.

### 2.3 Minor

1. **§5.3, "the published single draws, $+46.9$ and $+10.4$pp, fall inside their own ranges"** —
   names two of three. The bfloat16 draw is $+62.5$pp, inside $[+60.4, +63.5]$. Either name all
   three or write "each checkpoint's published draw falls inside its own range".
2. **Neither robustness study has a figure** (third round I've raised this). b18's gap-by-distance
   profile is 7 bins × 3 checkpoints in the JSON and the paper prints 2 of the 21 cells; a small
   panel would make "direction, not distance" visible rather than asserted. An authorial call, but
   the two studies now carrying §5.3 and §5.8 are the only results in the paper with no graphic.

---

## 3. Rubric

| Dimension | Weight | r6 | r7 |
|---|---|---|---|
| Novelty | Critical | 4/5 | **4/5** |
| Technical soundness | Critical | 5/5 | **5/5** |
| Significance | High | 4/5 | **4/5** |
| Experimental rigor | High | 5/5 | **5/5** |
| Reproducibility | Mod.–High | 5/5 | **5/5** |
| Clarity | Moderate | 3/5 | **4/5** ↑ both errors fixed, five stale claims closed, Setup reconciled; held off 5 by 2.1 and 2.2 |

| Venue dimension | r6 | r7 |
|---|---|---|
| Soundness (1–4) | 4 | **4** |
| Contribution (1–4) | 3 | **4** ↑ the runtime result is now reported at the weight it deserves, with the limit of its own coverage stated |
| Presentation (1–4) | 2 | **3** ↑ |
| **Overall (1–10)** | 7 | **7** |
| Confidence (1–5) | 5 | **5** |

Overall holds at 7. Contribution and presentation both went up; what keeps it off 8 is unchanged
and structural — one synthetic task family, models to 14.7B, no end-to-end pipeline, and a headline
mechanism number the paper itself declines to generalise.

---

## 4. Assessment

Seven rounds, and the pattern has held throughout: every objection either got fixed or got an
experiment run at it, and four times the experiment refuted the claim the paper had been making.
This round is the cleanest of them — two wrong numbers corrected, a finding promoted from a
Limitations paragraph to a Results subsection with its effect size and its own coverage gap stated,
five stale claims reconciled, and the two results I said were missing added with a table that makes
the harder reading ("14B does not work either") explicit.

What is left is one word in two sentences and one table in the wrong section. Fix §2.1 — the
Introduction and Conclusion should not say "requires" when §5.3 spent a paragraph establishing that
it does not — and this is done.

**Recommendation: accept.**
