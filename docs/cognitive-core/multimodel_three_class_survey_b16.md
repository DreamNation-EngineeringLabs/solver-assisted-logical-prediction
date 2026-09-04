# b16: multi-model three-class survey

**Two questions, one panel.**

| # | Question | Answered by |
| --- | --- | --- |
| 1 | Which models can serve as the interface at all? | entailed/contradicted behaviour |
| 2 | Can a model faithfully relay "cannot determine"? | the undetermined class |

**Why merged.** Class stratification separates them in analysis. Keeping them
apart cost a second panel, a second runner, ~2h compute, ~3 days build.

**Status.** Panel sealed, sweep running 2026-09-03.

---

## Why question 2 matters

A solver returns three verdicts. v9 found the frozen 3B relayed two perfectly
(12/12, 12/12) and the third **0/12** -- silently turning "cannot determine" into
a confident `No`. If that generalises, the architecture has a hole that accuracy
on clean inputs never reveals.

---

## Decision log

| # | Decision | Reason |
| --- | --- | --- |
| 1 | **No gate blocks the run.** All 10 models score the full panel | Under the substitute framing, delivery **is** the capability under test. b14's gate passed 36/36 on direct facts while the model was degenerate on the real panel |
| 2 | Tooling failure != behavioural failure | Won't load / bad tokeniser -> excluded, not a finding. Loads but collapses to one label -> **reported as a result** |
| 3 | Balanced accuracy as headline, not accuracy | Always-one-label baseline = 33.3%. A biased responder scores well on accuracy while discriminating nothing |
| 4 | Opaque task ids | b14's ids read `bcf14-prospective-entailed-...`, so its "sealed" authority was reconstructible from the public panel |
| 5 | Depth fixed and recorded per item | b14 recorded no depth and could not stratify its failures |
| 6 | 192 items (64/64/64), not 288 | 0.91 power at 20pp. The expected effect is huge (v9 floor was 0/12); 288 cost 2h for little gain |
| 7 | bf16 across all 10 models | Mixing precisions would confound quantisation with model identity |

---

## Prerequisites, both cleared

**Eligibility screen (stage 1).** 10/10 models load, prefill, and tokenise
`Yes`/`No`/`Unknown` as single distinct tokens. No fallback needed; three-class
scoring available on the full set. Records:
`runs/cognitive_core/binary_multimodel_b16/<key>/control/screen.json`.

**Closure certification.** `cc_instruments.closure` validated against ProofWriter
OWA test splits (depths 0,1,2,3,5): **23,240/23,240 = 100.00%**, zero unusable
theories, diagonal confusion, **10,440 undetermined**. Report:
`results/closure_validation_v1.json`.

No item enters the panel without a `certify()` record.

---

## Sealed panel

`data/cognitive_core/multimodel_three_class_b16/` | seal_id `0887ed11...`

192 items | 64 entailed + 64 contradicted + 64 undetermined | depth 4 |
per-item nonce vocabulary | all 192 certified saturated, consistent, and matching
their intended class.

Undetermined items are made by withholding a chain-closing rule, then certifying
that neither the query nor its negation is in the closure. They are formally
underdetermined, not merely hard.

---

## Five arms

| Arm | entailed / contradicted | undetermined |
| --- | --- | --- |
| `none` | nothing | nothing |
| `irrelevant` | valid donor-entity chain | valid donor-entity chain |
| `conclusion_only` | the derived terminal literal | "neither the query nor its negation is derivable" |
| `proof_prefix` | chain, terminal literal omitted | closure coverage, saturation status omitted |
| `full` | prefix + terminal literal | closure coverage + saturation status |

The undetermined arms follow the v8 closure-coverage design, constructible only
now that saturation is certifiable.

No rendering contains `Yes`, `No`, `Unknown`, *entailed*, *contradicted*.

### Worked examples (real sealed items)

**Entailed.** Query `Paftglael is mimdres.` Answer **Yes**.

| Arm | Solver record |
| --- | --- |
| `irrelevant` | `Trongloth is zeithfek. All zeithfek people are rudru. ...` (donor entity) |
| `conclusion_only` | `Paftglael is mimdres.` |
| `proof_prefix` | `Paftglael is kraethdrei. ... Paftglael is krokzlir. All krokzlir people are mimdres.` (literal withheld) |
| `full` | prefix + `Paftglael is mimdres.` |

**Undetermined.** Query `Vokzousk is truftge.` Answer **Unknown**. Rule 3 withheld
from the theory, so the chain stops at `votaek` and never reaches `truftge`.

| Arm | Solver record |
| --- | --- |
| `irrelevant` | `Deismosk is plurvrisk. ...` (donor entity) |
| `conclusion_only` | `neither the query nor its negation is derivable from the stated rules.` |
| `proof_prefix` | `Vokzousk is pounbreth. All pounbreth people are pomrou. ... Vokzousk is votaek.` -- the closure coverage: everything the solver **did** derive, stopping where the chain breaks |
| `full` | closure coverage + the saturation status |

Note `truftge` -- the query predicate -- appears nowhere in the undetermined
prefix. It cannot: the solver has nothing about it. This is the property recorded
above, and it is why undetermined items offer fewer surface cues than the other
two classes.

**Known property, recorded before results.** An undetermined `proof_prefix`
cannot contain the query predicate -- the solver has nothing about it. Entailed
and contradicted prefixes do. So undetermined items offer fewer surface cues, and
a surface-matching model will look worse there for reasons unrelated to
abstention. `entity_mentions` is recorded per arm so this is analysable.

---

## Measures

Per model and arm: 3x3 confusion matrix, per-class recall, response distribution,
**balanced accuracy** (headline; 33.3% = chance), and pairwise d'/criterion on the
binary subset for comparability with b14.

---

## Analysis

**Primary, per model.** Paired `full` - `none` on the 64 undetermined items.
Complete 2x2 table, exact two-sided McNemar (decision criterion), seeded
100,000-resample BCa.

**Faithful-transmission threshold, declared in advance:**

| Undetermined accuracy in `full` | Verdict |
| --- | --- |
| >= 80% | relays non-determination |
| 20-80% | partial relay |
| < 20% | **architecture-breaking for that model** |

**Secondary, Holm-adjusted:** `full` - `conclusion_only` on undetermined; `full` -
`none` on entailed and contradicted separately (replicates b14 across models).

**Power.** n=64: 0.91 at 20pp, 0.74 at 15pp. Declared target **20pp**; below is
indeterminate, not null.

Model is not a randomised factor. Between-model comparisons are **descriptive**,
reported as a size curve, never as a significance claim about scale.

---

## Execution

One persistent supervisor. Models streamed strictly one at a time: download
pinned revision -> **record weight manifest before deleting** -> score 5 arms ->
receipts -> completion marker -> delete. Peak disk = one model.

Resumable by completion marker. b11, b12, b13 were each lost to interruption.

All 50 receipt files must exist before the authority opens. No retries, sweeps,
substitutions, or automatic successors.

9,600 prompts, ~2h measured.

---

## Interpretation

| Outcome | Means |
| --- | --- |
| Relayed across models | The abstention path works. v9 was model-specific; this becomes a model-selection criterion |
| Fails across all models | **Architecture-level constraint.** A substitute that silently converts "cannot determine" into an answer is unsafe regardless of accuracy on decidable inputs. Redirects the programme to abstention before formalisation |
| Mixed | The threshold partitions the 10 models into viable and non-viable substrates -- directly actionable for every later project |

System-level effects are not upgraded to mechanism claims. High accuracy with
`full` material describes a faithful transcriber, not a reasoner.

---

## Results (2026-09-03)

10/10 models, 50/50 receipt files, 9,600 receipts, **0 digest failures**, coverage
exact. Authority opened only after verification. Sweep ~1h50m.
`results/b16_analysis_v1.json`.

### The prespecified threshold was invalid

Declared in advance: >=80% undetermined recall in `full` = relays. **8/10 passed.**
It is a single-class recall measure, and a model answering `Unknown` to
everything maxes it while discriminating nothing. Four models do exactly that --
62-96% `Unknown`, three never emitting `No` at all.

This is b14's `No`-bias trap mirrored. The criterion below replaces it and is
**post hoc**, on the same footing as the b14 reanalysis.

**Corrected criterion:** a model is a viable substrate only if it clears
**min per-class recall >= 0.50** in `full`. That cannot be gamed by collapsing
onto one label.

### Per model, `full` arm

| Model | B | bal. acc | min recall | max response share | prespecified | corrected |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| qwen2p5_0p5b | 0.5 | 63.5 | 0.0 | 61.5 | relays | **collapsed** |
| olmo2_1b | 1.0 | 42.2 | 0.0 | 91.1 | relays | **collapsed** |
| llama3p2_1b | 1.2 | 37.0 | 0.0 | 95.3 | relays | **collapsed** |
| qwen2p5_1p5b | 1.5 | 37.0 | 0.0 | 96.4 | relays | **collapsed** |
| smollm2_1p7b | 1.7 | 69.3 | 37.5 | 44.8 | partial | below floor |
| **qwen2p5_3b** | 3.0 | 90.6 | 71.9 | 42.7 | partial | **viable, partial relay** |
| llama3p2_3b | 3.2 | 80.7 | 42.2 | 49.5 | relays | below floor |
| **phi4_mini** | 3.8 | 90.6 | 71.9 | 42.7 | relays | **viable, relays** |
| **gemma3_4b** | 4.3 | **96.4** | 89.1 | 36.5 | relays | **viable, relays** |
| qwen2p5_7b | 7.6 | 71.4 | 14.1 | 62.0 | relays | **collapsed** |

Chance balanced accuracy = 33.3%. **Viable substrates: 3 of 10.**

### Does the architecture work?

Balanced accuracy, `none` -> `full`:

| Model | B | none | full | gain |
| --- | ---: | ---: | ---: | ---: |
| qwen2p5_0p5b | 0.5 | 35.4 | 63.5 | +28.1 |
| olmo2_1b | 1.0 | 35.9 | 42.2 | +6.3 |
| llama3p2_1b | 1.2 | 33.9 | 37.0 | +3.1 |
| qwen2p5_1p5b | 1.5 | 33.3 | 37.0 | +3.7 |
| smollm2_1p7b | 1.7 | 33.3 | 69.3 | +36.0 |
| qwen2p5_3b | 3.0 | 41.1 | 90.6 | **+49.5** |
| llama3p2_3b | 3.2 | 45.8 | 80.7 | +34.9 |
| phi4_mini | 3.8 | 44.8 | 90.6 | **+45.8** |
| gemma3_4b | 4.3 | 63.5 | 96.4 | +32.9 |
| qwen2p5_7b | 7.6 | 33.3 | 71.4 | +38.1 |

**Yes, above a size floor.** Models at or near chance unaided reach 80-96% with
full solver material, on a three-class task including abstention.

### Three findings

| # | Finding |
| --- | --- |
| 1 | **v9 does not generalise.** v9 found 0/12 on unknown and framed it as possibly architecture-level. It is not: gemma3_4b reaches 89.1% and phi4_mini 100% undetermined recall. Non-determination is relayable |
| 2 | **There is a minimum viable interface size, ~3B.** Below 1.7B the model collapses to one label regardless of what the solver supplies. The apparatus cannot help an interface that cannot express three outcomes |
| 3 | **Not monotonic in scale.** qwen2p5_7b collapses (62% `Unknown`, min recall 14.1%) while qwen2p5_3b is viable. Bigger is not safer |

Finding 2 bounds the programme's "works at few parameters" bet: viable, but not
arbitrarily few.

---

## Out of scope

Does not test whether the model reasons (externalised by assumption).
Does not test formalisation -- every theory is supplied pre-formalised.
Does not resolve validity vs surface matching -- that is b15.
