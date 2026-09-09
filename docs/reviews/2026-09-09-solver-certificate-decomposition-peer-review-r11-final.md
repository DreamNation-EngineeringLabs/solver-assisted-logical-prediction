# Peer review, round 11 (final) — "What a Language Model Does with a Solver Certificate"

- **Manuscript:** `paper/final/paper.pdf`, commit `23d63f5` "r10 copy items: the four remaining,
  all confirmed before fixing"
- **Shape:** 11 pp — **body ends on p9**, references p10–11, no appendix, all four figures and all
  five tables in the body
- **Recommendation: ACCEPT.** No remaining review items. Rubric **7/10**.

---

## 1. All four round-10 items fixed, and fixed correctly

1. **"degenerate" in the abstract** → "falls below the viability floor under another, on identical
   weights". The term now appears three times in the paper, all in its technical sense
   (single-label collapse at $0.000$), and Phi-4-mini's $0.219$ is described in the paper's own
   vocabulary. Verified: no remaining misuse.
2. **§5.1's depth claim is scoped, and the sharper datum is stated.** "depth is a cliff rather than
   a slope **on the Qwen checkpoints**: withholding two steps instead of one scores identically to
   supplying no certificate, $0/96$. Gemma-3-4B is not in that position, and **the direction there
   is worse than null**: a two-step-truncated certificate leaves it at $4/96$ against $22/96$
   unaided." That is the claim, the scope and the more interesting fact, in three clauses.
3. **The verifier count is corrected to ten**, the partition is right, and the enumeration names
   the checks it used to omit: "a recomputed digest for every one of the $34{,}584$ receipts, all
   sixty cells of `tab:models`, and the ten printed properties of the worked example in
   `tab:stimulus`."
4. **The three dead labels are gone** (`sec:decomposition`, `sec:closure`, `sec:limits`).

## 2. What I verified this round

- **`verify.py --all`: 10/10 pass.**
- **The new partition claim is accurate.** "Eight of its ten claims re-derive from the receipts and
  the sealed panels; the cross-model mean and the model table read released analysis files." Checked
  against the source: `cross-model` and `model-table` read `b16_analysis_v2_allarms.json`; the other
  eight (including `census`, which counts receipts on disk and compares to the census file, and
  `digests`, which recomputes all $34{,}584$) go to receipts. The previous draft had `census` on the
  wrong side of that line; this one has it right.
- **"the ten printed properties" is literally ten.** The `stimulus` check asserts exactly ten named
  properties of item `b15-4ef53c71988aec0e` against the sealed panel and authority — including that
  `broken_chain` and `truncate_1` both stand at 4 entity mentions and 8 lines. That is the paper's
  central control property, machine-checked on the item the reader is shown. It is a good idea and I
  had not thought to ask for it.
- **Labels:** 11 defined, zero undefined, zero orphaned.
- **Bibliography:** 39 entries, all 39 cited, none missing.
- No `??` in the rendered PDF; no lowercase-after-period anywhere; em-dashes steady at 9, all in
  captions and tables.
- **Body ends on p9.** The "back inside 9 pages" goal is met with every float in the body and no
  appendix — which is the version of that goal worth having.

Nothing new surfaced. I looked for it: re-ran the full mechanical suite, re-checked the four edited
passages against the released JSONs, and read the diff line by line. This round is a clean close.

## 3. Two packaging nits, not paper issues

Neither affects the manuscript; both affect what a reviewer unpacks.

1. **Two unused figure files ship in `paper/final/figures/`** — `arm_decomposition.png` and
   `substrate_size_curve.png`, orphaned when their figures were cut in favour of `tab:arms` and
   `tab:models`. Harmless, but a reviewer who diffs the directory against the paper will wonder
   which figure they were meant to be looking at.
2. **Build artifacts are tracked in `paper/final/`** — `paper.aux`, `paper.bbl`, `paper.out`, plus a
   `.DS_Store`. `paper.bbl` is worth keeping if the submission needs to compile without BibTeX;
   the other three are not.

## 4. Rubric

| Dimension | Weight | Score |
|---|---|---|
| Novelty | Critical | **4/5** |
| Technical soundness | Critical | **5/5** |
| Significance | High | **4/5** |
| Experimental rigor | High | **5/5** |
| Reproducibility | Mod.–High | **5/5** |
| Clarity | Moderate | **5/5** |

| Venue dimension | Score |
|---|---|
| Soundness (1–4) | **4** |
| Contribution (1–4) | **4** |
| Presentation (1–4) | **4** |
| **Overall (1–10)** | **7 — Accept** |
| Confidence (1–5) | **5** |

Unchanged from round 10, and for the reasons given there: what holds the overall at 7 is
structural, not editorial. One synthetic task family, models to $14.7$B, forced-choice
single-token scoring that the paper itself notes "no deployed solver-augmented setup does", and a
positive claim set of an instrument plus a non-transfer result plus one negative reliability
finding. Every sub-score that editing can move is now at or near its ceiling.

## 5. Assessment

Eleven rounds. The manuscript that started as a single-checkpoint mechanism claim with three of
five arms withheld, an undisclosed interaction term, a ceiling-limited factorial presented as a
channel decomposition, and an attribution its design could not support is now a nine-page paper
whose thesis is that the instrument works and almost nothing it returns transfers, with every
figure and table in the body, ten machine-checked headline claims, and a limitations section that
discloses a malformed regex that never fired.

Along the way it withdrew a headline result on its own analysis, relabelled a bootstrap interval
because the acceleration term was not defined for the statistic, walked back its own sealing
guarantee to what the code enforces per runner, and disclosed a $d'$ ceiling that eight of its own
cells sit on. Four of those corrections I had not asked for, and two of them corrected claims I had
explicitly endorsed. That is the apparatus working on its author rather than only on its reviewer,
which is the thing the paper argues for.

**Recommendation: accept.** No further review items. The two packaging nits in §3 are for whoever
assembles the supplementary.
