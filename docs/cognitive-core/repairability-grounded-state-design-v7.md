# Grounded proof-state causal repairability design v7

## Constraint from v6

The v6 reference-state test found no evidence that a frozen Qwen2.5-3B model
could use label-free `F/R/I` pointer strings.  Verified state scored 61/96,
corrupted state 60/96, and no state 62/96.  This was a valid delivery failure
of an *opaque reference* state, not a general test of a grounded solver state.

## Primary intervention

v7 supplies a solver-verified, natural-language derivation certificate at
inference.  Each certificate lists only the facts, rules, and derived
intermediate statements used by a stored ProofWriter proof.  It contains no
`A`/`B` answer token and no words `entailed` or `contradicted`.  Its final
derived statement is textually grounded, allowing the model to compare a
verified conclusion with the visible query.

The matched control is not a malformed trace.  It is an equally structured,
same-depth, independently valid certificate for a different conclusion from
the *same theory*.  Thus it holds solver validity, natural-language state,
line count, fact/rule/intermediate structure, and within-theory lexical context
fixed while removing relevance to the queried conclusion.

The primary estimand is verified-query-relevant certificate minus valid,
query-irrelevant certificate.  A no-certificate arm is secondary.

## Panels and gates

New deterministic, balanced panels exclude every theory used in v4 or v6:

| Role | Source member | Depth | Count |
| --- | --- | ---: | ---: |
| Base qualification | `OWA/depth-3/meta-train.jsonl` | 3 | 32 |
| Positive control | `OWA/depth-3/meta-test.jsonl` | 3 | 96 |
| Prospective panel | `OWA/depth-5/meta-train.jsonl` | 4 | 192 |

The source audit regenerates both certificates, independently forward-checks
their targets and intermediates, confirms the control conclusion differs from
the queried proof target, and checks that both certificates share an exact
sequence of fact/rule/intermediate line types.

The frozen Qwen2.5-3B direct A/B base gate is 8–24 correct of 32.  The one
positive-control gate requires verified state to gain at least six correct of
96 over the valid irrelevant state, exact two-sided paired McNemar p < 0.05,
and no loss to the no-state baseline.  Only then can the deeper depth-4
prospective authority open.  No training, retries, sweeps, automatic successors, or panel
substitutions are authorized.

## Interpretation

A success identifies a system-level explicit-state/verification repair in this
task envelope.  It does not show that the model learned the procedure, that
certificate delivery is universally sufficient, or that parameters must be
changed.  A failure identifies no grounded-certificate effect under this fixed
interface; it does not negate the prior valid tool route.
