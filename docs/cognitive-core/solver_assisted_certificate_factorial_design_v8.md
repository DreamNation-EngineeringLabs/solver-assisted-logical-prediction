# Solver-assisted certificate factorial: confirmatory design v8

## Status and purpose

This is a fresh experiment. It does not reopen, modify, pool with, or retry the
sealed ProofWriter v7 study. V7 is retained as a limited pilot showing that a
query-relevant solver certificate can improve Qwen2.5-3B forced-choice output.
Its result cannot distinguish external answer provision from model-side use of
intermediate proof state.

The v8 question is narrower and falsifiable:

> When a solver certificate is useful, does a proof prefix whose final
> conclusion is withheld improve prediction beyond conclusion-only evidence and
> a matched irrelevant-proof control?

## Task families and contamination boundary

The primary family is a deterministic, procedurally generated open-world rule
reasoning task. Each item is created after model release from a fixed public
seed and uses a per-item nonce vocabulary. The generator supports three
outcomes: entailed, contradicted, and unknown. It is not proof of complete
pretraining independence; rather, it eliminates reuse of public ProofWriter
items and makes exact-item novelty, generation, and solver closure auditable.

The sealed v7 ProofWriter result is reported separately as a public-benchmark
pilot and is never presented as a pretraining-independent result.

## Models and delivery qualification

Only frozen local models in the permitted 1.7B and 3B classes may be used:

- Qwen2.5-3B-Instruct-4bit;
- Qwen3-1.7B only if it passes this new three-way semantic delivery screen.

Before any factorial result is opened, each model must score at least 75% on a
fresh 36-item direct-fact screen, have no class below 2/3 correct, and agree on
at least 32 of 36 items under two semantically equivalent scoring templates.
Candidate token ids, templates, model/config/weight hashes, package versions,
and per-item logits are recorded. A failed qualification is a delivery result,
not a treatment null, and that model is excluded from confirmatory aggregation.

## Five matched arms

Every item appears in all five arms. The system prompt, visible theory, query,
candidate response tokens, output length, and decoding are identical.

| Arm | Solver material | Mechanistic role |
| --- | --- | --- |
| `none` | none | direct-prediction baseline |
| `irrelevant` | a valid same-shape proof for a different conclusion | proof length, format, and validity control |
| `conclusion_only` | only the solver-derived conclusion/status for the query | external answer-evidence control |
| `proof_prefix` | certified facts, rules, and intermediates; final derived conclusion/status omitted | test of whether usable supplied state supports the final inference |
| `full` | prefix plus final conclusion/status | solver-assisted upper comparison |

For an entailed or contradicted item, `conclusion_only` states the derived
literal but never the response label. `proof_prefix` contains every preceding
certificate line but omits the final literal. For unknown, it uses a closure
coverage certificate: the prefix lists all solver-derived literals relevant to
the target entity/property but omits the final saturation status; the full and
conclusion-only arms include the solver status that neither query polarity is
derivable. The irrelevant control has the same certificate type and line count
but concerns another query in the same generated theory.

All certificate renderings exclude the response tokens and the class words
`entailed`, `contradicted`, and `unknown`.

## Panels, analysis, and power

The development panel has 72 items (24 per class) and is used only to test the
delivery and construction gates. The confirmatory prospective panel has 192
items (64 per class), generated from disjoint nonce/theory seeds. It is opened
once only after all gates pass. There are no prompt sweeps, retries, or automatic
successor runs.

The single primary contrast is `proof_prefix - conclusion_only` on correctness.
The main falsifiable prediction is a positive paired risk difference. A full
2x2 paired table, exact two-sided McNemar p value, and 95% paired BCa bootstrap
interval (100,000 seeded resamples) will be reported. `proof_prefix -
irrelevant` and `full - conclusion_only` are planned secondary contrasts and
are controlled by Holm adjustment within a model/family. Class-stratified
effects are descriptive unless powered separately.

The prospective size targets 80% or greater normal-approximation power for a
paired 15 percentage-point difference with expected discordance 0.35:
approximately 123 paired items before continuity correction. The 192-item
panel permits the planned three-class balance, partial degradation from the
development estimate, and a 10% receipt-loss buffer while retaining at least
160 analysable pairs. This is a design calculation, not a post-hoc power claim
for v7.

## Decision interpretation

- If `proof_prefix` does not exceed `conclusion_only`, the data support
  solver-assisted answer provision, not evidence that intermediate proof state
  supports final inference.
- If `proof_prefix` exceeds both `conclusion_only` and `irrelevant`, the study
  supports a limited system-level inference-support result in the qualified
  model/task envelope. It still does not identify an internal cognitive process
  or a universal repair theory.
- If only `full` improves, the effect is compatible with external answer
  provision.
- A model failing delivery qualification is not included in causal aggregation.

## Required public release

Release before submission includes code, fixed generator seeds, public panels,
sealed authorities after terminal scoring, prompt templates, certificates,
model/config/weight manifests, exact candidate token ids, package/runtime
manifest, per-item likelihood receipts, analysis script, manuscript source, and
a SHA-256 manifest with a one-command verifier.
