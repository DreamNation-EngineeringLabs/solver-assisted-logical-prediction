# Peer review, round 9 — "What a Language Model Does with a Solver Certificate"

- **Manuscript:** commit `08ae0de` "fix six internal inconsistencies, drop redundant tab:scale"
- **Recommendation: ACCEPT.** Rubric unchanged at **7/10**. Five copy-level items, one of which is
  a wrong count.

---

## 1. Fixed

**The runtime factor is now consistent everywhere.** "Viability is a property of (model × arm ×
runtime), not of a model" appears identically in §5.7's bolded claim, `tab:models`' caption and
`fig:size`'s caption. The three-way formulation used to be in the abstract only.

**§4.1 covers the robustness studies** — "Every experiment and study here uses rule-chaining
queries…" replaces "All four experiments", which excluded b18 and b19.

**The model count is reconciled in §5.7** — "Experiment 3 scores ten models… and §5.8 adds two more
on a second runtime… (one of the ten does not load there)" — though see 2.1.

**`tab:models` absorbed the scale extension**, with the two new rows below a `\midrule` and an
explicit italic note: "scale extension, second runtime (§5.8); not directly comparable to the rows
above". Both rows' balanced accuracies verified against `b19_scale_extension_v1.json`
(Llama-3.1-8B 38.5/34.4/65.6/64.6/66.7; Qwen2.5-14B 57.3/35.4/80.7/70.3/82.8).

**§5.7 correctly distinguishes the table from the figure** — "`tab:models` reports all five arms
for every model… `fig:size` plots the ten ordered by parameter count."

Mechanically clean: `verify.py --all` **7/7**, no orphan labels, bibliography 39/39, no undefined
references, 15 pp with the body ending p10.

---

## 2. Introduced or reopened by this round's consolidation

### 2.1 "for eleven scored in all" undercounts — it is twelve

The paper scores **twelve distinct models**: ten on the first runtime (including Gemma-3-4B), and
eleven on the second (the nine that load, plus Llama-3.1-8B and Qwen2.5-14B). Eleven is the count
*on the second runtime*, not the total. `b19_scale_extension_v1.json` lists exactly those eleven;
Gemma is the twelfth and appears only on the first.

"For eleven scored in all" reads as a grand total, and contribution (v) in §1 — "a sweep over
eleven models" — has the same problem. Suggested: "twelve models in all: ten on the first runtime,
eleven on the second, nine in common."

### 2.2 The Conclusion dropped the two failed criteria again

It now reads "Two prespecified criteria failed here, caught only by reporting sensitivity alongside
accuracy, which we recommend as standard." The specifics are gone: no arm at $50.0\%$ with
$d' = 0.00$, no threshold maximised by answering `Unknown` to everything. I confirmed neither
string appears anywhere between `\section{Conclusion}` and the Reproducibility Statement.

**This is the second time this exact content has been lost to a compression pass** — I raised it at
round 4, it was restored, and it is out again. The abstract does not name them either, so the two
cases now survive only in §3.4 and §5.7. They are among the paper's most transferable
contributions: a reader who takes nothing else away should take away that a balanced-panel arm at
chance accuracy can have zero sensitivity, and that a single-class recall floor is gameable. Two
clauses.

### 2.3 Deleting `tab:scale` orphaned three numbers from every table

Consolidating was the right instinct, but the deletion cost more than the space it freed:

- **The harm ladder is now five unlabelled numbers in prose** — "the harm runs $0.000$, $0.000$,
  $-0.219$, $-0.688$, $+0.062$". To read them the reader must map five values onto Qwen2.5 rows
  that are scattered through a size-sorted table *and* are first-runtime rows, while the ladder is
  entirely second-runtime. The values correspond to nothing that can be looked up. The retained
  caveat ("the whole ladder on one runtime") states the problem without solving it.
- **Qwen2.5-14B's "$0.422$ and $0.484$" and Llama-3.1-8B's "$0.000$ throughout" are minimum
  per-class recalls**, and `tab:models` reports balanced accuracy only. Those figures are now in no
  table in the paper. §5.7 half-acknowledges it — "despite the balanced accuracy `tab:models`
  reports for it" — which reads as the authors noticing the gap without closing it.

Cheapest fix: add a min-per-class-recall column to `tab:models` (it is the quantity the viability
verdict is computed from, so the "Viable in" column currently rests on numbers the table does not
show). That would serve `tab:scale`'s purpose in the table that replaced it.

### 2.4 `tab:models` now presents two runtimes as one size ladder

The `\midrule` plus the italic note is the right mitigation, and it is explicit. But the `B` column
now runs 0.5 … 7.6, 8.0, 14.7 continuously, so a reader skimming the table gets exactly the
cross-runtime size comparison the note forbids — the note has to be read to be obeyed, and table
rows are the part people skim. Shading the block, or a `runtime` column, would make the boundary
visual rather than textual.

### 2.5 Em-dashes went up

Body count is **32**, against 31 before this commit. The Conclusion rewrite reintroduced a
parenthetical pair ("model-specific --- $98.3\%$ … another --- so we offer"). Small, but the stated
goal two commits ago was to cut the habit, and this round net-added one. The nine in §5.7 flagged
last round are untouched.

---

## 3. Standing item, unchanged

The body still carries **three floats** (`fig:factorial`, `tab:arms`, `tab:models`) against nine in
the appendix. Dropping `tab:scale` freed appendix space, not body space, so §5.6's detection result
— one of the three findings the paper says hold on every checkpoint — still has neither its table
nor its figure in the body, and §5.8's runtime result still has no float at all. §2's four
subsections of related work remain the cheapest source of the space.

---

## 4. Rubric

| Dimension | Weight | r8 | r9 |
|---|---|---|---|
| Novelty | Critical | 4/5 | **4/5** |
| Technical soundness | Critical | 5/5 | **5/5** |
| Significance | High | 4/5 | **4/5** |
| Experimental rigor | High | 5/5 | **5/5** |
| Reproducibility | Mod.–High | 5/5 | **5/5** |
| Clarity | Moderate | 4/5 | **4/5** — the runtime-consistency fix offsets the wrong count and the three orphaned numbers |

| Venue dimension | r8 | r9 |
|---|---|---|
| Soundness (1–4) | 4 | **4** |
| Contribution (1–4) | 4 | **4** |
| Presentation (1–4) | 3 | **3** |
| **Overall (1–10)** | 7 | **7** |
| Confidence (1–5) | 5 | **5** |

---

## 5. Assessment

The consolidation was the right call and the runtime factor is now stated the same way in all four
places it appears. What the pass cost is smaller than what it bought, but it is not nothing: one
count is wrong in two places, three quantities the prose asserts are no longer in any table, and
the Conclusion's two worked examples of degenerate measurement have been squeezed out for the
second time in five rounds.

That last one is the only item I would press on. The paper's most reusable advice is not the
decomposition — it is the pair of concrete cases showing how a headline number can be degenerate,
and a compression pass has now removed them twice. Whatever the page budget, those two clauses
should be treated as load-bearing.

**Recommendation: accept**, with 2.1 and 2.2 applied and 2.3 addressed by a column rather than a
reinstated table.
