# Solver-Assisted Logical Prediction

Code-only companion to the preprint *"Auditing Solver-Assisted Logical
Prediction with a Sealed Five-Arm Certificate Factorial"* (draft dated
1 Sep 2026). Imported here on 2 Sep 2026 from
`solver_assisted_logical_prediction_paper_code_v1.zip`.

See [`../CLAUDE.md`](../CLAUDE.md) for the multi-project root convention.

## Research question

External solvers can hand a language model evidence that settles a query. Big
accuracy gains in that setting do **not** show the model used an intermediate
*proof state* or repaired its own reasoning — it may simply be reading off a
supplied conclusion.

The falsifiable question:

> When a solver certificate helps, does a **proof prefix** whose terminal
> literal is withheld improve prediction beyond **conclusion-only** evidence and
> a matched **irrelevant-proof** control?

Answered by a five-arm matched factorial (`none`, `irrelevant`,
`conclusion_only`, `proof_prefix`, `full`), scored by direct next-token
likelihood over verified single-token candidates — no free-text generation.

## Where it stands

**Complete and sealed.** The preprint is drafted; the primary contrast is
answered in the negative. Outstanding work is release/publication hygiene, not
experimentation. See "Open items" below.

Headline numbers (frozen Qwen2.5-3B-Instruct-4bit, MLX):

| Study | Result |
| --- | --- |
| v7 ProofWriter pilot, 192-item prospective | relevant cert 187/192 (97.4%) vs. irrelevant 91/192 (47.4%); paired RD +0.500, exact McNemar *p* = 6.25e-28 |
| b14 five-arm binary factorial, 192 items | none 91 · irrelevant 96 · conclusion-only 176 · proof-prefix 167 · full 191 (of 192) |
| **b14 primary contrast** (prefix − conclusion-only) | **RD −0.047, exact McNemar *p* = 0.078 → not supported** (6 prefix-only vs. 15 conclusion-only) |
| b14 secondary: prefix − irrelevant | +0.370, *p* = 1.51e-19 (Holm-adj. 3.02e-19) |
| b14 secondary: full − conclusion-only | +0.078, *p* = 6.10e-05 |

**Interpretation boundary (do not soften this):** the supported claim is a
*system-level* effect of query-relevant solver material in a narrow binary task
envelope. The paper explicitly does **not** claim internal reasoning repair, and
the primary contrast points the other way (conclusion-only numerically better
than prefix).

### Completed post hoc reanalysis (2026-09-03): b14 read as a 2x2

B14's five arms form a 2x2 of *answer evidence* x *proof state*, with `none`
and `irrelevant` as two flavours of the empty cell. The paper's prespecified
primary contrast (`proof_prefix` - `conclusion_only`) is the **diagonal** of
that square: it removes answer evidence and adds proof state simultaneously, so
its null is not attributable to either factor. The four one-factor **edges** are
the interpretable contrasts, and the paper reports only two of them.

| | -state | +state |
| --- | ---: | ---: |
| **-answer** | irrelevant 96 | proof_prefix 167 |
| **+answer** | conclusion_only 176 | full 191 |

Reading the edges instead of the diagonal, from the same sealed receipts:

- **State main effect +22.4pp** (edges: +37.0pp with no answer present, *p* = 1.5e-19; +7.8pp with answer present, *p* = 6.1e-5). Never reported in the manuscript.
- **Substitution:** the answer literal is worth +80 items without state but only +24 with it — it loses **70% of its value** once state is supplied.
- **Unreported contrast** `proof_prefix` - `full` = **-12.5pp, *p* ~ 1e-7**; derivable from the marginals to within one item. A model reliably executing the withheld step should show ~0 here.
- Swing from diagonal to state main effect: **-4.7pp -> +22.4pp**, a 27.1pp sign flip on identical data.

This is a **reanalysis, not a new result**, and must be labelled post hoc. It
does not distinguish inference from lexical overlap — that is what b15 tests.

**Executed 2026-09-03** by
`scripts/reanalyse_cognitive_binary_certificate_factorial_b14_posthoc_v1.py`
against `results/b14_raw_model_calls_960.jsonl` (960 receipts, all digests
verified, file SHA-256 matches its manifest). The answer authority is *not* in
that export but is recoverable from the class token in each `task_id`
(`bcf14-prospective-{entailed,contradicted}-*`), with `entailed`→`Yes`,
`contradicted`→`No`. The script hard-asserts that the reconstruction reproduces
all five published per-arm counts before reporting; it does. Output:
`results/b14_posthoc_2x2_reanalysis_v1.json` (all 10 pairwise contrasts, paired
tables, exact McNemar, seeded BCa, Holm over the edge family, class strata,
signal detection, margin descriptives).

### The response-bias finding (2026-09-03) — most consequential result so far

Splitting the receipts by class overturns the manuscript's baseline claim. The
model answers `No` to **88%** of prospective items.

| Arm | hits (entailed) | false alarms (contradicted) | d' | criterion c |
| --- | ---: | ---: | ---: | ---: |
| `none` | 9/96 | 14/96 | **−0.26** | +1.17 |
| `irrelevant` | 9/96 | 9/96 | **0.00** | +1.29 |
| `conclusion_only` | 80/96 | 0/96 | +3.52 | +0.81 |
| `proof_prefix` | 71/96 | 0/96 | +3.20 | +0.97 |
| `full` | 95/96 | 0/96 | +4.72 | +0.20 |

- **"47.4% = chance" is wrong.** It is zero discriminative sensitivity plus a
  heavy `No` bias. A trivial always-`No` strategy scores 96/192; `none` scored
  91 and `irrelevant` 96 — **at or below** it. `irrelevant` gives an identical
  9/96 `Yes` rate in both classes, i.e. *exactly* zero sensitivity.
- **Same label-collapse mode as the terminal v8/v9 screens.** v9 was 0/12 on
  unknown, always `No`; b14 is 88% `No` on the real panel. This is a recurring
  property of the model, not three unrelated incidents.
- **b14's delivery gate did not test the task.** It passed 36/36 on *direct
  facts* while the model is degenerate on multi-step items. The gate validated
  the output channel only.
- **Half the panel carries no information.** With certificates the contradicted
  class is 96/96 in every arm — the `No` bias is free correctness there. All 21
  discordant pairs in the primary contrast are in the entailed class; the
  contradicted class contributes **zero**. Effective n was 96, not 192.
- **Accuracy is the wrong dependent measure** on a balanced panel with a biased
  responder. Report d' and criterion separately. This correction is written into
  the b15 design doc, whose primary contrast is now the entailed subset with a
  required same-sign d' drop.

**Publication decision (2026-09-02): hold b14 and publish with b15 as one
paper.** Reanalysis alone reframes a null as a positive but leaves the
mechanism question open, which caps the venue; b15 answers it.

### b16 results (2026-09-03) — three-class survey, 10 models

10/10 models, 9,600 receipts, 0 digest failures. `results/b16_analysis_v1.json`.

**The prespecified threshold was invalid.** ">=80% undetermined recall = relays"
passed 8/10 — but it is single-class recall, and four models answer `Unknown` to
54–97% of everything, averaged over arms, and never emit `No` at all. b14's `No`-bias trap, mirrored.
Replaced **post hoc** by **min per-class recall >= 0.50**, which collapse cannot game.

| Finding | |
| --- | --- |
| **Architecture works, above a floor** | Balanced accuracy `none`→`full`: qwen2p5_3b 41.1→**90.6**, phi4_mini 44.8→**90.6**, gemma3_4b 63.5→**96.4**. Chance = 33.3% |
| **Viable substrates: 3 of 10 under `full`** | qwen2p5_3b, phi4_mini, gemma3_4b. Superseded: the paper reports viability per arm, as a property of (model x arm x runtime); four models are viable in *some* arm |
| **v9 does not generalise** | v9's 0/12 on unknown was model-specific, not architecture-level. gemma3_4b reaches 89.1%, phi4_mini 100% |
| **A floor near 3B for *tolerating full certificates*** | Not a floor for serving as an interface: Llama-3.1-8B is degenerate in all five arms. Nothing below 3B clears the floor in any arm |
| **Not monotonic in scale** | qwen2p5_7b collapses (62% `Unknown`, min recall 14.1%) while qwen2p5_3b is viable |

### b15 results (2026-09-03) — validity vs surface overlap: **RESOLVED**

1,920 receipts, 0 digest failures. `results/b15_analysis_v1.json`.

**Primary** `truncate_1` − `broken_chain` (entailed, n=96): **+60.4pp,
p = 6.9e-18**, BCa [+49.0, +68.8], d' drop +2.446 (same-sign requirement met).

| Component | |
| --- | ---: |
| total state effect | +61.5pp |
| surface component | **+1.0pp** (p = 1) |
| **validity component** | **+60.4pp** |
| **validity share** | **98.3%** |
| Finding | |
| --- | --- |
| **b14's state effect is inference, not word matching** | 98.3% survives holding surface form fixed and breaking only the logic |
| **Entity repetition explains nothing** | `same_entity_irrelevant` 0/96, identical to `irrelevant` at 0/96 despite 4x vs 0x entity mentions |
| **Depth is exactly one step** | `truncate_2` = 0/96, identical to `none`. A cliff, not a slope |
| **No resistance to corrupted solver output** | `misleading` 3/192, d' = **−4.363**. The model follows a wrong-pointing certificate 189/192 times |

Five arms (`none`, `irrelevant`, `same_entity_irrelevant`, `truncate_3`,
`truncate_2`) are **identical**: 96/192, 0/96, d' = 0.000, c = 2.565 — an
all-`No` responder. Behaviour is binary: the chain reaches one step from the
answer, or the model is blind.

## Experiment lineage

Read in this order to understand the history — each version is frozen, and each
successor exists for a stated reason.

| Version | What it was | Outcome |
| --- | --- | --- |
| v4/v6 | Label-free `F/R/I` pointer-string reference state | Null (61/96 vs 60/96 vs 62/96) — an *opaque-reference* delivery failure |
| **v7** | Sealed ProofWriter pilot: relevant vs. matched-irrelevant vs. no certificate; 32-item base, 96 positive control, 192 prospective (depth-4) | **Passed, large effect.** Cannot separate answer provision from state use |
| v8 | First 3-class (entailed/contradicted/unknown) five-arm factorial design | **Terminal.** Qwen2.5-3B failed arbitrary-label qualification (25/36 ordinary, 13/36 counterbalanced); Qwen3-1.7B died on an MLX bfloat16→NumPy buffer conversion before scoring. Factorial never opened |
| v9 | Semantic `Yes`/`No`/`Unknown` qualification (replaces arbitrary labels) | **Terminal.** Interface perfectly stable (36/36 across templates) but 24/36 correct: 12/12 entailed, 12/12 contradicted, **0/12 unknown** — systematic open-world collapse |
| v10 | Fresh Qwen3-1.7B successor to v8; only change is explicit MLX float32 cast | **Terminal.** Scoring path worked; model picked label `A` for all 36 items under both mappings (0/36 semantic agreement). Prospective panel never opened |
| b11 | Pivot to **binary** derivable-query task, direct `Yes`/`No`, five arms | Qualified, then prospective run **externally interrupted** at 24 items before any receipt persisted |
| b12 | Same design; execution split into 8× 24-item shards with exclusive start/complete/completion records | Interrupted again |
| b13 | Same design; one-forward-batch execution transport | Interrupted again |
| **b14** | Same design; **single persistent local supervisor process** with stdout/stderr saved under the run dir | **Completed.** Qualification 36/36 direct + 33/36 reordered, 33/36 agreement → authorized one 192-item prospective run. All five receipt files written before the answer authority was opened |
| **b15** | **Complete and sealed.** Ran on three checkpoints (4-bit, bf16, Gemma-3-4B), 5,976 responses. Mechanism decomposition, **ten arms**: `none`, `irrelevant`, `same_entity_irrelevant`, `truncate_3/2/1`, `broken_chain`, `misleading`, `shuffled`, `full`. 192 items (96/96), depth 4. Design doc: [`binary_certificate_factorial_b15.md`](docs/cognitive-core/binary_certificate_factorial_b15.md) | Splits b14's +37pp state effect into **surface-overlap** and **validity-tracking** components. Both open decisions were settled in the design doc's log on 2026-09-03 |
| **b16** | **Complete and sealed.** 10 models, 9,600 responses. Merged multi-model three-class survey: 192 items (64 entailed / 64 contradicted / 64 undetermined) x 5 arms x 10 models. Design doc: [`multimodel_three_class_survey_b16.md`](docs/cognitive-core/multimodel_three_class_survey_b16.md) | Answers substrate viability **and** faithful non-determination in one panel; class stratification separates them |
| **b17 / b17b** | Three-class rescoring of b15's `broken_chain` items with an `Unknown` candidate, plus a `none` abstention baseline. 1,728 + 576 responses | Experiment 4. Abstention direction is **reference-dependent**: it falls against `none`/`irrelevant`, rises against the surface-matched `truncate_1` |
| **b18** | b15's items re-scored under eight line permutations each, 9 arms, 5,184 responses | Robustness study. Direction, not adjacency: reversing a rule and its premise costs accuracy on every checkpoint |
| **b19** | b16's panel re-scored through `transformers` on CUDA, plus Llama-3.1-8B and Qwen2.5-14B, 11 models, 10,560 responses | Robustness study. The inference runtime is a factor: phi-4-mini's verdict flips between stacks on identical weights |
| **b20** | b15's panel re-scored at scale on Modal H100s: Qwen3-32B and Llama-3.3-70B, 10 arms each, 3,840 responses. Design doc: [`binary_certificate_factorial_b20.md`](docs/cognitive-core/binary_certificate_factorial_b20.md) | Scale check. The corruption failure does not attenuate: Llama-3.3-70B answers `full` 192/192 and solves 145/192 unaided, and is wrong on **all 192** misleading items at d' = −5.12. Qwen3-32B recorded but not interpreted: a stratified diagnostic shows the scored bare `Yes`/`No` pair disagrees with the model's own preferred verdict on 5 of 12 items under `full`, so its collapse there is substantially a tokenisation artefact |

b11→b14 differ **only in execution transport**. The task, arms, sample size,
primary contrast, and analysis plan are identical; each successor uses a newly
seeded sealed panel. This shows up in the code as thin subclass-style modules
that import the predecessor and override `VERSION`/`DATA`/`RUN`/seeds — e.g.
`prepare_...b14.py` imports `...b13` which imports `...b12` which imports the
b11 root, rewriting `bcf13-*` task ids to `bcf14-*`.

## Layout

```
manuscript/grounded_state_repair_preprint_v1/
  manuscript.md            # the preprint (authoritative results text)
  references.bib
  build_preprint_pdf.py    # reportlab PDF builder
src/scientist/domains/cognitive_core/
  proofwriter_verified_trace_v4.py   # pure-Python ProofWriter parsing + restricted
                                     # forward chainer + canonical proof traces; no model
scripts/
  prepare_* / run_* / score_* / qualify_*   # per-version generators, runners, gates
  audit_*                                   # no-model verifiers
  package_*                                 # release bundle builders (v1..v6, paper-code v1)
docs/cognitive-core/
  *design*.md, binary_certificate_factorial_b1*.md   # per-version design docs / protocols
MANIFEST.json              # SHA-256 of all 37 archived files; manifest_id c3fe580a...
requirements-publication-code.txt
archive/                   # provenance: original import zip + built preprint PDF
                           #   solver_assisted_logical_prediction_paper_code_v1.zip  (ede49f72...)
                           #   solver_assisted_logical_prediction_audit_preprint.pdf (75eee6a5...)
```

Naming is consistent and load-bearing: `prepare_*` seals data, `run_*` executes
scoring, `score_*` scores a v7 panel, `qualify_*` runs a delivery gate,
`audit_*` re-verifies without a model, `package_*` builds a release zip.

## Running things

The only thing runnable end-to-end without model weights and without the
artifacts package:

```bash
PYTHONPATH=src:scripts python3 scripts/audit_cognitive_binary_certificate_factorial_b14.py --project .
```

It re-derives everything from receipts using only the standard library: panel
SHA-256s and row counts, per-receipt canonical digests (`receipt_id` = SHA-256
of the receipt body minus that field), receipt/authority coverage, per-arm
counts, the three paired 2×2 tables, paired risk differences, and exact
two-sided McNemar *p* values — then asserts each against
`runs/.../results/prospective-factorial.json`.

**It currently fails with `FileNotFoundError` on
`data/cognitive_core/binary_certificate_factorial_b14/public/seal.json`** — this
is expected. This archive is *code only*.

PDF: `python3 manuscript/grounded_state_repair_preprint_v1/build_preprint_pdf.py`
(needs `reportlab`).

## Missing dependencies (important)

This bundle deliberately excludes model weights, prompts, certificates, answer
authorities, likelihood receipts, and all derived results. Those live in a
separately prepared archive **`solver_assisted_reasoning_release_v6.zip`**
(built by `scripts/package_cognitive_solver_assisted_public_release_v6.py`).
**Unpack both at the same project root** for the audit to work. That archive is
not present in this directory — it needs to be located and imported.

Original scoring environment: Python 3.12.13, NumPy 2.5.1, MLX 0.32.0,
mlx-lm 0.31.3. Local Python here is 3.12.12.

Model paths are **hardcoded to another machine's home directory**
(`/Users/krishnachaitanya/.cache/huggingface/...`) in
`scripts/qualify_cognitive_semantic_three_way_interface_v9.py:24` and
`scripts/run_cognitive_solver_assisted_certificate_factorial_v8.py:36,43`.
Any re-run on this machine needs those repointed — but note that repointing a
frozen runner is a code change to a sealed script; prefer a new versioned
successor over editing in place.

## Plan and open items

Sequenced 2026-09-02. Decisions taken: **hold b14, publish with b15**; start on
the b15 design doc; program-level goal statement to be written by the author.

**Blocker — only the author can clear this.**

0. ~~Locate **`solver_assisted_reasoning_release_v6.zip`**~~ **CLEARED** — the
   panels, authorities and receipts are now in-repo under `data/`, `runs/` and
   `results/`, and every Track A item completed without the zip. Original text:
   locate the archive (panels, prompts,
   certificates, answer authorities, 960 likelihood receipts). Not present in
   `~/Downloads` or `~/Desktop` as of 2026-09-02. Every Track A item is blocked
   on it and the b14 audit cannot run without it.

**Track A — reanalysis, no model runs.** Unblocks once the artifacts land.

1. Run the b14 audit; confirm it passes.
2. Reanalyse b14 as the 2x2: all four edges, state main effect, substitution.
   Label post hoc.
3. Add the unreported `proof_prefix` - `full` contrast.
4. Stratify the 25 `proof_prefix` failures by proof depth.
5. Manuscript reframe: state main effect as the headline; the diagonal demoted
   to a footnote carrying the ceiling arithmetic (8.3pp headroom vs a 15pp
   prespecified target).
6. Add missing citations, most urgently Lanham et al. on CoT faithfulness
   (truncation and mistake-injection are the manipulations b15 adopts), plus
   Logic-LM, LINC, SatLM, PrOntoQA, RuleTaker.

**b16 model eligibility screen — COMPLETE (2026-09-03).**
`scripts/screen_cognitive_binary_multimodel_b16.py`, records under
`runs/cognitive_core/binary_multimodel_b16/<key>/control/screen.json`.
**10/10 candidates eligible**: every model loads under mlx-lm, completes a real
prefill, and tokenises `Yes`/`No`/`Unknown` as single distinct tokens. No
`first_token_fallback` needed anywhere, and **three-way scoring is clean on all
ten**, so the non-determination experiment is measurable as designed. Weight
hashes and pinned commit shas recorded before deletion; 43 GB of weights cycled
through a cache that never held more than one model, and disk fully recovered.
Model list and pins: `models.toml`.

**b16 panel sealed; sweep complete (2026-09-03).**
`prepare_cognitive_multimodel_three_class_b16.py` ->
`data/cognitive_core/multimodel_three_class_b16/` (seal_id `0887ed11...`).
192 items, 64/64/64, depth 4, per-item nonce vocabulary, **every item certified by
`cc_instruments.closure`** (saturated, consistent, verdict == intended class for
all 192). Task ids are opaque: unlike b14, whose ids read
`bcf14-prospective-entailed-...` and leaked the key, the class lives only in the
authority file, which must therefore be preserved in the release package.
`run_cognitive_multimodel_three_class_b16.py` streams one model at a time,
manifests weights before deleting, is resumable by completion marker, verifies the
panel hash against the seal, and never reads the authority. Measured 0.140 s per
prompt on the 0.5B; full sweep ~2 h.

**Track B — b15, the mechanism experiment.** Panel sealed 2026-09-03
(`prepare_cognitive_binary_certificate_factorial_b15.py`, seal_id `e2bcbc4a...`),
**ten arms** after three design corrections: the depth ladder (b14 had no dynamic
range), `same_entity_irrelevant` (b14 confounded relevance with entity
repetition), and `full` (added before data collection as a ceiling and
comparability anchor). Source audit and runner not yet built. **Two open
decisions block the runner** -- whether to restore `conclusion_only` for a free
replication of b14's 2x2, and whether to run 4-bit (matching b14's anchors, as the
design doc specifies) or bf16 (matching `models.toml` and b16). These conflict and
must be settled before scoring.

7. Implement `prepare_`/`run_`/`audit_cognitive_binary_certificate_factorial_b15.py`
   following the b14 lineage pattern. ~1,536 forward passes across seven arms.
   The `broken_chain` source audit is the substantive new code.

**Track C — b16.** Complete; it is Experiment 3 of the paper. The 65-75% unaided
screen below was never adopted: the substrate criterion is minimum per-class
recall >= 0.50.

8. Screen candidate models for **65-75% unaided baseline** on the binary task.
   Only then is the scaffolding/"repair" hypothesis testable at all. Shape
   depends on b15's outcome.

**Track D — program and release hygiene.**

9. Write the Cognitive Core goal statement into the root `CLAUDE.md`. Author to
   draft; not recorded anywhere in the repo as of 2026-09-02.
10. Consider elevating the v9 abstention failure (0/12 on unknown, always `No`)
    out of a diagnostics footnote — it is a capability gap with direct
    architectural consequences for any reasoning core.
11. Choose and add an explicit licence — the bundle asserts none.
12. Review ProofWriter source and derivative-data licence terms before any
    redistribution.
13. Deposit the release archive in a versioned/archival service with a permanent
    DOI (pending; the paper says so).
14. Author block is still "Anonymous author(s)"; `:::study-flow` at
    `manuscript.md:28` is an unrendered figure placeholder.

## Constraints when working in this project

- **Sealed means sealed.** v7, v8, v9, v10, b11, b12, b13, b14 are terminal. Do
  not re-run, re-score, edit, or pool them. A new question gets a new version id
  and a new design doc in `docs/cognitive-core/`.
- No retries, prompt sweeps, panel substitutions, or automatic successors were
  authorized in any protocol — don't introduce them.
- A failed qualification gate is a delivery/competence result, not a treatment
  null. Never report v8/v9/v10 as evidence that proof prefixes don't work.
- Analysis reporting standard: full paired 2×2 table + exact two-sided McNemar
  (the decision criterion) + seeded 100,000-resample paired BCa interval, with
  Holm adjustment across secondary contrasts within a model.
- The v7 custom Wilson sensitivity envelope is retained in the immutable
  terminal record but is **not** the publication-facing uncertainty estimate.
- v7 has **no** prospective power calculation and must not be presented as a
  power-justified confirmatory design; b14 does (80% normal-approximation power
  for a 15pp paired difference at expected discordance 0.35, *n* ≈ 123).
- Both the pilot and b14 exclude the open-world **unknown** class. That is a
  known, material competence boundary (see v9), not an oversight to paper over.
