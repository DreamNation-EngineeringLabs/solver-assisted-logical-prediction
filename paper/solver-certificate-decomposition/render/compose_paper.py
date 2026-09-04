#!/usr/bin/env python3
"""Step 4 — compose paper.tex from intro_relwork.tex plus the remaining sections.

Preamble, Introduction and Related Work are preserved verbatim from Step 3.
Every numeric value below traces to inputs/experimental_log.md. LaTeX patterns
follow papers/solver-certificate-decomposition/tex_profile.json (cleveref, nicefrac, microtype, T1 all True).
"""
import pathlib, re

PAPER = pathlib.Path(__file__).resolve().parents[1]


def apply_layout(src: str) -> str:
    """Two-column ICLR layout and the trims that bring the draft to 9 pages.

    This belongs here, not in a hand-edit of drafts/paper.tex: the composer
    rebuilds from the single-column intro_relwork.tex, so any manual layout fix
    is silently discarded the next time it runs.
    """
    src = src.replace("\\documentclass[10pt]{article}",
                      "\\documentclass[10pt,twocolumn]{article}", 1)
    src = src.replace("\\usepackage[letterpaper,margin=1in]{geometry}",
                      "\\usepackage[letterpaper,margin=0.9in,columnsep=0.28in]{geometry}", 1)
    src = src.replace("\\setlength{\\parskip}{2pt}",
                      "\\setlength{\\parskip}{2pt}\n\\sloppy\n\\emergencystretch=2em", 1)
    src = src.replace("\\usepackage{xcolor}",
                      "\\usepackage{xcolor}\n\\usepackage{microtype}\n"
                      "\\usepackage{nicefrac}\n\\usepackage{url}\n\\usepackage{cleveref}", 1)
    # tables compact
    src = src.replace("\\begin{table}[t]\n\\centering\n\\caption",
                      "\\begin{table}[t]\n\\centering\\small\n\\caption")
    # the two widest objects span both columns
    for label, env in (("tab:models", "table"), ("fig:arms", "figure")):
        m = re.search(r"\\begin\{" + env + r"\}\[t\].*?\\label\{" + re.escape(label)
                      + r"\}.*?\\end\{" + env + r"\}", src, re.S)
        if m:
            src = src.replace(m.group(0),
                              m.group(0).replace("\\begin{" + env + "}[t]", "\\begin{" + env + "*}[t]")
                                        .replace("\\end{" + env + "}", "\\end{" + env + "*}"), 1)
    # figure widths for a narrow column
    src = src.replace("width=0.72\\textwidth]{figures/answer_state_factorial",
                      "width=\\columnwidth]{figures/answer_state_factorial")
    src = src.replace("width=\\textwidth]{figures/arm_decomposition",
                      "width=0.86\\textwidth]{figures/arm_decomposition")
    src = src.replace("width=0.8\\textwidth]{figures/substrate_size_curve",
                      "width=\\columnwidth]{figures/substrate_size_curve")
    return src



src = (PAPER / "drafts/intro_relwork.tex").read_text()

TITLE = ("Reading Is Not Reasoning, and Reasoning Is Not Robustness:\\\\\n"
         "Decomposing What a Language Model Does with a Solver Certificate")

ABSTRACT = r"""
Solver-, tool- and retrieval-augmented language model systems report large
accuracy gains, and those gains are routinely read as evidence that the model
used the supplied material. Two mechanisms produce the same number: the model
reading a supplied answer, and the model reasoning over supplied state. The
standard control, a same-shape irrelevant record, separates neither. We build a
control that does. Across three sealed experiments on frozen small models,
scored by direct next-token likelihood over verified single-token candidates, we
decompose solver assistance into an answer channel and a state channel. Reading
a completed five-arm factorial as a $2\times2$ of answer evidence by proof state
recovers a state main effect of $+22.4$pp that its prespecified diagonal
contrast could not attribute. Holding line count, line types, query-entity
occurrence count, query-predicate presence and token length fixed across ten
arms and destroying validity alone gives a validity component of $+60.4$pp
against a surface component of $+1.0$pp: $98.3\%$ of the state effect is
inference over the supplied lines, not text matching. That inference is exactly
one step deep --- withholding two steps rather than one scores identically to
supplying nothing --- and it confers no robustness: given a valid-looking
certificate whose fabricated final rule establishes the negation, the model
follows it on 189 of 192 items ($d' = -4.36$). A ten-model three-class sweep,
whose \emph{undetermined} items are certified by forward-closure saturation
validated at $23{,}240/23{,}240$ against an independent corpus, finds three
viable substrates of ten and a minimum viable interface size near 3B, not
monotonic in scale. Two measurement lessons recur: an arm scoring $50.0\%$ on a
balanced panel with $d' = 0.00$, and a prespecified criterion that a degenerate
single-label responder maximised. We report sensitivity alongside accuracy
throughout, and never upgrade a system-level effect into a claim about the
model's own reasoning.
""".strip()

BODY = r"""
\section{Method}

\subsection{The answer-evidence decomposition}
\label{sec:decomposition}

A solver certificate carries two things at once: the \emph{answer} to the query,
and the \emph{state} from which that answer follows. End-to-end accuracy
conflates them. We separate them by arranging arms as a $2\times2$ of answer
evidence by proof state, with a no-material baseline outside the square.

Let \textsc{irrelevant} supply a valid derivation for a different entity (no
answer, no relevant state), \textsc{conclusion\_only} the derived terminal
literal alone (answer, no state), \textsc{proof\_prefix} the chain with that
literal withheld (state, no answer), and \textsc{full} both. A contrast along an
\emph{edge} of this square moves one factor; a contrast along the
\emph{diagonal} moves two, and a null on it attributes to neither. This is not a
statistical subtlety but an identification one: the prespecified primary
contrast of the experiment we reanalyse, \textsc{proof\_prefix} minus
\textsc{conclusion\_only}, is exactly that diagonal.

Reading the four edges instead gives a state main effect, the mean of the two
edges along which state is added, and an answer main effect defined
symmetrically.

\subsection{Surface-matched invalidity}
\label{sec:broken}

A prefix that stops one step short is not a clean state manipulation. It still
names the query's subject and predicate in adjacent lines, so surface
co-occurrence remains available. To isolate validity we construct
\textsc{broken\_chain}: one intermediate link is cut so the displayed lines no
longer reach the query, while every surface property is held fixed.

Concretely, against the matched \textsc{truncate\_1} arm we preserve the
query-entity occurrence count (audited per item, not approximately), the
presence of the query predicate in the final rule, the line count, the exact
fact/rule/literal type sequence, and token length within a recorded tolerance.
Every \emph{rule} displayed is a real rule of the theory; exactly one derived
literal is false. All 192 items are certified by forward-closure saturation
(\cref{sec:closure}) to leave the query \emph{undetermined} under the displayed
lines. The decomposition follows:
\begin{align}
\text{total state effect} &= \textsc{truncate\_1} - \textsc{irrelevant},\\
\text{surface component} &= \textsc{broken\_chain} - \textsc{irrelevant},\\
\text{validity component} &= \textsc{truncate\_1} - \textsc{broken\_chain}.
\end{align}

Four companion arms separate the remaining confounds.
\textsc{same\_entity\_irrelevant} supplies a valid derivation about the
\emph{query} entity toward an unrelated predicate: it names the query subject
four times where \textsc{irrelevant} names it zero times, and neither contains
the query predicate, so the pair isolates entity repetition alone.
\textsc{shuffled} presents \textsc{truncate\_1}'s lines in seeded random order,
separating a chain from a bag of statements. \textsc{truncate\_2} and
\textsc{truncate\_3} withhold two and three steps, giving a depth ladder.
\textsc{misleading} supplies a valid-looking chain whose single fabricated final
rule establishes the query's negation; the ground-truth answer is unchanged, so
a model that follows the supplied state answers incorrectly.

\subsection{Certifying underdetermination}
\label{sec:closure}

Showing that a query \emph{is} derivable is easy: exhibit the proof. Showing it
is \emph{not} requires saturating the theory's forward closure. Our certifier
operates under open-world semantics with explicit negation, so a negative
literal is derivable only if something derives it, never by failure to prove the
positive. Rule antecedents are ordinary literals, with no negation as failure,
which makes naive forward chaining sound and complete on this fragment.

Two safeguards matter for generated theories. The chaining loop carries an
explicit round cap and reports a \texttt{saturated} flag, so a malformed theory
fails loudly rather than spinning; and any theory deriving both an atom and its
negation is marked inconsistent and its items rejected rather than labelled. An
item is \emph{undetermined} when neither the query nor its negation appears in
the closure.

We validated the certifier before generating any panel, against the open-world
splits of an independently labelled corpus \citep{tafjord2020proofwriter} at
depths $0$, $1$, $2$, $3$ and $5$: $23{,}240$ of $23{,}240$ questions agree,
$100.00\%$, with perfectly diagonal confusion and zero unusable theories,
including $10{,}440$ undetermined items. No item enters a sealed panel without a
certification record.

\subsection{Measurement: sensitivity, not accuracy}
\label{sec:measurement}

Accuracy on a balanced panel is uninterpretable when the responder is biased.
One arm below scores $50.0\%$ --- apparent chance --- with an identical
$9/96$ ``Yes'' rate in \emph{both} classes, that is $d' = 0.00$: no
discriminative signal whatever, at or below the trivial always-one-label
strategy. We therefore report sensitivity $d'$ and criterion $c$ alongside
accuracy for every arm \citep{macmillan1991detection,stanislaw1999calculation},
using the loglinear correction for extreme rates. For the three-class panel the
headline scalar is balanced accuracy, the mean of per-class recalls, under which
chance is $33.3\%$ and a single-label responder scores exactly chance.

Paired contrasts report the complete $2\times2$ table, the exact two-sided
McNemar test \citep{mcnemar1947note} as the decision criterion, and a seeded
$100{,}000$-resample paired bias-corrected accelerated bootstrap interval
\citep{efron1987better}, with Holm adjustment within declared families.

\section{Experimental Setup}

\subsection{Task, panels and scoring}

All three experiments use rule-chaining queries over small theories of facts and
universally quantified rules. \Cref{tab:panels} lists the panels. The three
sealed panels are procedurally generated after model release with per-item nonce
vocabularies, are mutually disjoint, and fix derivation depth at four by
construction, recorded per item. The public corpus is used \emph{only} to
validate the certifier; no item from it is scored by any model here.

\begin{table}[t]
\centering
\caption{Datasets. The three sealed panels are nonce-generated and disjoint; the
public corpus validates the certifier only.}
\label{tab:panels}
\begin{tabular}{llrl}
\toprule
Panel & Classes & Items & Used by \\
\midrule
\texttt{b14} & entailed / contradicted & 192 & Experiment 1 \\
\texttt{b15} & entailed / contradicted & 192 & Experiment 2 \\
\texttt{b16} & entailed / contradicted / undetermined & 192 & Experiment 3 \\
ProofWriter OWA \citep{tafjord2020proofwriter} & three-way & 23{,}240 & certifier validation \\
\bottomrule
\end{tabular}
\end{table}

Responses are scored by direct next-token likelihood over verified single-token
candidates: \texttt{Yes}/\texttt{No} for Experiments 1 and 2,
\texttt{Yes}/\texttt{No}/\texttt{Unknown} for Experiment 3. The model generates
no free text, so nothing is parsed and no verdict is inferred from prose. Every
prompt is four lines --- instruction, theory, solver record, query --- of which
only the solver record varies across arms; the theory is visible in all arms.

\subsection{Models}

Experiments 1 and 2 use the same frozen 3B instruction-tuned checkpoint at
4-bit precision \citep{team2024qwen}, pinned to byte-identical weights, so the
anchors of the first transfer to the second without a weights caveat.
Experiment 3 scores ten instruction-tuned models from $0.5$B to $7.6$B
\citep{team2024qwen,grattafiori2024llama,team2025gemma,microsoft2025phi,team2024olmo,allal2025smollm},
all at bfloat16 so precision is not confounded with model identity. An
eligibility screen confirmed that all ten load, complete a forward pass, and
tokenise all three candidates as single distinct tokens.

\subsection{Sealed protocol}

Panels are hash-stamped before scoring and the runner refuses a modified panel.
Each response is written to a receipt carrying a SHA-256 of its own contents,
and the answer authority is opened only once every receipt exists, so nothing
can be tuned to a result. Audits depend on the standard library alone, so
verification never requires the environment to resolve. In total $12{,}480$
prompts were scored with zero receipt digest failures.

Experiment 3 makes a deliberate protocol change: \emph{no gate blocks the run}.
Where earlier practice excluded a model that failed a delivery screen, delivery
is itself the capability under test here, so a model that cannot emit a verdict
reliably is a finding about substrate viability rather than a reason to drop it.
Tooling failures --- a model that will not load, or whose tokeniser cannot
represent the candidates --- remain exclusions and are not findings; the screen
found none.

\section{Results}

\subsection{Reading the factorial as a \texorpdfstring{$2\times2$}{2x2}}

\Cref{fig:factorial} shows the five arms of Experiment 1 arranged by
\cref{sec:decomposition}. The prespecified primary contrast,
$\textsc{proof\_prefix} - \textsc{conclusion\_only}$, was $-4.7$pp with exact
McNemar $p = 0.078$ and was reported as a null. It is the diagonal.

\begin{figure}[t]
\centering
\includegraphics[width=0.72\textwidth]{figures/answer_state_factorial.png}
\caption{The five arms form a $2\times2$ of answer evidence by proof state, with
the no-material baseline outside it. Each cell gives correct items of 192.
Arrows mark the four one-factor edges; the dashed diagonal is the prespecified
primary, which moves both factors at once and therefore attributes its null to
neither.}
\label{fig:factorial}
\end{figure}

The four edges are reported in \cref{tab:edges}. \textbf{This reading is post
hoc}: it is a different analysis of sealed data, not a re-run, and every value
is re-derived from the 960 raw receipts by a script that reconstructs the answer
key and asserts it reproduces all five published per-arm counts before
reporting. The state main effect is $+22.4$pp and the answer main effect
$+27.1$pp; the answer literal retains only $30\%$ of its value once state is
present.

\begin{table}[t]
\centering
\caption{The four one-factor edges of the $2\times2$, and the prespecified
diagonal. Post hoc reanalysis of sealed data.}
\label{tab:edges}
\begin{tabular}{lrrl}
\toprule
Contrast & Effect & Exact McNemar $p$ & Reported originally \\
\midrule
Add answer, no state present   & $+41.67$pp & $1.7\times10^{-24}$ & no \\
Add state, no answer present   & $+36.98$pp & $1.5\times10^{-19}$ & secondary \\
Add answer, state present      & $+12.50$pp & $1.2\times10^{-7}$  & no \\
Add state, answer present      & $+7.81$pp  & $6.1\times10^{-5}$  & secondary \\
\midrule
\emph{Diagonal (prespecified primary)} & $-4.69$pp & $0.078$ & primary \\
\bottomrule
\end{tabular}
\end{table}

Splitting by class overturns the baseline description. The model answers
\texttt{No} to $88\%$ of items. \Cref{tab:sdt} gives the signal detection
summary: \textsc{irrelevant} returns an identical $9/96$ ``Yes'' rate in both
classes, $d' = 0.00$. A trivial always-\texttt{No} strategy scores $96/192$;
\textsc{none} scored 91 and \textsc{irrelevant} 96, at or below it. The
contradicted class sits at ceiling in every certificate arm and contributed
$0$ of the $21$ discordant pairs in the primary contrast, so the effective
sample was 96, not 192.

\begin{table}[t]
\centering
\caption{Signal detection for Experiment 1. Apparent chance and zero
sensitivity are not the same thing.}
\label{tab:sdt}
\begin{tabular}{lrrrr}
\toprule
Arm & Hits /96 & False alarms /96 & $d'$ & Criterion $c$ \\
\midrule
\textsc{none}            &  9 & 14 & $-0.26$ & $+1.17$ \\
\textsc{irrelevant}      &  9 &  9 & $\mathbf{0.00}$ & $+1.29$ \\
\textsc{conclusion\_only}& 80 &  0 & $+3.52$ & $+0.81$ \\
\textsc{proof\_prefix}   & 71 &  0 & $+3.20$ & $+0.97$ \\
\textsc{full}            & 95 &  0 & $+4.72$ & $+0.20$ \\
\bottomrule
\end{tabular}
\end{table}

\subsection{Validity versus surface overlap}

Experiment 2 holds surface form fixed and destroys validity alone. The primary
contrast, evaluated on the entailed subset ($n = 96$) as declared before the run
because the contradicted class contributes no discordance, is
$\textsc{truncate\_1} - \textsc{broken\_chain} = +60.4$pp, exact McNemar
$p = 6.9\times10^{-18}$, BCa $[+49.0, +68.8]$, with a paired table of $1$ both
correct, $58$ \textsc{truncate\_1}-only, $0$ \textsc{broken\_chain}-only and
$37$ neither. Sensitivity moves with it: $d'$ drops by $+2.446$, satisfying the
same-sign requirement declared in advance, so this is a change in
discrimination and not in criterion placement.

The decomposition is therefore a total state effect of $+61.5$pp comprising a
surface component of $+1.0$pp ($p = 1$) and a validity component of $+60.4$pp:
a \textbf{validity share of $98.3\%$}. \Cref{fig:arms} and \cref{tab:arms} give
the full arm set.

\begin{figure}[t]
\centering
\includegraphics[width=\textwidth]{figures/arm_decomposition.png}
\caption{Ten matched arms on one item set, differing only in the solver record.
Left: correct on the entailed subset (of 96). Right: sensitivity $d'$, signed.
Destroying validity alone removes almost the whole effect. The
\textsc{misleading} arm, whose fabricated final rule points the wrong way, is
followed to the wrong answer on 189 of 192 items.}
\label{fig:arms}
\end{figure}

\begin{table}[t]
\centering
\caption{Experiment 2, all ten arms. Five arms return identical results,
including \textsc{same\_entity\_irrelevant}, which names the query entity four
times.}
\label{tab:arms}
\begin{tabular}{lrrr}
\toprule
Arm & All /192 & Entailed /96 & $d'$ \\
\midrule
\textsc{none}                    &  96 &  0 & $0.000$ \\
\textsc{irrelevant}              &  96 &  0 & $0.000$ \\
\textsc{same\_entity\_irrelevant}&  96 &  0 & $0.000$ \\
\textsc{truncate\_3}             &  96 &  0 & $0.000$ \\
\textsc{truncate\_2}             &  96 &  0 & $0.000$ \\
\textsc{truncate\_1}             & 155 & 59 & $2.853$ \\
\textsc{broken\_chain}           &  97 &  1 & $0.407$ \\
\textsc{shuffled}                & 110 & 14 & $1.527$ \\
\textsc{misleading}              &   3 &  0 & $-4.363$ \\
\textsc{full}                    & 192 & 96 & $5.131$ \\
\bottomrule
\end{tabular}
\end{table}

Three supporting contrasts sharpen the reading. Entity repetition explains
nothing: $\textsc{same\_entity\_irrelevant} - \textsc{irrelevant} = +0.0$pp
($p = 1$), despite the former naming the query subject four times and the latter
not at all. Order matters: $\textsc{truncate\_1} - \textsc{shuffled} = +46.9$pp
($p = 6.8\times10^{-13}$), so the model is not reading a bag of statements.
And depth is a cliff, not a slope:
$\textsc{truncate\_2} - \textsc{truncate\_1} = -61.5$pp
($p = 3.5\times10^{-18}$), with \textsc{truncate\_2} scoring identically to
supplying no certificate at all. Five arms are indistinguishable ---
$96/192$, $0/96$ entailed, $d' = 0.000$, $c = 2.565$ --- so behaviour is binary:
either the supplied chain reaches one step from the answer, or the model is
blind to it.

\subsection{Following a corrupted apparatus}

The \textsc{misleading} arm supplies a chain identical to \textsc{full} except
that its final rule, which is fabricated and absent from the theory, flips
polarity. The ground-truth answer is unchanged. The model scores $3$ of $192$,
with $d' = -4.363$: $\textsc{misleading} - \textsc{full} = -100.0$pp
($p = 2.5\times10^{-29}$).

The model therefore follows a valid-looking certificate that points the wrong
way on 189 of 192 items. Read against the $98.3\%$ validity share, the two
results are not in tension but jointly informative: the model demonstrably
tracks whether a supplied derivation connects, and that tracking provides no
defence whatever when the derivation connects to the wrong conclusion. Validity
tracking is not verification.

\subsection{Which models can serve as the interface}

Experiment 3 scores ten models on the three-class panel. We declared in advance
that a model relays non-determination if it reaches $\geq 80\%$ recall on
undetermined items with full solver material. \textbf{Eight of ten passed, and
the criterion was invalid.} It measures recall on a single class, which a model
answering \texttt{Unknown} to everything maximises while discriminating nothing
--- and four models do exactly that, emitting \texttt{Unknown} on $62$--$96\%$
of all items, three of them never emitting \texttt{No} at all. This is the
same failure the $d' = 0.00$ arm exhibits in Experiment 1, mirrored onto a
different label.

We replace it \textbf{post hoc} with a floor on every class: a model is a viable
substrate if its minimum per-class recall is at least $0.50$. Collapse cannot
game this. Both verdicts are retained in the released results;
the superseded one is not deleted. \Cref{tab:models} and \cref{fig:size} report
the outcome.

\begin{figure}[t]
\centering
\includegraphics[width=0.8\textwidth]{figures/substrate_size_curve.png}
\caption{Balanced accuracy for ten models with no solver material (open marker)
and with full material (filled), ordered by parameter count. Chance is $33.3\%$.
Colour gives the corrected viability verdict. Three of ten are viable; below
1.7B the interface collapses to a single label whatever the solver supplies.}
\label{fig:size}
\end{figure}

\begin{table}[t]
\centering
\caption{Experiment 3. Balanced accuracy (\%), chance $=33.3$. The prespecified
criterion passed eight of ten; the corrected criterion passes three.}
\label{tab:models}
\begin{tabular}{lrrrrrl}
\toprule
Model & Params (B) & \textsc{none} & \textsc{full} & Min recall & Max label share & Verdict \\
\midrule
Qwen2.5-0.5B  & 0.5 & 35.4 & 63.5 & 0.0  & 61.5 & collapsed \\
OLMo-2-1B     & 1.0 & 35.9 & 42.2 & 0.0  & 91.1 & collapsed \\
Llama-3.2-1B  & 1.2 & 33.9 & 37.0 & 0.0  & 95.3 & collapsed \\
Qwen2.5-1.5B  & 1.5 & 33.3 & 37.0 & 0.0  & 96.4 & collapsed \\
SmolLM2-1.7B  & 1.7 & 33.3 & 69.3 & 37.5 & 44.8 & below floor \\
Qwen2.5-3B    & 3.0 & 41.1 & \textbf{90.6} & 71.9 & 42.7 & \textbf{viable} \\
Llama-3.2-3B  & 3.2 & 45.8 & 80.7 & 42.2 & 49.5 & below floor \\
Phi-4-mini    & 3.8 & 44.8 & \textbf{90.6} & 71.9 & 42.7 & \textbf{viable} \\
Gemma-3-4B    & 4.3 & 63.5 & \textbf{96.4} & 89.1 & 36.5 & \textbf{viable} \\
Qwen2.5-7B    & 7.6 & 33.3 & 71.4 & 14.1 & 62.0 & collapsed \\
\bottomrule
\end{tabular}
\end{table}

Three findings follow. Supplying full solver material takes viable models from
at or near chance to $90$--$96\%$ balanced accuracy on a task that includes
abstention, so the architecture works above a floor. That floor is near 3B:
below 1.7B, models collapse to a single label whatever the solver supplies, and
an apparatus cannot help an interface that cannot express three outcomes. And
the effect is not monotonic in scale --- the 7.6B model collapses ($62.0\%$
\texttt{Unknown}, minimum per-class recall $14.1$) while a 3B model does not.
Model is not a randomised factor here, so these comparisons are descriptive and
we make no significance claim about scale.

\section{Limitations}

\subsection{Scope of the mechanism claim}

The inference we measure is \emph{exactly one step deep}. \textsc{truncate\_2}
scores identically to supplying no certificate, so ``validity tracking'' should
be read as: the model can complete a final inference when both premises are
present and adjacent, and can detect when the chain that would license it is
broken. It cannot chain two steps. That is a hard bound on how this result may
be described.

The full theory is visible in every arm, so the query remains derivable from the
theory regardless of what the certificate says. Breaking a certificate is
diagnostic only because the model scores $0/96$ working from the theory alone. A
model that used a broken certificate as a pointer back into the theory would be
performing inference of a different kind; our design does not exclude that
reading, and we record it as an interpretation caveat rather than a controlled
alternative.

\textsc{truncate\_2} and \textsc{truncate\_3} necessarily drop the query
predicate out of the certificate, since it lives in the final rule. The depth
ladder therefore confounds depth with predicate presence and must be read
against \textsc{same\_entity\_irrelevant}, which holds entity repetition high
while removing the predicate.

\subsection{Post hoc analyses and superseded criteria}

Two analyses in this paper are post hoc and are labelled where they are used.
The $2\times2$ reading of Experiment 1 is a different analysis of sealed data,
not a re-run. The viability criterion of Experiment 3 replaced a prespecified
threshold that the data showed to be invalid; the original is retained in the
released results.

Experiment 1 also carries design errors we report rather than repair. It
prespecified a $15$pp primary effect while its comparison arm reached $91.7\%$,
leaving $8.3$pp of headroom, so the target was arithmetically unreachable. It
recorded no proof depth and so cannot stratify its failures. And its task
identifiers encoded the semantic class, so its answer authority was
reconstructible from the public panel --- convenient for our reanalysis, but not
a sealed authority. Experiments 2 and 3 fix all three.

\subsection{Generalisation}

This is one task family, small models only, and synthetic panels; the mechanism
result rests on a single model, and the ten-model sweep addresses substrate
viability rather than mechanism. Nonce vocabularies establish item novelty, not
independence from all relevant pretraining patterns
\citep{golchin2023time,deng2024investigating}.

An undetermined \textsc{proof\_prefix} cannot contain the query predicate,
because the solver has nothing to say about it, whereas entailed and
contradicted prefixes can. Undetermined items therefore offer fewer surface
cues, and a surface-matching model will look worse on them for reasons unrelated
to abstention; per-arm entity-mention counts are recorded so this is analysable
rather than discovered later.

Finally, every theory here arrives \emph{already formalised}. Nothing in this
paper tests whether a model can take a framework described in prose and produce
the solver's input, which is the step on which any claim of working in an
unfamiliar framework depends. \Cref{sec:closure} and the corruption result make
that gap consequential rather than merely open: a formalisation error would not
be caught downstream, but followed.

\section{Conclusion}

Solver assistance improves a small model's accuracy on rule-chaining queries,
and the improvement is not text matching. Holding line count, line types,
entity occurrence count, predicate presence and token length fixed and
destroying validity alone removes $98.3\%$ of the state effect. Entity
repetition, the most plausible surface confound, contributes nothing measurable.

Two qualifications travel with that result and should not be separated from it.
The inference is one step deep, so this is a narrow competence and not a general
reasoning claim. And it provides no protection against a wrong apparatus: the
same model that detects a broken chain follows a fabricated one to the wrong
answer on 189 of 192 items. For architectures that externalise reasoning to a
verified component and use the model as the interface, that asymmetry is the
operationally important finding --- validity tracking is not verification, and a
system built on it inherits the apparatus's errors in full.

The measurement lessons generalise beyond this task. Twice in this programme a
number that looked like competence was a degenerate responder: an arm at
$50.0\%$ accuracy with $d' = 0.00$, and a prespecified criterion that a model
answering \texttt{Unknown} to everything maximised. Both were caught only by
reporting sensitivity alongside accuracy. We recommend the practice for any
evaluation of tool-augmented systems, together with the answer-evidence
decomposition, which requires no new data collection --- only that the arms be
arranged so that each contrast moves one factor at a time.

\section*{Reproducibility Statement}

\textbf{Code and data.} The supplementary material accompanying this submission
is self-contained: sealed panels and answer authorities, all $12{,}480$
per-response receipts, the generators, runners, audits and analysis scripts, and
the forward-closure certifier with its validation harness. Every number in this
paper can be re-derived from a fresh unpack with no network access, no model
weights and no external packages --- the audits use the Python standard library
only, so verification does not depend on resolving an environment. A permanent
archive with a DOI will accompany the camera-ready version.

All panels, answer authorities, per-response receipts, audit scripts and
analysis scripts are released. Every number in this paper is re-derivable from
the receipts without loading a model: the audits use the standard library only,
so verification does not depend on resolving an environment. Panels are
hash-stamped and the runners refuse a modified panel; each receipt carries a
SHA-256 of its own contents, and all $12{,}480$ verified with zero failures.
Model weights are not redistributed, but each run records the pinned revision
and a hash of the weight files before those files are deleted. The
forward-closure certifier and its validation against the public corpus are
included.

\section*{AI-Use Statement}

A large language model was used as a coding and drafting assistant throughout:
generating experiment code, analysis scripts and figure code, and drafting this
manuscript. All experimental design decisions, the interpretation of results,
and the claim boundaries were made and verified by the authors. Every numeric
value reported was produced by the released analysis scripts from sealed
receipts, not written by a model; the released audits allow any reader to
re-derive them independently.
"""

# --- preamble: apply tex_profile flags -------------------------------------
src = src.replace(r"\usepackage{xcolor}",
                  "\\usepackage{xcolor}\n\\usepackage{microtype}\n"
                  "\\usepackage{nicefrac}\n\\usepackage{cleveref}")
src = src.replace("\\title{TITLE}", "\\title{" + TITLE + "}")
src = src.replace("ABSTRACT", ABSTRACT)

# --- replace the empty section stubs with the body -------------------------
stub = re.compile(r"\\section\{Method\}.*?(?=\\bibliographystyle)", re.S)
assert stub.search(src), "section stubs not found"
src = stub.sub(lambda _m: BODY.strip() + "\n\n", src)   # lambda: LaTeX backslashes are not regex templates

src = apply_layout(src)

out = PAPER / "drafts/paper.tex"
out.write_text(src)
print(f"paper.tex written: {len(src)} chars, {src.count(chr(10))} lines")
for s in ("Introduction", "Related Work", "Method", "Experimental Setup", "Results",
          "Limitations", "Conclusion", "Reproducibility Statement", "AI-Use Statement"):
    print(f"  {'OK ' if ('section{'+s+'}' in src or 'section*{'+s+'}' in src) else 'MISSING'} {s}")
