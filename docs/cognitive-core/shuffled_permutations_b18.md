# b18: eight permutations, and adjacency measured rather than assumed

| | |
| --- | --- |
| Question 1 | `shuffled` was one seeded permutation per item. Is `+46.9`pp a stable estimate? |
| Question 2 | §6.1 claimed the model completes "when both premises are present **and adjacent**". Is that true? |
| Status | Run 2026-09-07 on all three b15 checkpoints, 9 arms x 192 items each |
| Verdict | Estimate stable. **Adjacency refuted; direction is the mechanism.** |

---

## Why question 2 needed asking

The manuscript asserted adjacency and had no measurement behind it. `shuffled`
destroys three things simultaneously:

1. the **gap** between the final rule and the premise it fires on,
2. the **order** of that pair, and
3. the sequence of everything else.

When accuracy collapses, none of the three can be blamed. "Order matters" was as
specific as the design allowed, yet §6.1 said something sharper.

## Design

Every `truncate_1` record is 8 sentences ending premise-then-rule:

```
...
7. Daelkruth is zaelbrom.            <- PREMISE
8. All zaelbrom people are gakaem.   <- FINAL RULE
Query: Daelkruth is gakaem.
```

Eight permutations per item, seeds derived from `2026090701-<task_id>-<i>`. For
each, the signed gap `position(rule) - position(premise)` is recorded in
`public/geometry.jsonl`, so accuracy can be read against gap and against
direction separately.

**Contradicted items end on a negated final rule** (`All X people are not <pred>.`)
rather than a positive one; the parser handles both and asserts it found exactly
one rule and one premise per item, on all 192.

## Decision log

| # | Decision | Reason |
| --- | --- | --- |
| 1 | 8 permutations, not 4 | 1,536 permutation-instances spread gaps 1-7 with 442 at gap 1 and 52 at gap 7 -- enough to read a curve |
| 2 | Record geometry at generation time | b15 never recorded where the two lines landed, which is why its single shuffle could not be analysed after the fact |
| 3 | `perm_identity` arm re-scores `truncate_1`'s exact bytes | A byte-faithfulness check. If it does not reproduce the b15 receipts, nothing else in the run is trustworthy |
| 4 | Seeds distinct from b15's | So `perm_1..8` are genuinely new draws, not a re-run of the published one |
| 5 | New script, not an edit to the b15 runner | Repo norm: b15 is frozen and hash-recorded |

---

## Results

**Control.** `perm_identity` reproduced the b15 `truncate_1` receipts **192/192 on
all three checkpoints**.

**Question 1 -- the estimate is stable.**

| Checkpoint | order effect over 8 permutations | published single draw |
| --- | --- | --- |
| qwen2.5-3b 4-bit | +41.7 … **+44.8** … +50.0 pp | +46.9 (inside) |
| qwen2.5-3b bf16 | +60.4 … **+61.5** … +63.5 pp | — |
| gemma-3-4b | +6.2 … **+11.5** … +13.5 pp | +10.4 (inside) |

**Question 2 -- adjacency is refuted; direction is the mechanism.**

Accuracy by |gap|, entailed subset:

| Checkpoint | gap 1 | gap 4 | gap 7 |
| --- | ---: | ---: | ---: |
| qwen2.5-3b 4-bit | 18.1% | 14.6% | 24.0% |
| qwen2.5-3b bf16 | 15.3% | 14.6% | 20.0% |
| gemma-3-4b | 94.9% | 92.7% | 92.0% |

No decay with distance on any checkpoint. But direction is decisive:

| Checkpoint | rule **after** premise | rule **before** |
| --- | ---: | ---: |
| qwen2.5-3b 4-bit | **26.8%** | 5.8% |
| qwen2.5-3b bf16 | **22.4%** | 4.8% |
| gemma-3-4b | **94.9%** | 84.9% |

Paired within item on the 4-bit checkpoint: 45 items favour rule-after, 2 favour
rule-before, 48 tie. Exact two-sided sign test **p = 1.6e-11**.

Distance carries almost nothing once direction is fixed: near (+1,+2) 29.8% vs
far (+3..+7) 23.6%.

### The three tiers

| Condition | 4-bit accuracy |
| --- | ---: |
| Canonical order (`truncate_1`) | **61.5%** |
| Final rule after its premise, rest scrambled | ~27% |
| Final rule before its premise | ~6% |

So two requirements, not one: the final rule must **follow** the premise it fires
on, **and** the chain leading up to it must be in order. Adjacency is not among
them.

## Consequence for the manuscript

§6.1's "present and adjacent" was wrong and is corrected to "the rule follows the
premise it fires on". §5.2's order claim now points at §5.3. §6.3's
single-permutation limitation is discharged and replaced by a narrower one: eight
is a sample of 8! orderings, and the gap-versus-direction split is read off
permutations that happened to land in each cell rather than a design that fixed
them.

## Artifacts

| | |
| --- | --- |
| Runner | `scripts/prepare_and_run_shuffled_permutations_b18.py` |
| Analysis | `scripts/analyse_shuffled_permutations_b18.py` |
| Results | `results/b18_permutations_v1.json` |
| Panel | `data/cognitive_core/shuffled_permutations_b18/` (incl. `public/geometry.jsonl`) |
| Receipts | `runs/cognitive_core/shuffled_permutations_b18/<key>/` |

## Out of scope

- Whether a design that *fixes* gap and direction (rather than sampling them)
  would separate them more cleanly. It would; we sampled.
- Whether the effect holds beyond depth-4 chains of 8 lines.
