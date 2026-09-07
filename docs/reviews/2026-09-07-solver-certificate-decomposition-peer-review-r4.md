# Peer review, round 4 — "What a Language Model Does with a Solver Certificate"

- **Manuscript:** `paper/solver-certificate-decomposition/final/paper.pdf` (14 pp incl. appendix),
  commit `1453cab` "Round-3 copy fixes: nine of ten"
- **Prior rounds:** `…-peer-review.md` (r1), `…-r2.md`, `…-r3.md`
- **Recommendation:** **Accept.** Nothing below is a review objection; items 1–2 are proofing
  defects introduced by this round's compression and should be fixed before submission.

---

## 1. Round-3 items: nine fixed, one declined

| r3 item | Status |
|---|---|
| 1. §4.1 "All three experiments" | Fixed — "All four experiments" |
| 2. Experiment 4 absent from Setup | Fixed — new §4.1 paragraph describing the rescoring, the byte-identical inputs, the instruction/candidate-set change recorded in the seal, and b17b's `none` arm; candidate sets now read "Experiments 3 and 4" |
| 3. `tab:panels` caption/table mismatch | Fixed — b17/b17b row added, caption now says Experiment 4 rescores Experiment 2's items |
| 4. Abstract asserted what §5.3 refuses | Fixed — "either $40.4\%$ or $51.4\%$ depending on whether the denominator is a same-shape control or the model's unaided score"; "exploits surface overlap heavily" is gone |
| 5. Abstract's detection delta was one checkpoint on an incomparable reference | Fixed — now "lowers abstention on every checkpoint and against both baselines, and the strongest substrate abstains on $0$ of $192$ broken certificates while completing $76$" |
| 6. §6.1 range didn't name its baseline | Fixed — "$40.4\%$ to $98.6\%$" against `irrelevant`, "$51.4\%$ to $98.6\%$" against unaided |
| 7. §5.2 order claim unscoped | Fixed — "Order matters \emph{on this checkpoint}… though §5.3 shows this too is checkpoint-specific" |
| 8. `fig:replication` single-baseline | Fixed — figure regenerated with "share 40.4% / 51.4% · vs irrelevant / vs none", caption rewritten |
| 9. `fig:detection` caption narrower than its figure | Fixed — caption now describes both baselines and the dotted/dashed marking |
| 10. `tab:edges` to the body | **Declined** (per commit message). Legitimate authorial call; it is cited 3× and lands on p12 |

The round-3 framing suggestion was also adopted, and adopted well: §5.5 now leads the Gemma
paragraph with "**On Gemma-3-4B the delta carries no weight, and we do not rest the claim on
it**… its $-0.5$pp is a no-power null", then gives the baseline-free composition evidence
(0 abstentions in 192, 76 completions) as the argument. The Conclusion was rewritten to lead
with the same fact.

Re-verified this round: bibliography still 39/39 with no dangles, no `??` or undefined
references in the rendered PDF, and no reported number changed except the added $51.4\%$
(previously verified against `b15_share_baselines_v3.json`).

---

## 2. Introduced by this round's compression

1. **`tab:models` (Table 4) is now referenced nowhere in the text.** The §5.6 rewrite that merged
   two paragraphs deleted the sentence "\Cref{tab:models} reports all five arms for all ten
   models." I checked every `\label` against every `\cref`/`\ref`: `tab:models` has **zero**
   references. This is the paper's largest results table and the direct answer to the withheld-arms
   problem from round 1 — an orphan float with no textual pointer, in a two-column layout where
   `[tb]` placement can drift away from the discussion. Restore a pointer.
2. **`fig:size` (Figure 5, p14) is also referenced nowhere.** Same cause: the earlier rewrite
   removed "both visible in \cref{tab:models} and \cref{fig:size}" and nothing replaced it. An
   unreferenced appendix figure is effectively unpublished, and some venues strip them at
   camera-ready. §5.6's "Viability is a property of (model × arm)" paragraph is where it belongs.
3. **`sec:tenmodel` is a dead label** — the round-2 self-`cref` was removed but the label stayed.
   Harmless; delete or use it.
4. **The "holds on every checkpoint" count disagrees with itself.** §1: "**Three** results do hold
   on every checkpoint: the inference is one step deep; it is not detection…; and none resists a
   corrupted apparatus." Conclusion: "**Two** findings hold on every checkpoint." Same set — the
   Conclusion merges one-step-deep with not-detection. Pick one count.
5. **§5.5 treats power as binary where it is a gradient.** "Where the deltas do have power they run
   against detection: $-37.5$ and $-3.6$pp versus \textsc{none}." The bf16 checkpoint's `none`
   abstention floor is $41/192$ ($21.4\%$), so the largest fall available to it was $-21.4$pp and
   it used $-3.6$ of that — 17% of the range, against the 4-bit checkpoint's $-37.5$ of an
   available $-79.7$ (47%). Grouping bf16 with 4-bit as "has power" overstates it; the honest
   reading is that power runs 4-bit > bf16 > Gemma ≈ none. The composition argument carries the
   section regardless, so this is one clause.
6. **The Conclusion's final merge cost content.** The measurement-lesson paragraph was folded into
   the preceding one mid-line and lost its specifics: the $50.0\%$-accuracy arm at $d' = 0.00$ and
   the viability threshold a single-label responder maximised are no longer named anywhere in the
   Conclusion — only alluded to as "Two prespecified criteria of our own failed here". Those two
   concrete cases are among the paper's more transferable contributions and the abstract does not
   name them either, so after this edit they appear only in §3.4 and §5.6. Also "We recommend it"
   now takes its antecedent from two clauses back. If the merge was for page budget, §2 remains
   the cheaper place to cut.
7. **`fig:replication`'s bars still show only one denominator.** The annotation now gives both
   shares, but the bar lengths ($+58.3$ / $+39.6$pp) are the `irrelevant` decomposition; the
   `none` decomposition is $+37.5$ / $+39.6$ of a $+77.1$pp total. One clause in the caption
   ("bars use the same-shape denominator; the second share re-divides by the unaided total")
   closes it.

---

## 3. Assessment

Four rounds in, every substantive objection has been closed with data rather than with wording,
and every number I have checked across those rounds has reproduced from the released receipts.
This round fixed nine of ten copy items and declined the tenth for a stated reason. What is left
is proofing residue from the compression pass: two primary floats lost their in-text references,
one self-inconsistent count, and a Conclusion paragraph that lost its examples to a page squeeze.
Items 1 and 2 are the ones I would insist on — an unreferenced Table 4 is exactly the kind of
detail that reads as carelessness in a paper whose argument is that it is careful.

**Recommendation: accept**, with items 1–6 applied as proofing corrections.
