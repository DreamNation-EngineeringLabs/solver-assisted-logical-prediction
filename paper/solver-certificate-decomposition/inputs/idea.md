# Idea Summary

## Problem Statement

### The observation that needs explaining

Paste a solver's verified proof into a small language model's prompt and its
accuracy on rule-chaining queries jumps from chance to near-perfect. Two
explanations produce that identical number:

- **Answer reading.** The proof contains the conclusion; the model copies it.
- **State use.** The model works with the supplied premises and completes the
  remaining inference itself.

One says nothing about machine reasoning. The other says something specific.
Almost no published work on solver-, tool- or retrieval-augmented systems
separates them, because the accuracy gain looks the same either way.

## The gap in existing controls

The standard control is a same-shape irrelevant proof. That rules out generic
proof length, generic validity and proof formatting — but not answer reading,
because a relevant certificate remains answer-diagnostic even when the response
token is withheld. A prefix that stops one step short still names the query's
subject and predicate in adjacent lines, so a model that checks surface
co-occurrence reproduces every number a reasoning model would.

## Core Hypothesis

When a solver certificate improves a small model's accuracy on rule-chaining
queries, the improvement is attributable to the model **tracking the logical
validity of the supplied derivation**, not to surface overlap between the
certificate and the query.

Falsifiable form: hold line count, line types, query-entity occurrence count,
query-predicate presence and token length fixed, and destroy validity alone. If
the effect is surface overlap, accuracy is unchanged. If it is validity
tracking, accuracy collapses and sensitivity (d') drops with it.

A second hypothesis, tested in the same design: validity tracking, if present,
confers **no resistance to a corrupted apparatus** — a valid-looking certificate
pointing the wrong way will be followed.

## Approach

Three sealed experiments on frozen small models, scored by direct next-token
likelihood over verified single-token candidates. No free text is generated, so
nothing is parsed or inferred from prose.

1. **A 2x2 reanalysis of a completed five-arm factorial.** The arms form a
   square of *answer evidence* x *proof state*. Reading its edges instead of its
   diagonal recovers a state main effect the original analysis missed, and
   splitting by class shows the reported baseline was a biased responder rather
   than a chance responder.
2. **A ten-arm mechanism decomposition.** Hold every surface property fixed —
   line count, line types, query-entity occurrence count, query-predicate
   presence, token length — and destroy validity alone. This splits the state
   effect into a *surface overlap* component and a *validity tracking*
   component. Additional arms vary entity repetition, line order, truncation
   depth, and supply a certificate whose fabricated final rule points the wrong
   way.
3. **A ten-model three-class survey.** Adds a formally certified
   *undetermined* class — items where a chain-closing rule is withheld and
   non-derivability is verified by forward-closure saturation — and asks which
   models can serve as the interface at all, and whether any can faithfully
   relay a solver's "cannot determine".

## Findings

- **The state effect is inference, not text matching.** 98.3% of it survives
  holding surface form fixed and breaking only the logic. The surface component
  is +1.0pp, indistinguishable from zero.
- **Entity repetition explains nothing.** A valid derivation about the query
  entity toward an unrelated predicate scores identically to one about a
  different entity entirely, despite mentioning the query subject four times
  rather than zero.
- **Inference depth is exactly one step.** Withholding two steps instead of one
  scores identically to supplying no certificate at all. A cliff, not a slope.
- **The architecture has no resistance to a corrupted apparatus.** Handed a
  valid-looking certificate whose fabricated final rule points the wrong way,
  the model follows it 189 times out of 192.
- **There is a minimum viable interface size, around 3B.** Three of ten models
  clear a per-class floor; below 1.7B they collapse to a single label whatever
  the solver supplies. The effect is not monotonic in scale — the largest model
  tested collapses while a 3B does not.
- **Accuracy alone is not reportable in this setting.** One arm scored 50.0% on
  a balanced panel with d' = 0.00 — zero discriminative signal, at or below a
  trivial always-one-label strategy.

## Contributions

1. An **answer-evidence decomposition** that separates solver-supplied answers
   from solver-supplied reasoning state, reusable for any tool-augmented system.
2. A **surface-matched invalidity control** (`broken_chain`) that isolates
   logical validity from every co-occurring surface cue, with per-item
   certification that the displayed lines do not settle the query.
3. A **forward-closure certifier** for constructing formally underdetermined
   items, validated at 23,240/23,240 against an independent labelled corpus.
4. Evidence that validity tracking is real, shallow, and confers **no protection
   against corrupted solver output** — a reliability result for the whole class
   of solver-in-the-loop architectures.
5. A **substrate-size floor** for the architecture, from a ten-model sweep.

## Claim boundary — maintained throughout

System-level effects are never upgraded to mechanism claims about the model's
own reasoning. Every arm without a near-complete supplied chain returns d' = 0,
so the models studied do not reason unaided; high accuracy with full solver
material describes a faithful transcriber, not a reasoner. Two prespecified
criteria were found invalid after the fact and replaced; both replacements are
labelled post hoc and the originals retained.
