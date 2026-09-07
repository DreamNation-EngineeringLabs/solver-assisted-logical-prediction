# Peer review, round 5 (final) — "What a Language Model Does with a Solver Certificate"
## An Answer-Evidence Decomposition Across Ten Models

- **Manuscript:** `paper/solver-certificate-decomposition/final/paper.pdf`, 14 pp incl. appendix,
  commit `e6af322` "Round-4 proofing"
- **Reviewer method:** `cognitive-core/.claude/skills/peer-review` (Stages 1–7); rubric per
  `venue-templates/references/reviewer_expectations.md` § "ML Conferences (NeurIPS, ICML, ICLR)"
- **Prior rounds:** r1 (2026-09-04), r2, r3, r4 (2026-09-07)
- **Recommendation: ACCEPT.** Two cosmetic typos to fix at proof; nothing else outstanding.

---

## 1. Rubric

### 1.1 Reviewer priorities (weights per `reviewer_expectations.md`)

| Dimension | Weight | Score | Basis |
|---|---|---|---|
| **Novelty** | Critical | **3.5 / 5** | The answer-evidence 2×2 and the surface-matched invalidity control are new *as controls* in this literature, and the per-item underdetermination certification is the part nobody else supplies. But the truncation and mistake-injection manipulations are adapted from \citet{lanham2023measuring}, and this is a measurement paper — no new method, model or capability. Real but modest. |
| **Technical soundness** | Critical | **5 / 5** | Sealed hash-stamped panels; per-response SHA-256 receipts; answer authority opened only after every receipt exists; forward-closure certifier validated three ways (23,240/23,240 public corpus, nine adversarial classes, differential test against an independently written engine on the actual nonce panels) with the tautology limit of the first stated in the authors' own words; SDT reported alongside accuracy everywhere; exact McNemar; BCa bootstrapped over the *ratio* not its numerator; Holm within declared families; tie-breaking documented and counted (2 in 5,760); degenerate responders identified and excluded from the cross-model mean; both share denominators reported. Across five rounds I re-derived every reported number from the released artifacts and broke none. |
| **Significance** | High | **3.5 / 5** | The corruption result — 189/186/192 of 192 items followed to the wrong answer given a fabricated final rule — is a genuinely consequential reliability finding for the whole solver-in-the-loop class, and "your same-shape irrelevant control does not rule out answer reading" is directly actionable for anyone reporting tool-augmented gains. Bounded by scope: one synthetic task family, 0.5–7.6B models, no frontier model, no end-to-end pipeline, and the paper itself declines to generalise its central number. A methodological warning plus a reliability result, not a result that changes what gets built. |
| **Experimental rigor** | High | **5 / 5** | Four sealed experiments, 20 model-runs, 18,840 scored responses. Ten matched arms on three checkpoints; ten models × five arms; a three-candidate detection test plus its own `none` abstention floor. The baselines are the right ones and *both* are reported. Ablations are the substance of the paper, not an appendix. One gap: no ten-arm b15 run on Phi-4-mini, so the share is characterised on two families rather than three. |
| **Reproducibility** | Mod.–High | **5 / 5** | Best-in-class. Every number re-derivable from a fresh unpack with no network, no weights and stdlib-only audits; the audit count is *generated* by `scripts/census_receipts_v1.py` at compose time rather than typed into the prose; both superseded criteria retained in the released results rather than deleted. I independently reproduced the 18,840/20 census, both Gemma shares, the 20-of-22 overlap, all six b17 deltas, the ten-model means on both subsets, and the tie count. |
| **Clarity** | Moderate | **4 / 5** | Claim boundaries stated at every point of use; post hoc analyses labelled where used, not only in Limitations; tables carry both baselines; figures now carry the qualifications (Fig. 1 annotates the interaction and ceiling, Fig. 4 marks both abstention baselines). Held back by float placement — `tab:edges` and four of five figures sit in the appendix while the body argues from them — and two residual typos. |

### 1.2 Venue scoring dimensions

| Dimension | Range | Score |
|---|---|---|
| **Soundness** | 1–4 | **4** — technically correct; five rounds of adversarial number-checking found no error |
| **Contribution** | 1–4 | **3** — an adoptable control and one consequential negative result, in a narrow setting |
| **Presentation** | 1–4 | **3** — clear and honest; float placement and two typos keep it from 4 |
| **Overall** | 1–10 | **7 — Accept** |
| **Confidence** | 1–5 | **4** — artifacts verified directly; not a specialist in neurosymbolic pipelines |

**Calibration note.** 7 is above the acceptance bar, not a courtesy. It is not 8 because the scope
is one synthetic task family with sub-8B models and the headline mechanism number is explicitly
non-general. It is not 6 because the rigor, the artifact quality and the negative results are
clearly above what a typical accepted paper in this area delivers — this manuscript's audit trail
is stronger than most published work it cites.

### 1.3 Peer-review stage coverage

| Stage | Verdict |
|---|---|
| 1. Initial assessment | Pass — scope, venue fit and claim shape all coherent |
| 2. Section-by-section | Pass — abstract matches body (fixed r3–r4); Setup describes all four experiments; Limitations names quantisation, prompt format, single permutation, prior report, ceiling, non-randomised model factor |
| 3. Methodological / statistical rigor | Pass — see 1.1 Technical soundness |
| 4. Reproducibility & transparency | Pass — see 1.1 Reproducibility |
| 5. Figures & data presentation | Pass — colourblind-safe after r3 (hatch + colour redundantly encode viability); Fig. 1 draws the baseline it claims; no integrity concerns |
| 6. Ethics | N/A — no human/animal subjects; AI-Use Statement present and specific |
| 7. Writing quality | Pass with two typos (§2.1) |

---

## 2. Round-4 items: all six fixed

| r4 item | Fix |
|---|---|
| 1. `tab:models` orphaned | §5.6: "\Cref{tab:models} reports all five arms for all ten models, with the per-arm verdict" |
| 2. `fig:size` orphaned | Same sentence: "\cref{fig:size} plots the same data ordered by parameter count" |
| 3. Dead `sec:tenmodel` label | Removed |
| 4. Two-vs-three count contradiction | Conclusion now "**Three** findings hold on every checkpoint", matching §1 |
| 5. Power treated as binary | New paragraph: "Power is a gradient, not a switch… 4-bit had $79.7$pp available and used $47\%$; bfloat16 had $21.4$pp and used $17\%$; Gemma-3-4B had $0.5$pp — which is why its delta is uninformative and its `Yes` count is not." All three percentages verified correct. |
| 6. Conclusion lost its examples | Restored as its own paragraph, both criteria named: the $50.0\%$/$d'=0$ arm and the all-`Unknown` viability threshold |

**Verified clean this round:** every `\label` has at least one reference (zero orphan floats);
no `??` in the rendered PDF; no duplicate `\usepackage`; bibliography 39 entries, all 39 cited,
none missing; 14 pp.

---

## 2.1 Remaining — two typos, fix at proof

1. **`fig:replication` caption, line 997:** "…against what the model manages unaided**. the** two
   denominators coincide…" — full stop followed by a lowercase sentence. Capitalise or make it a
   semicolon. (This is the only lowercase-after-period in the file; I checked all of them.)
2. **Duplicate `\looseness=-1`, lines 889–890.** Harmless to output, but delete one.

Optional, purely cosmetic: prose uses `gemma-3-4b` at lines 137, 846 and 984 and `Gemma-3-4B`
twelve times elsewhere. Pick one.

---

## 3. Assessment

Five rounds ago this was a single-checkpoint mechanism claim with three of five Experiment-3 arms
withheld, an undisclosed −29.2pp interaction, a ceiling-limited 2×2 presented as a channel
decomposition, an attribution ("the model detects a broken chain") its design could not support,
a point-estimate headline with no interval, a certifier validation that was closer to tautological
than independent, and an undisclosed prior report. All of that is now either fixed, measured, or
disclosed — and in four cases the authors fixed it by running the experiment that refuted their
own claim and then leading with the refutation:

- b17/b17b turned "the model detects invalidity" into "**detection is refuted**", on three
  checkpoints against two baselines, with the no-power case on Gemma called out as a no-power case.
- The b15 replication turned a $98.3\%$ validity share into a checkpoint-specific quantity, and
  the added `none` baseline then moved the contrary case from $40.4\%$ to $51.4\%$ — a correction
  *against* the paper's own rhetorical interest, which the paper makes anyway.
- The all-arms b16 release turned a "substrate-size floor" into "viability is a property of
  (model × arm)", with proof state *degrading* three of ten interfaces.
- Excluding the degenerate responders withdrew the "less than half" comparison the paper had
  wanted to make.

That behaviour is what the sealed protocol was built to enable, and it is rarer in practice than
in principle. The paper is stronger for having lost four arguments to its own data.

The contribution stands as stated. A control that separates answer-reading from state-use, with
per-item certification that the invalid arm really is undetermined. A demonstration that what the
control returns is checkpoint-specific, so single-model mechanism claims in this literature —
including the authors' own first draft — should not be generalised. And three negative results
that held everywhere they were applied: the inference is one step deep, it is completion rather
than detection, and nothing defends against a corrupted apparatus. The last of those is the
finding the solver-in-the-loop literature should be made to read, and the paper is right to end
on it.

**Recommendation: accept.** Overall 7/10, soundness 4/4, contribution 3/4, presentation 3/4,
confidence 4/5. Fix the two typos in §2.1 at proof.
