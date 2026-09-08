# Research Brief

## §1 · Core Claim and Narrative
_Written by: outline-agent, Step 1_

**Core claim:** When a solver certificate improves a small model's accuracy on
rule-chaining queries, 98.3% of that improvement is the model tracking the
*logical validity* of the supplied derivation rather than matching surface
overlap between certificate and query — and that validity tracking is shallow
(exactly one inference step) and confers no resistance to a corrupted apparatus.

**Narrative tension:** Solver-, tool- and retrieval-augmented systems report
large accuracy gains and read them as evidence the model used the supplied
information. Answer reading and state use produce identical numbers, and the
standard irrelevant-proof control does not separate them.

**Key novelty framing:** Not "does solver assistance help" (settled) but "what
exactly is the model doing with it", answered by a surface-matched invalidity
control that holds line count, line types, entity occurrence count, predicate
presence and token length fixed while destroying validity alone.

**Outline decisions:**
- Plotting plan: 3 figures, all real renders from sealed results
- Related Work clusters: faithfulness of displayed reasoning; solver- and
  tool-augmented reasoning; synthetic deductive benchmarks; response bias and
  the limits of accuracy
- Section structure: Introduction, Related Work, Method, Experimental Setup,
  Results, Limitations, Conclusion

**Potential weaknesses flagged at outline stage:**
- Inference depth is exactly one step — a reviewer will press on whether
  "validity tracking" overstates a single pre-assembled modus ponens.
- One task family; the mechanism result rests on a single model.
- Two post hoc corrections (the b14 2x2 reading, the b16 viability criterion)
  must be labelled at point of use, not only in a footnote.
- Formalisation is untested, which matters because 5.3 implies a formalisation
  error would propagate silently.

---

## §2 · Literature Landscape
_Written by: literature-review-agent, Step 3_

**What the literature says about the core claim:** The faithfulness literature
has built exactly the manipulations this paper needs — truncating a reasoning
trace and injecting mistakes into it — but applies them to *model-generated*
traces, asking whether the model's own account is honest. The solver-augmented
literature supplies the architecture and reports large end-to-end gains, but
attributes them to the pipeline as a whole; no located work separates the
answer channel from the state channel, and none measures behaviour under a
wrong-but-well-formed solver output. The two bodies of work therefore leave the
attribution question this paper asks genuinely open, which is a good position
for the paper and should be stated plainly rather than as a takedown.

**Strongest prior work (must address in the paper):**
- `lanham2023measuring`: the closest methodological antecedent. Its early-answering
  (truncation) and mistake-injection interventions are what the truncate-k and
  `misleading` arms adapt. Any reviewer who knows this paper will ask what is new;
  the answer is the object (external verified state, not a self-generated trace)
  and the surface-matched invalidity control, not the manipulation itself.
- `pan2023logiclm`, `olausson2023linc`, `ye2023satlm`: the systems whose reported
  gains motivate the decomposition. Frame as the target of the measurement
  critique, never as baselines this paper outperforms — none is evaluated against.
- `turpin2023language`: establishes that a displayed rationale can misrepresent the
  cause of an answer; the general licence for asking the attribution question.
- `tafjord2020proofwriter`: the only public corpus touched, and only as the
  independent check on the forward-closure certifier (23,240/23,240).
- `zhao2021calibrate`, `zheng2023large`, `pezeshkpour2023large`: the bias literature
  that makes the d'-and-criterion reporting rule defensible rather than idiosyncratic.

**Gaps confirmed by the literature:**
- No located solver-augmented paper controls for answer reading; the standard
  control is a same-shape irrelevant record, which does not separate the channels.
- No located work in either cluster measures a solver-in-the-loop system under a
  corrupted certificate.
- Public deductive benchmarks (RuleTaker, ProofWriter, PrOntoQA, FOLIO) supply
  proofs but no matched adversarial certificate variants, and all predate the
  models evaluated on them.
- Signal detection reporting is standard in psychophysics and absent from
  solver-augmented reasoning evaluation.

**Baseline comparisons — verification status:**

| Baseline | In citation_pool? | Confidence tier |
|---|---|---|
| `none` (no solver material) | n/a — internal arm | n/a |
| `irrelevant` (valid donor-entity chain) | n/a — internal arm | n/a |
| always-one-label trivial strategy | n/a — internal arm | n/a |
| Logic-LM (context, not compared against) | yes, `pan2023logiclm` | high |
| LINC (context, not compared against) | yes, `olausson2023linc` | high |
| SatLM (context, not compared against) | yes, `ye2023satlm` | high |

No external system is evaluated against in `experimental_log.md`. Every cited
system is context only; the EVALUATION RULE forbids any "beats" framing.

**Related Work cluster coverage:**

| Cluster | Papers found | Notes |
|---|---|---|
| Faithfulness of displayed reasoning | 6 | wei, turpin, lanham, lyu, arcuschin, chen2025 |
| Solver-/tool-augmented reasoning | 8 | pan, olausson, ye, gao, schick, yang, lewis, plus shi/xie on context sensitivity |
| Synthetic deductive benchmarks | 8 | clark, tafjord, saparov, han, chen2024premise, wu, deng, golchin |
| Response bias and limits of accuracy | 10 | zhao, pezeshkpour, zheng, holtzman, kadavath, yin, macmillan, stanislaw, mcnemar, efron |
| Model reports (Intro) | 6 | qwen2.5, llama 3, gemma 3, phi-4-mini, olmo 2, smollm2 |

**Anything the section-writing agent should know:**
- 39 verified references; `workspace/refs.bib` keys are canonical and already
  100% cited in `intro_relwork.tex`. Reuse those keys; do not invent new ones.
- Two candidates were dropped for failing corroboration (Sharma et al. on
  sycophancy; Yao et al., ReAct) — neither is cited anywhere and neither should
  be reintroduced without verification.
- Semantic Scholar was unavailable (no API key); verification rests on OpenAlex
  + Crossref, with the arXiv API used by hand for one entry. See
  `workspace/cross_verification_report.json`.
- The Intro already states the claim boundary (transcriber, not reasoner) and
  the d'-alongside-accuracy rule. Do not restate them as new in later sections;
  extend them.
- Numbers used in the Intro, all from `experimental_log.md`: +60.4pp validity
  component, +1.0pp surface component, 98.3% validity share, +0.0pp entity
  repetition, 189/192 on `misleading`, 3 of 10 viable substrates, 50.0% at
  d' = 0.00, 23,240/23,240 certifier validation.
