# Peer review, round 10 — "What a Language Model Does with a Solver Certificate"

- **Manuscript:** `paper/final/paper.pdf` (moved from `paper/solver-certificate-decomposition/final/`),
  commit `ccd6373`; 21 commits since round 9
- **Shape:** 11 pp, no appendix, every figure and table in the body (was 15 pp with a 10-float appendix)
- **Recommendation: ACCEPT.** Four items, all copy-level. Rubric **7/10**, Clarity up to 5/5.

---

## 1. This is the best version by a wide margin, and the trimming made it more honest

Cutting a paper in half usually costs caveats. This one gained them. The thesis is now stated as
what the programme actually found: **"The instrument works, and almost nothing it returns
transfers."** That was previously distributed across eight Results subsections as a set of
qualifications; as a headline it is both more accurate and more useful. Related Work went from four
subsections to four dense paragraphs with every citation intact (39/39). The new `tab:stimulus`
shows the reader what the model actually sees, which nine rounds of review had not asked for and
which the paper needed. Em-dashes are down from 32 to **9**.

The new motivating paragraph is the one the paper had been missing: "A model completing a supplied
inference has some purchase on whether that inference is sound; a model matching surface
co-occurrence has none, and anything built on it inherits the solver's errors in silence."

## 2. Six self-corrections, two of which correct me

**The detection refutation is withdrawn.** §5.3: abstention falls $37.5$ and $32.8$pp against
`none` and `irrelevant` but **rises $31.2$pp against the surface-matched `truncate_1`** — "the sign
is a function of the reference, and neither reference is clean. We draw no conclusion from it and
withdraw the claim that it refutes detection."

I endorsed that refutation from round 2 through round 8 and never asked what happened against the
matched valid arm, which is the one comparison the surface-matching design exists to license.
Verified: `truncate_1` 21 `Unknown` of 192 against `broken_chain`'s 81, so $+31.25$pp. The
withdrawal is correct and I was wrong to accept the claim.

**The share interval is relabelled from BCa to percentile**, with the reason given: the statistic
is a ratio of paired differences, for which the acceleration term is not defined. I asked for a
ratio interval at round 2 and took "BCa" at face value without checking that BCa applies to it.
Values are unchanged ($[94.4, 100.0]$); only the label and the justification. And the paired
*difference* correctly keeps its BCa interval, so the two cases are properly distinguished rather
than relabelled wholesale.

**$d'$ censoring disclosed:** "At $n = 96$ the loglinear correction censors $d'$ at $\pm 5.13$ and
eight cells of `tab:arms` sit on it, so $d'$ differences involving a saturated arm are bounds." I
verified those $d'$ values across five rounds without noting the ceiling.

**The sealing claim is walked back to what the code does.** Only the validity control and the model
sweep "refuse a panel whose hash does not match, while the others record the hash without
enforcing it", and the authority is opened after the receipts "by convention in the analysis order
rather than by a gate in the code". Earlier drafts asserted enforcement flatly. This is the paper
weakening its own strongest process claim on its own initiative.

**The reanalysis's defect list went from three to five**, adding a release "as a flat receipt export
with no sealed panel, so its answer key is reconstructed from those identifiers", and a screen for
response-token leakage "that was a malformed regular expression and never fired (the released
certificates contain none, checked after the fact)".

**A new ecological caveat:** "Every response is a forced choice among verified single-token
candidates, which no deployed solver-augmented setup does."

Also new and unprompted: the `irrelevant` control is not inert on a competent model — it costs
Gemma 20 of its 22 unaided successes, "so any effect measured against it there is inflated"; a
*second* prespecified criterion is disclosed as gamed (the $20$pp paired `full − none`, met by five
of ten under Holm, two of which the replacement floor rejects); and Phi-4-mini's absence from the
validity-control arms is explained rather than left as a gap.

## 3. Round-9 items: all three fixed as suggested

- **"twelve models"** throughout, including contribution list and Conclusion.
- **`tab:models` carries minimum per-class recall in every cell**, with bold marking the $0.50$
  floor "so `viable in` is derivable from the cells beside it" — exactly the column I proposed
  instead of reinstating `tab:scale`.
- **The scale-extension rows are shaded**, with "the parameter ladder continues, the numbers are
  not comparable across the rule" — the visual boundary I asked for.
- The Conclusion's two worked cases are back: "two criteria we had prespecified were gamed by label
  collapse, and a baseline arm at $50.0\%$ had $d' = 0.00$."

## 4. Independently verified

- `verify.py --all` — **10/10 pass**, up from 7 claims to 10, adding `digests` (recomputes every
  receipt digest), `model-table` (all 60 cells of `tab:models`) and `stimulus` (the worked example).
- **45 of the 60 new `tab:models` cells** checked by hand against `b16_analysis_v2_allarms.json`
  and `b19_scale_extension_v1.json`: **zero mismatches**.
- `tab:sdt`'s `none` $d'$ corrected from $-0.26$ to $-0.25$. The loglinear value is $-0.2546$, so
  the new figure is right and the old one was wrong for nine rounds. I checked that table repeatedly
  and did not catch it.
- Bibliography 39/39, no undefined references, no `??` in the PDF.

---

## 5. Remaining — four items, all copy-level

### 5.1 The Reproducibility Statement undercounts its own verifier

It says "Five of its **seven** claims re-derive from the receipts and the sealed authority", then
enumerates seven under `--all`. `verify.py --list` reports **ten**, and the three the paper omits
are among the most valuable: `digests`, `model-table` and `stimulus`. A reviewer who runs `--all`
sees ten OK lines beside a paper claiming seven — which reads as staleness in the one paragraph
whose whole purpose is to be checkable. Fix the count and name the three; `model-table` in
particular (60 cells, machine-checked) is worth advertising.

### 5.2 "degenerate" is used against the paper's own definition, in the abstract

"one model is a usable interface under one inference stack and **degenerate** under another, on
identical weights" refers to Phi-4-mini at $0.219$ minimum per-class recall. The paper's three
other uses reserve "degenerate" for label collapse at $0.000$ ("four responders degenerate in
every arm", "Llama-3.1-8B is degenerate in every arm"), and `tab:models` bolds only the rows that
clear the floor. $0.219$ is **below the floor**, which is the paper's own term for it. As written
the abstract overstates the case it does not need to overstate.

### 5.3 §5.1's depth claim is the one unscoped spot left

"And depth is a cliff rather than a slope: withholding two steps instead of one scores identically
to supplying no certificate." True on both Qwen checkpoints, false on Gemma-3-4B, where
`truncate_2` is $4/96$ against $22/96$ unaided. The abstract scopes it ("one step on two
checkpoints and not on a third") and Limitations scopes it; §5.1 does not.

The direction is worth stating rather than just scoping: on Gemma a two-step-truncated certificate
leaves it **worse than no certificate at all** ($4$ against $22$). That is a sharper datum than
"not in that position", and it belongs in the Results where the cliff is claimed.

### 5.4 Three dead labels from the restructure

`sec:closure`, `sec:decomposition` and `sec:limits` are defined and never referenced. Harmless;
delete or use.

---

## 6. Rubric

| Dimension | Weight | r9 | r10 |
|---|---|---|---|
| Novelty | Critical | 4/5 | **4/5** |
| Technical soundness | Critical | 5/5 | **5/5** — held at the ceiling, but the *disclosure* quality rose materially: the sealing walk-back, the $d'$ censoring, the BCa→percentile correction and the withdrawn refutation were all volunteered |
| Significance | High | 4/5 | **4/5** |
| Experimental rigor | High | 5/5 | **5/5** |
| Reproducibility | Mod.–High | 5/5 | **5/5** — `verify.py` at 10 checks including all 60 table cells is past the ceiling |
| Clarity | Moderate | 4/5 | **5/5** ↑ 11 pp, no appendix, every float in the body, thesis stated as the finding, 9 em-dashes |

| Venue dimension | r9 | r10 |
|---|---|---|
| Soundness (1–4) | 4 | **4** |
| Contribution (1–4) | 4 | **4** |
| Presentation (1–4) | 3 | **4** ↑ |
| **Overall (1–10)** | 7 | **7** |
| Confidence (1–5) | 5 | **5** |

**On not raising the overall to 8.** I considered it and decided against, and the reasoning matters
more than the number. What improved this round is presentation and disclosure, both of which the
sub-scores now reflect. What holds the overall at 7 is unchanged and structural: one synthetic task
family, models to $14.7$B, forced-choice single-token scoring that the paper itself says "no
deployed solver-augmented setup does", and — after the withdrawal — a positive claim set consisting
of an instrument plus a non-transfer result plus one negative reliability finding.

The honest test is whether a reviewer seeing only this version, with no knowledge of the previous
nine, would score it 8. I do not think so: they would find an exemplary, narrow diagnostic paper
and land at 7. Scoring 8 would be rewarding the trajectory rather than the artifact, and the
trajectory is not what the venue is buying.

---

## 7. Assessment

Ten rounds, and the interesting thing about this one is that the paper found four problems I had
not, two of them in claims I had explicitly endorsed. The detection refutation was the paper's
cleanest-looking positive result and it is now withdrawn on the correct ground — that the sign
depends on which reference you pick, and the matched reference gives the opposite answer. A BCa
label I accepted is now a percentile label with a reason. A $d'$ ceiling I verified around is now
disclosed as a ceiling. A sealing guarantee that read as absolute now describes what the code
actually enforces, per runner.

That is what the sealed-receipt apparatus was built to make possible, and it is worth saying that
the apparatus caught its author, not just its reviewer. The trimming pass, which I expected to cost
caveats, added six.

What remains is a count in the Reproducibility Statement, a word in the abstract, a clause in
§5.1, and three unused labels.

**Recommendation: accept.**
