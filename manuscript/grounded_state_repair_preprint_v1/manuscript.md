# Auditing Solver-Assisted Logical Prediction with a Sealed Five-Arm Certificate Factorial

**Anonymous author(s)**

*Preprint draft - 1 September 2026*

## Abstract

External solvers can supply language models with evidence that directly settles a query. Large gains in this setting do not, by themselves, show that a language model used an intermediate proof state or repaired its own reasoning. We report a sealed ProofWriter pilot, terminal three-class delivery diagnostics, and a completed prospective **five-arm** binary certificate factorial: no certificate, irrelevant proof, conclusion only, proof prefix with the terminal literal omitted, and full proof. In the pilot, a frozen Qwen2.5-3B model reached 187/192 correct (97.4%) with a query-relevant certificate, versus 91/192 (47.4%) with a same-shape query-irrelevant certificate; the paired risk difference was 0.500 (exact two-sided McNemar *p* = 6.25 x 10^-28). In the fresh 192-item binary factorial, the model reached 91/192 (47.4%) with no certificate, 96/192 (50.0%) with an irrelevant proof, 176/192 (91.7%) with conclusion-only evidence, 167/192 (87.0%) with a proof prefix, and 191/192 (99.5%) with a full proof. The prespecified primary contrast, proof prefix minus conclusion only, was -0.047 (6 prefix-only versus 15 conclusion-only; exact McNemar *p* = 0.078). Thus the study does not show that a prefix improves performance beyond direct conclusion evidence. However, the prefix exceeded irrelevant proof by 0.370 (*p* = 1.51 x 10^-19), and full proof exceeded conclusion only by 0.078 (*p* = 6.10 x 10^-5; Holm-adjusted secondary tests). These are system-level effects of query-relevant solver material, not evidence that the model performed the proof or repaired an internal reasoning process. The three-class diagnostics remain important scope boundaries: Qwen2.5-3B failed the open-world unknown gate, and Qwen3-1.7B failed label-mapping invariance. We prepared, but have not publicly posted, a hash-checked local release package. The contribution is an auditable answer-evidence decomposition and a methodological warning: stable delivery, task competence, answer-evidence controls, and public artifacts are prerequisites for mechanism claims about reasoning repair.

**Keywords:** solver-assisted prediction; language-model reasoning; proof certificates; causal controls; output delivery; open-world reasoning; reproducibility

## 1. Introduction

Language models can be embedded in systems that retrieve, verify, or compute information externally. Such systems may improve accuracy substantially. But an improvement can have different causes: the model may use an external state as a working representation, or it may simply recognize that an externally supplied conclusion answers the question. These explanations have different implications for claims about reasoning, tools, and learned representations.

Natural-language chains of thought and scratchpads can improve task performance [1-3], yet their presence does not establish that a model's final decision was caused by the displayed steps [4,5]. The same issue arises more sharply for solver-produced certificates. A certificate that proves the query (or its inverse) is answer-diagnostic even if it omits the response token. A comparison with irrelevant text or malformed reasoning does not rule out external answer provision. It only becomes informative about intermediate-state use when a control separates the final conclusion from the preceding usable premises, rules, and derived state.

This paper reports a completed, sealed pilot on the public ProofWriter benchmark [6], a post hoc standard paired reanalysis, three terminal delivery/competence diagnostics, and a completed fresh binary five-arm factorial. The pilot establishes a large system-level effect of query-relevant solver evidence. The diagnostics prevent an overstatement of that result on the original three-class task; a distinct binary Yes/No qualification then authorized the five-arm factorial. We report both paths because an invalid output channel or a competence floor is not evidence that a treatment has no causal effect, while passing a narrow binary qualification does not establish open-world competence.

The paper makes four deliberately limited contributions:

- A fully reported paired system result for query-relevant versus same-shape query-irrelevant solver certificates in frozen Qwen2.5-3B.
- A prospective five-arm decomposition of no evidence, irrelevant proof, conclusion-only evidence, proof prefix, and full proof in a fresh binary task, with a prespecified proof-prefix-versus-conclusion-only primary contrast.
- A claim boundary that distinguishes system-level use of query-relevant proof material from internal reasoning repair, together with terminal diagnostics for arbitrary-label instability, open-world unknown-class failure, and label-mapping collapse.
- A prepared, hash-addressed local release package with prompts, certificates, answer authorities, raw likelihood receipts, model/runtime details, and executable analysis; public posting and a DOI remain pending.

:::study-flow

## 2. Related work

### 2.1 Reasoning traces, faithfulness, and answer evidence

Chain-of-thought prompting can improve accuracy on arithmetic, symbolic, and commonsense tasks [1], and scratchpads expose intermediate computation to a model [2]. Neither result alone identifies whether an observed trace is causally used by the model. Faithfulness work has shown that a plausible natural-language rationale need not reflect the determinants of a model's prediction [3-5]. In particular, counterfactual and mediation analyses motivate distinguishing a displayed explanation from the actual computation or evidence that produced an answer [4,5]. Our concern is narrower: a solver certificate can be valid and useful as external evidence while still failing to show that the receiving model performed the derivation.

### 2.2 Solvers, tools, and formal proof environments

Verifiers can improve reasoning-system outcomes [7], and tool-use systems can learn when and how to incorporate external API outputs into language-model prediction [8]. Formal theorem-proving environments likewise make proof validity and premise access explicit [9]. These lines of work show why solver assistance can be valuable, but they do not make LLM mediation necessary. If a trusted solver already returns the desired answer, directly using that answer is generally simpler and more reliable. An LLM-mediated certificate is useful only in a broader system that must interpret, combine, communicate, or act on solver output; that system-level role is not evaluated here.

### 2.3 Delivery, label bias, and benchmark validity

Multiple-choice labels are an output interface, not a neutral measurement device. Contextual calibration and option order can affect prompted classification [10,11]. This motivates testing whether a model can deliver semantically sensitive responses before interpreting a treatment-control contrast. Benchmark provenance matters as well. ProofWriter is a public synthetic resource [6]; disjointness from our earlier local panels does not establish independence from model pretraining. Finally, open-world unknown cases are substantively different from contradicted cases. Excluding them simplifies the task and limits generalization.

## 3. Completed sealed pilot

### 3.1 Model, task, and intervention

The primary pilot used a frozen local MLX snapshot of Qwen2.5-3B-Instruct-4bit. It was scored by direct next-token likelihood over certified single-token `A` and `B` candidates, with `A = entailed` and `B = contradicted`; no free-text answer was generated. The underlying public ProofWriter task was restricted to binary derivable queries, so it excluded the benchmark's unknown class.

For each selected theory, the prompt included numbered facts and rules plus one of three conditions. The query-relevant condition supplied a solver-verified natural-language derivation of the query or its inverse. The matched irrelevant condition supplied an independently valid derivation for another conclusion in the same theory, exactly matched in fact/rule/intermediate line-type sequence. The no-certificate condition supplied no derivation. All certificates excluded `A`, `B`, *entailed*, and *contradicted*. The relevant certificate nevertheless made the answer available: its final derived literal established the query's truth or its inverse.

The pilot used a 32-item base screen, a 96-item positive-control panel, and a fresh 192-item depth-4 prospective panel. Results were sealed until the preceding gate passed. There were no training runs, prompt sweeps, automatic restarts, or panel substitutions. The package preserves task prompts, certificates, answer authorities, source hashes, code-freeze records, and direct-likelihood receipts.

### 3.2 Analysis

The original pilot reported exact paired McNemar tests and a custom Wilson sensitivity envelope. That envelope is retained in the immutable terminal record but is not used as the publication-facing uncertainty estimate. We instead report the complete 2x2 paired table, exact two-sided McNemar test [12], and a clearly labeled post hoc 95% nonparametric paired BCa bootstrap interval with 100,000 deterministic resamples [13]. This reanalysis does not change the outcomes or reopen the sealed study.

No effect-size sample-size calculation was recorded for the completed v7 pilot. Its 192-item panel is therefore not presented as a power-justified confirmatory design for a broad theory. The later b14 factorial was separately sealed with a prospective design calculation; it is reported in Section 5.5 and does not retroactively change the pilot's status.

## 4. Pilot results

Qwen2.5-3B passed the original base screen with 24/32 correct. On the locked positive-control panel, query-relevant certificates were correct on 95/96 items, compared with 54/96 for query-irrelevant certificates and 60/96 with no certificate. On the prospective panel, query-relevant certificates were correct on 187/192 items (97.4%), query-irrelevant certificates on 91/192 (47.4%), and no certificate on 106/192 (55.2%).

| Comparison | Left correct | Right correct | Paired risk difference | Exact McNemar *p* | 95% paired BCa interval |
| --- | ---: | ---: | ---: | ---: | --- |
| Relevant certificate - irrelevant certificate | 187/192 | 91/192 | +0.500 | 6.25 x 10^-28 | [0.427, 0.573] |
| Relevant certificate - no certificate | 187/192 | 106/192 | +0.422 | 1.89 x 10^-22 | [0.349, 0.495] |

| Relevant versus irrelevant paired outcome | Count |
| --- | ---: |
| Both correct | 90 |
| Relevant-only correct | 97 |
| Irrelevant-only correct | 1 |
| Neither correct | 4 |

The large paired difference rules out generic added proof length, generic proof validity, and the matched within-theory proof format as complete explanations. It does **not** rule out the central alternative: the model can recognize that the externally supplied final literal settles the query and map that evidence to the response token. The supported result is therefore solver-assisted forced-choice prediction, not proof that an explicit state repaired the model's own logical inference.

## 5. Follow-up delivery and competence diagnostics

### 5.1 Why the factorial was needed

The decisive mechanism test was specified before the follow-up calls. Every eligible binary task would be evaluated in five matched arms: no certificate, valid irrelevant proof, conclusion-only solver evidence, proof prefix with its final conclusion omitted, and full certificate. A proof-prefix advantage over both conclusion-only and irrelevant controls would be stronger evidence that supplied intermediate state supports the model's final inference. If full proof only matched conclusion-only evidence, the result would be consistent with external answer provision.

The initial fresh protocol used post-training procedural generation with nonce vocabularies, a three-class open-world task, and a 192-item panel balanced across entailed, contradicted, and unknown outcomes. Exact item novelty does not prove pretraining independence, but it avoids reuse of public ProofWriter items and makes generation and solver closure auditable. Its output-interface gates are reported below as terminal diagnostics. The completed b14 successor retained post-training nonce generation and the five arms but deliberately restricted the task to binary derivable queries; it used the same predeclared primary contrast, proof prefix minus conclusion-only evidence, a full paired table, exact McNemar test, and seeded BCa interval. Its 192-item panel was selected from a prospective design calculation targeting a 15-percentage-point paired difference with expected discordance 0.35 (normal-approximation 80% power at *n* = 123).

### 5.1a Compact worked five-arm example

This illustrative, v10-format item shows exactly what the factorial would distinguish; it is not a result-bearing item. **Theory:** `Pava is copper. Dori is striped. All copper people are calm. All calm people are trusted. All striped people are swift. All swift people are alert.` **Query:** `Pava is trusted.` The response mapping is `A = entailed`, `B = contradicted`, and `C = unknown`.

- **None:** no solver record is added.
- **Irrelevant proof:** `Dori is striped -> Dori is swift -> Dori is alert.` This is valid and similarly structured, but concerns the donor entity rather than the query.
- **Conclusion only:** `Solver-verified conclusion: Pava is trusted.` This supplies answer evidence without intermediate proof state.
- **Proof prefix:** `Pava is copper; all copper people are calm; Pava is calm; all calm people are trusted.` The terminal literal `Pava is trusted` is deliberately omitted.
- **Full proof:** the proof prefix plus `Pava is trusted.`

The shared prompt is `Use only the stated rules, facts, and any solver record. Return exactly one response label. [theory] [certificate arm] Query: Pava is trusted. A = entailed. B = contradicted. C = unknown. Answer:`. For every arm, the model is scored without free-text generation: `prediction = argmax(logit(A), logit(B), logit(C))`, using fixed, verified single-token candidate ids (in the Qwen3 v10 screen: `A = 32`, `B = 33`, `C = 34`). Thus conclusion-only isolates direct external answer evidence, while proof prefix tests whether the model can use the supplied intermediate material to carry out the last inference.

### 5.2 Arbitrary response-label qualification failed

Before opening the factorial, Qwen2.5-3B was tested on 36 direct-fact items under two prompts that differed only in the mapping between semantic outcomes and `A`/`B`/`C`. The qualification required at least 27/36 correct under each mapping, at least 8/12 correct in every class under each mapping, and at least 32 semantically consistent responses across mappings.

The model scored 25/36 under the ordinary mapping and 13/36 under the counterbalanced mapping, with semantic agreement on 22/36 items. It was 12/12 on entailed items under the counterbalanced mapping but 1/12 on contradicted and 0/12 on unknown items. The arbitrary-label interface was therefore not qualified. This is a delivery failure; it says nothing about any certificate arm because the factorial was not opened.

The full confusion matrices show the direction of this instability. In the ordinary map, the model largely preserved entailed and contradicted labels but frequently mapped unknown to contradicted. Under the counterbalanced map, it still recognized entailed items, but contradicted and unknown items shifted toward the entailed or contradicted semantic labels rather than the required counterbalanced labels.

| Qwen2.5-3B v8 ordinary map: true / predicted semantic class | Entailed | Contradicted | Unknown |
| --- | ---: | ---: | ---: |
| Entailed | 12 | 0 | 0 |
| Contradicted | 3 | 9 | 0 |
| Unknown | 0 | 8 | 4 |

| Qwen2.5-3B v8 counterbalanced map: true / predicted semantic class | Entailed | Contradicted | Unknown |
| --- | ---: | ---: | ---: |
| Entailed | 12 | 0 | 0 |
| Contradicted | 11 | 1 | 0 |
| Unknown | 2 | 10 | 0 |

### 5.3 Semantic-token qualification exposed unknown-class failure

A separately sealed engineering qualification replaced arbitrary labels with direct semantic candidates `Yes`, `No`, and `Unknown` and used two equivalent wording/order templates. This interface was perfectly stable across templates (36/36 agreement). However, it achieved 24/36 correct on each template: 12/12 entailed, 12/12 contradicted, and 0/12 open-world unknown. Thus the limiting problem was not merely response-token mapping. The frozen 3B model did not meet the predeclared three-way task-competence gate.

The two templates produced the same semantic confusion matrix. Unknown items were consistently mapped to `No` rather than `Unknown`, showing that the failure is a systematic open-world collapse rather than random uncertainty.

| Qwen2.5-3B v9: true class / predicted semantic class | Entailed (`Yes`) | Contradicted (`No`) | Unknown (`Unknown`) |
| --- | ---: | ---: | ---: |
| Entailed | 12 | 0 | 0 |
| Contradicted | 0 | 12 | 0 |
| Unknown | 0 | 12 | 0 |

### 5.4 Fresh Qwen3 successor: scoring fixed, semantic delivery failed

The initial Qwen3-1.7B v8 qualification ended before its first score because its MLX bfloat16 candidate-logit buffer could not be converted directly to NumPy. V8 remains terminal. We therefore sealed one fresh v10 successor with a new nonce-generated 36-item qualification panel and 192-item prospective panel. The sole runtime change was an explicit MLX float32 cast followed by conversion through a Python list; prompts, model, candidate labels, construction rule, and analysis plan were unchanged. The scoring path completed, but the model selected raw label `A` for all 36 items under both response mappings.

Under the ordinary mapping, `A` denotes entailed; under the counterbalanced mapping, it denotes contradicted. The two semantic confusion matrices therefore diagnose label anchoring directly, rather than a failure attributable to one class alone.

| Qwen3-1.7B v10 ordinary map: true / predicted semantic class | Entailed | Contradicted | Unknown |
| --- | ---: | ---: | ---: |
| Entailed | 12 | 0 | 0 |
| Contradicted | 12 | 0 | 0 |
| Unknown | 12 | 0 | 0 |

| Qwen3-1.7B v10 counterbalanced map: true / predicted semantic class | Entailed | Contradicted | Unknown |
| --- | ---: | ---: | ---: |
| Entailed | 0 | 12 | 0 |
| Contradicted | 0 | 12 | 0 |
| Unknown | 0 | 12 | 0 |

The screen scored 12/36 under each mapping with 0/36 semantic agreement, far below the preregistered thresholds of 27/36 per mapping, at least 8/12 in every class, and 32/36 agreement. It did not authorize the prospective panel. This is a terminal delivery result, not a five-arm treatment result.

The v8 and v10 prospective factorials remain unopened. These diagnostics are not a replication, a model-size comparison, or evidence that proof prefixes do not work. They are the reason that no such claim is made.

### 5.5 Completed binary five-arm factorial (b14)

The three-class diagnostics did not authorize a treatment comparison. They did, however, identify a narrower binary derivable-query envelope in which Qwen2.5-3B could be measured directly with `Yes` and `No` candidates. We sealed b14 as a fresh post-training nonce-generated binary panel rather than reopening a failed three-class panel. The task explicitly excludes open-world unknown outcomes. Its five matched prospective arms were: **none**, **irrelevant proof**, **conclusion only**, **proof prefix**, and **full proof**. The proof-prefix arm contained solver-verified facts, rules, and intermediate derivations, but omitted the terminal literal that established the query or its inverse. The irrelevant-proof arm supplied a valid donor-entity derivation; the conclusion-only arm supplied only the terminal derived literal.

Before opening the answer authority, the direct `Yes`/`No` interface had to reach at least 27/36 correct under each of two equivalent templates, at least 12/18 correct in each class under each template, and at least 32/36 candidate agreement. Qwen2.5-3B scored 36/36 under the direct template and 33/36 under the reordered template, with 33/36 candidate agreement. It therefore authorized one 192-item prospective execution. All five 192-item receipt files were written before the prospective answer authority was opened; no prompt sweep, retry, data substitution, or automatic successor was authorized.

| Arm | Correct / 192 | Accuracy |
| --- | ---: | ---: |
| No certificate | 91 | 47.4% |
| Irrelevant proof | 96 | 50.0% |
| Conclusion only | 176 | 91.7% |
| Proof prefix (terminal literal omitted) | 167 | 87.0% |
| Full proof | 191 | 99.5% |

The prespecified primary contrast was proof prefix minus conclusion only. Its complete paired table was 161 both correct, 6 prefix-only correct, 15 conclusion-only correct, and 10 neither correct. The paired risk difference was -0.047, with exact two-sided McNemar *p* = 0.078 and a seeded 95% paired BCa interval of [-0.094, -0.005]. We treat the exact test as the decision criterion specified in the protocol: the primary comparison did not support a proof-prefix advantage over conclusion-only evidence.

| Comparison | Left-only | Right-only | Paired risk difference | Exact McNemar *p* | 95% paired BCa interval |
| --- | ---: | ---: | ---: | ---: | --- |
| Proof prefix - conclusion only (primary) | 6 | 15 | -0.047 | 0.078 | [-0.094, -0.005] |
| Proof prefix - irrelevant proof | 73 | 2 | +0.370 | 1.51 x 10^-19 | [0.302, 0.443] |
| Full proof - conclusion only | 15 | 0 | +0.078 | 6.10 x 10^-5 | [0.047, 0.125] |

The two secondary comparisons were Holm-adjusted within model (adjusted *p* = 3.02 x 10^-19 for proof prefix minus irrelevant proof; adjusted *p* = 6.10 x 10^-5 for full proof minus conclusion only). The proof prefix therefore improved this frozen LLM-mediated system markedly over a valid irrelevant proof despite omitting the final conclusion. Full proof also improved over conclusion-only evidence. Neither pattern establishes that an explicit state repaired the model's internal reasoning: a relevant derivation can still serve as highly diagnostic external evidence, and the full certificate adds redundant, query-aligned answer support. Conversely, the nonsignificant and directionally negative primary contrast means this experiment does not show that the prefix is better than direct conclusion evidence. The supported conclusion is limited to system-level effects of query-relevant solver material in this binary task envelope.

## 6. Reproducibility and prepared release materials

We prepared a local, hash-checked release package. It includes the selected v7 panels and sealed authorities; all three v7 prompt conditions and certificates; per-item candidate logits and margins; gate, code-freeze, terminal, and scoring records; model config and weight hashes; candidate token ids; an environment manifest; the post hoc paired analysis; the v8, v9, and v10 protocols and receipts; and the b14 public and sealed panels, protocol, code freezes, qualification and prospective receipts, terminal record, and factorial aggregate. The package also contains a machine-readable manifest and verifier instructions.

Before public posting, the archive should be placed in a versioned repository or archival service and accompanied by a permanent DOI. ProofWriter source and derivative-data licence terms must be reviewed before redistribution. The local archive is an artifact record, not a substitute for a public repository.

## 7. Limitations

This work is one frozen 3B model, one completed public synthetic benchmark pilot, one fresh synthetic binary factorial, and terminal qualification screens. It does not establish transport across model families, sizes, tasks, prompt interfaces, or deployment settings. Qwen3-1.7B is not a replication: in the fresh v10 screen it selected `A` for every item under both mappings, and it was not included in the completed b14 factorial.

ProofWriter may have been represented in pretraining. Theory disjointness within local experiments does not resolve that possibility. B14 used exact post-training nonce generation, but that establishes item novelty rather than independence from all relevant pretraining patterns. Both the pilot and b14 exclude unknown cases, while the fresh three-class qualification shows that open-world unknown is a material competence boundary for the frozen 3B model. The b14 proof prefix omits the terminal literal but remains query-relevant external evidence; the factorial cannot identify whether the model internally executed the final inference rather than recognized an answer-diagnostic derivation. Finally, a trusted solver can answer these rule tasks directly; this paper does not establish a practical advantage to routing its result through an LLM.

## 8. Conclusion

In a sealed binary ProofWriter pilot, query-relevant solver-produced proof evidence markedly improved frozen Qwen2.5-3B forced-choice accuracy over an equally valid query-irrelevant proof. In the completed, fresh five-arm binary factorial, proof-prefix evidence without the terminal literal greatly improved performance over irrelevant proof, and full proof improved over conclusion-only evidence. These are robust system-level results in a narrow task envelope.

The stronger state-use hypothesis remains unresolved. The prespecified proof-prefix-versus-conclusion-only comparison was not significant and favored conclusion-only evidence numerically. Before interpreting solver assistance as internal reasoning repair, one must establish a semantically stable output channel, competence on every included task class, controls for direct answer evidence, multiple models and task families, and a public artifact record. This paper therefore reports solver-assisted logical prediction and an answer-evidence decomposition, not a general causal theory of reasoning repair.

## References

[1] Wei, J., Wang, X., Schuurmans, D., et al. (2022). Chain-of-Thought Prompting Elicits Reasoning in Large Language Models. *NeurIPS 2022*. https://arxiv.org/abs/2201.11903

[2] Nye, M., Andreassen, A. J., Gur-Ari, G., et al. (2021). Show Your Work: Scratchpads for Intermediate Computation with Language Models. https://arxiv.org/abs/2112.00114

[3] Lyu, Q., Havaldar, S., Stein, A., et al. (2023). Faithful Chain-of-Thought Reasoning. *IJCNLP-AACL 2023*. https://aclanthology.org/2023.ijcnlp-main.20/

[4] Turpin, M., Michael, J., Perez, E., and Bowman, S. R. (2023). Language Models Don't Always Say What They Think: Unfaithful Explanations in Chain-of-Thought Prompting. https://arxiv.org/abs/2305.04388

[5] Paul, D., West, R., Bosselut, A., and Faltings, B. (2024). Making Reasoning Matter: Measuring and Improving Faithfulness of Chain-of-Thought Reasoning. *Findings of EMNLP 2024*. https://aclanthology.org/2024.findings-emnlp.882/

[6] Tafjord, O., Dalvi Mishra, B., and Clark, P. (2021). ProofWriter: Generating Implications, Proofs, and Abductive Statements over Natural Language. *Findings of ACL 2021*. https://arxiv.org/abs/2012.13048

[7] Cobbe, K., Kosaraju, V., Bavarian, M., et al. (2021). Training Verifiers to Solve Math Word Problems. https://arxiv.org/abs/2110.14168

[8] Schick, T., Dwivedi-Yu, J., Dessi, R., et al. (2023). Toolformer: Language Models Can Teach Themselves to Use Tools. https://arxiv.org/abs/2302.04761

[9] Yang, K., Swope, A. M., Gu, A., et al. (2023). LeanDojo: Theorem Proving with Retrieval-Augmented Language Models. *NeurIPS 2023*. https://arxiv.org/abs/2306.15626

[10] Zhao, T. Z., Wallace, E., Shi, F., Klein, D., and Singh, S. (2021). Calibrate Before Use: Improving Few-Shot Performance of Language Models. https://arxiv.org/abs/2102.09690

[11] Pezeshkpour, P., and Hruschka, E. (2024). Large Language Models Sensitivity to The Order of Options in Multiple-Choice Questions. *Findings of NAACL 2024*, 2006-2017. https://aclanthology.org/2024.findings-naacl.130/

[12] McNemar, Q. (1947). Note on the Sampling Error of the Difference between Correlated Proportions or Percentages. *Psychometrika*, 12, 153-157. https://doi.org/10.1007/BF02295996

[13] Efron, B. (1987). Better Bootstrap Confidence Intervals. *Journal of the American Statistical Association*, 82, 171-185. https://doi.org/10.1080/01621459.1987.10478410
