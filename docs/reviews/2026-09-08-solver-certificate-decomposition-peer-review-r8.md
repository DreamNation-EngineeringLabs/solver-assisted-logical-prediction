# Peer review, round 8 — "What a Language Model Does with a Solver Certificate"

- **Manuscript:** commit `92a70c9` (humaniser pass) on top of `3074988` (round-7 minors)
- **Recommendation: ACCEPT.** Rubric unchanged at **7/10**. Nothing here blocks; the remaining
  items are style and float placement.

---

## 1. The humaniser pass did not damage the paper

This is the thing worth checking first, because the usual failure mode of a humanising pass on a
numbers-heavy manuscript is claim drift under rewording. It did not happen. I read all 24 changed
passages against the round-7 text:

- **No number changed.** `verify.py --all` still passes **7/7**, recomputing from receipts.
- **No claim boundary moved.** No hedge added, none removed, no scope widened.
- The two "not X but Y" rewrites preserve meaning exactly. "not an interface that cannot express
  three outcomes, but one the proof state breaks" became "it can express three outcomes, and the
  proof state is what breaks it" — same content, and the active version is better. Likewise "This
  is not a statistical subtlety but an identification one" → "This is a problem of identification,
  not of statistics."
- One rewrite is a clear improvement on its original: §3.2's `same_entity_irrelevant` sentence,
  where the dashed parenthetical became two clean clauses.

Mechanically clean throughout: no orphan floats (all 23 labels referenced), no
lowercase-after-period, bibliography 39/39 with no dangles, no undefined references in the PDF,
body ends p10.

## 2. All round-7 items closed

- **The false "requires" is gone from both places.** §1 line 121 and the Conclusion line 859 now
  read "is degraded when the final rule precedes its premise", matching §5.3's "ordering is not a
  *requirement* everywhere" and §6.1. The front matter and the body finally agree on this.
- **§5.3 names all three published draws** ($+46.9$, $+62.5$, $+10.4$pp), each inside its own range.
- **b18 has a figure** (`fig:order`) — three rounds after I first asked. It plots the gap profile
  for all seven gaps on all three checkpoints with each checkpoint's canonical-order score dashed,
  annotates "n falls 216 to 25" so the thin cells are visible on the figure itself, and uses a
  colourblind-safe palette. The caption carries the direction numbers and the Gemma caveat
  ("reversal degrades rather than prevents"). Good figure and a good caption.
- **`tab:arms` is back in the body.** See §4 for the cost.

---

## 3. The pass did half the job — and the tell moved rather than left

The commit says "cut the em-dash habit". Measured on the body (abstract through Conclusion,
~51k chars, ≈9 pages):

| Pattern | Count | Per page |
|---|---|---|
| Em-dashes (`---`) | **31** | ≈3.4 |
| Colon-led appositives (`word: lowercase…`) | **41** | ≈4.6 |
| "rather than" | **25** | ≈2.8 |
| "not X but Y" | 1 | — |
| "Two/Three X hold/follow" scaffolds | 3 | — |
| delve / leverage / underscore / notably / moreover / that said / worth noting | **0** | — |

Three readings of that:

1. **31 em-dashes survive**, and **nine of them are in §5.7 alone** ("Which models can serve as the
   interface"), which the pass never reached. The pass removed roughly 20 and left more than it
   removed, concentrated in one section. If the goal is to cut the habit, §5.7 is where the work is.
2. **The fingerprint redistributed rather than dissolved.** Em-dashes became colons and commas, so
   the dominant sentence shape is now the colon-led appositive (41 instances) and the default
   contrastive is "rather than" (25). Both are legible on their own; at ~4.6 and ~2.8 per page they
   read as a single uniform hand, which is the thing a humanising pass is supposed to break. The
   lever from here is sentence-shape variety — vary clause order, let some sentences be short and
   declarative, let a few contrasts be carried by a plain "but" — not further punctuation swaps.
3. **The register was never in the crude failure mode.** Zero instances of the standard lexical
   tells. Worth knowing, because it means the remaining signal is structural, not vocabulary, and
   no thesaurus pass will touch it.

### Two places the de-dashing hurt readability

- **§3.4.** "One arm below scores $50.0\%$, apparent chance, with an identical $9/96$ ``Yes'' rate
  in *both* classes, that is $d' = 0.00$: no discriminative signal whatever, at or below the trivial
  always-one-label strategy." Four commas, a "that is" splice, then a colon. The dashes were
  carrying real structure here; a parenthesis around "apparent chance" restores it without
  reinstating the habit.
- **Abstract.** "We build one that does, holding every surface property fixed while destroying
  validity alone, and apply it across four sealed experiments…" — "and apply it" now reaches back
  across a comma-parenthetical, so the sentence briefly parses as a list. Parentheses, or split the
  sentence.

Minor: the pass collapsed several paragraphs onto single very long `.tex` lines, which will make
future diffs noisier than they need to be. Cosmetic, but re-wrapping costs nothing.

---

## 4. The float trade was a rotation, not a fix

`tab:arms` is back in the body, which is right — §5.2 quotes its primary contrast and §5.4's whole
"which baseline" argument rests on it. But it came in by pushing **`tab:detection` out to the
appendix**, so the body-float count is unchanged:

- **Body (3):** `fig:factorial`, `tab:arms`, `tab:models`
- **Appendix (10):** `tab:panels`, `tab:edges`, `tab:sdt`, `tab:scale`, `tab:detection`, `fig:arms`,
  `fig:replication`, `fig:detection`, `fig:order`, `fig:size`

Three floats for eight Results subsections. The detection finding — one of the three the paper says
holds on *every* checkpoint — now has neither its table nor its figure in the body. §5.8, the
runtime result the abstract promotes to the headline, has no float at all. §5.3's new figure is
also in the appendix.

Rotating primary results through a fixed budget does not solve this; the budget is the problem.
§2 remains four subsections of related work and is still the cheapest cut available — a third of
its length would buy back `tab:detection` and `tab:scale` without losing a citation.

## 5. One figure note

`fig:order` plots the null and not the positive. The subsection is titled "Direction separates the
arms; distance does not", and the figure shows only the flat distance profile; the direction result
— the one carrying $p = 1.6\times10^{-11}$ — appears only as text in the caption. A second panel
with the six rule-after / rule-before values would make the figure match the claim it illustrates.
The caption is doing that work well in the meantime, so this is a suggestion, not a defect.

---

## 6. Rubric

| Dimension | Weight | r7 | r8 |
|---|---|---|---|
| Novelty | Critical | 4/5 | **4/5** |
| Technical soundness | Critical | 5/5 | **5/5** |
| Significance | High | 4/5 | **4/5** |
| Experimental rigor | High | 5/5 | **5/5** |
| Reproducibility | Mod.–High | 5/5 | **5/5** |
| Clarity | Moderate | 4/5 | **4/5** — the "requires" fix and the new figure offset the two comma pile-ups and the thin body |

| Venue dimension | r7 | r8 |
|---|---|---|
| Soundness (1–4) | 4 | **4** |
| Contribution (1–4) | 4 | **4** |
| Presentation (1–4) | 3 | **3** |
| **Overall (1–10)** | 7 | **7** |
| Confidence (1–5) | 5 | **5** |

Overall holds at 7 for the same structural reasons as the last three rounds: one synthetic task
family, models to 14.7B, no end-to-end pipeline, and a headline mechanism number the paper itself
declines to generalise. None of those is fixable by editing.

---

## 7. Assessment

The substantive review closed at round 7 and nothing since has reopened it. This round's job was to
confirm that a style pass over a paper whose entire argument is "check your numbers" did not
disturb the numbers, and it did not: every value still re-derives from the receipts, and every
claim boundary the previous seven rounds negotiated is intact. The last two review items also
landed — the false "requires" is gone from the Introduction and Conclusion, and the permutation
study finally has a graphic.

On the humanising itself: it removed the most visible marker and left the underlying one. Thirty-one
em-dashes remain, nine of them in a section the pass skipped, and the ones it did remove turned
into colons and commas, so the paper now has 41 colon-appositives and 25 "rather than"s carrying
the same uniformity the dashes used to. The absence of every crude lexical tell means the remaining
signal is sentence architecture, which is a harder and more interesting edit than punctuation.

**Recommendation: accept.** Optional before submission: sweep §5.7's nine em-dashes, restore
parentheses in the two sentences at §3.2 above, and buy `tab:detection` back into the body out of
§2's length.
