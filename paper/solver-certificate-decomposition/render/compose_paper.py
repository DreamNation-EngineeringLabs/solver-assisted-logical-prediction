#!/usr/bin/env python3
"""Step 4 — compose paper.tex from intro_relwork.tex plus the remaining sections.

Preamble, Introduction and Related Work are preserved verbatim from Step 3.
Every numeric value below traces to inputs/experimental_log.md. LaTeX patterns
follow papers/solver-certificate-decomposition/tex_profile.json (cleveref, nicefrac, microtype, T1 all True).
"""
import pathlib, re

PAPER = pathlib.Path(__file__).resolve().parents[1]


def float_block(src: str, label: str, env: str) -> tuple[int, int] | None:
    """Character span of the ``env`` float carrying ``label``.

    Scans outward from the label to the nearest enclosing \\begin/\\end rather
    than matching a regex across the document: a ``.*?`` with ``re.S`` starts at
    the *first* float in the file and swallows every one up to this label --- the
    defect that corrupted this script once already.
    """
    anchor = src.find("\\label{" + label + "}")
    if anchor < 0:
        return None
    start = src.rfind("\\begin{" + env, 0, anchor)
    end = src.find("\\end{" + env, anchor)
    if start < 0 or end < 0:
        return None
    end = src.index("}", end) + 1
    block = src[start:end]
    assert block.count("\\begin{" + env) == 1, f"{label}: float block is not self-contained"
    return start, end


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
                      "\\setlength{\\parskip}{2pt}\n\\sloppy\n\\emergencystretch=2em\n"
                      # twelve floats at the class defaults cost roughly half a
                      # page of white band around captions and float boundaries.
                      "\\setlength{\\abovecaptionskip}{4pt}\n"
                      "\\setlength{\\belowcaptionskip}{0pt}\n"
                      "\\setlength{\\textfloatsep}{10pt plus 2pt minus 2pt}\n"
                      "\\setlength{\\dbltextfloatsep}{10pt plus 2pt minus 2pt}\n"
                      "\\setlength{\\floatsep}{8pt plus 2pt minus 2pt}\n"
                      "\\setlength{\\dblfloatsep}{8pt plus 2pt minus 2pt}\n"
                      "\\setlength{\\intextsep}{8pt plus 2pt minus 2pt}", 1)
    src = src.replace("\\usepackage{xcolor}",
                      "\\usepackage{xcolor}\n\\usepackage{microtype}\n"
                      "\\usepackage{nicefrac}\n\\usepackage{url}\n\\usepackage{cleveref}", 1)
    # tables compact
    src = src.replace("\\begin{table}[t]\n\\centering\n\\caption",
                      "\\begin{table}[t]\n\\centering\\small\n\\caption")
    # the two widest objects span both columns
    # Every table here is wider than a 3.2in column, and fig:arms needs the
    # full measure. Promote them by name, so adding a float cannot silently
    # change the placement of another one.
    SPANNING = tuple((lab, "table") for lab in (
        "tab:panels", "tab:edges", "tab:sdt", "tab:arms", "tab:replication",
        "tab:detection", "tab:models")) + (("fig:arms", "figure"),)
    for label, env in SPANNING:
        span = float_block(src, label, env)
        if span is None:
            continue
        start, end = span
        block = src[start:end]
        src = src[:start] + block.replace("\\begin{" + env + "}[t]", "\\begin{" + env + "*}[t]", 1) \
                                 .replace("\\end{" + env + "}", "\\end{" + env + "*}", 1) + src[end:]
    # figure widths for a narrow column
    src = src.replace("width=0.72\\textwidth]{figures/answer_state_factorial",
                      "width=\\columnwidth]{figures/answer_state_factorial")
    src = src.replace("width=\\textwidth]{figures/arm_decomposition",
                      "width=0.86\\textwidth]{figures/arm_decomposition")
    src = src.replace("width=0.8\\textwidth]{figures/substrate_size_curve",
                      "width=\\columnwidth]{figures/substrate_size_curve")
    # --- supporting floats to an appendix -----------------------------------
    # The venue caps main text at 9 pages; references and appendix are exempt.
    # These six are supporting: four figures whose numbers already appear in a
    # main-text table, the dataset inventory, and the SDT breakdown whose
    # headline values are quoted in prose.
    APPENDIX = (("tab:panels", "table"), ("tab:sdt", "table"),
                ("tab:replication", "table"), ("fig:arms", "figure"),
                ("fig:replication", "figure"), ("fig:detection", "figure"),
                ("fig:size", "figure"))
    moved = []
    for label, env in APPENDIX:
        span = float_block(src, label, env)
        assert span is not None, f"{label}: not found for the appendix move"
        start, end = span
        moved.append(src[start:end])
        src = src[:start].rstrip("\n") + "\n\n" + src[end:].lstrip("\n")
    tail = ("\n\\appendix\n\\section{Supporting Tables and Figures}\n\n"
            + "\n\n".join(moved) + "\n\n")
    src = src.replace("\\end{document}", tail + "\\end{document}", 1)

    return src



src = (PAPER / "drafts/intro_relwork.tex").read_text()

TITLE = ("What a Language Model Does with a Solver Certificate:\\\\\n"
         "An Answer-Evidence Decomposition Across Ten Models")

ABSTRACT = r"""
Solver-, tool- and retrieval-augmented language model systems report large
accuracy gains, and those gains are routinely read as evidence that the model
used the supplied material. Two mechanisms produce the same number: the model
reading a supplied answer, and the model reasoning over supplied state. The
standard control, a same-shape irrelevant record, separates neither. We build a
control that does --- holding line count, line types, query-entity occurrence
count, query-predicate presence and token length fixed while destroying validity
alone --- and apply it across four sealed experiments, twelve model-runs and
$18{,}816$ scored prompts, all re-derivable from released receipts.

Three results. First, the decomposition works and is worth adopting: reading a
five-arm factorial as a $2\times2$ of answer evidence by proof state recovers a
state main effect its prespecified diagonal contrast could not attribute, and
the same $2\times2$ computed across ten models shows the answer channel
dominating the state channel in $8$ of $10$. Second, how much of the state
effect is genuine inference is \emph{model-specific}: the validity share is
$98.3\%$ (95\% BCa $[94.4, 100.0]$) on one checkpoint and $40.4\%$ on another
that exploits surface overlap heavily, so a single-model mechanism result should
not be generalised --- including ours. Third, the finding that does replicate
everywhere is a negative one: given a valid-looking certificate whose fabricated
final rule establishes the negation, models follow it on $189/192$, $186/192$ and
$192/192$ items. A three-candidate test refutes the reading that the model
detects invalidity at all --- supplying a broken chain \emph{lowers} the
abstention rate, from $75.0\%$ to $42.2\%$.

We also report what the design cannot support: the $2\times2$ is ceiling-limited,
viability is a property of (model $\times$ arm) rather than of a model, and
supplying proof state actively degrades three of ten interfaces. Two prespecified
criteria of our own were invalidated by our own data and are reported as such.
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
splits of a public corpus \citep{tafjord2020proofwriter} at depths $0$, $1$, $2$,
$3$ and $5$: $23{,}240$ of $23{,}240$ questions agree, $100.00\%$, with perfectly
diagonal confusion, including $10{,}440$ undetermined items.

That check is weaker than a perfect score suggests, and we state its limits.
Those labels are themselves produced by forward chaining over the same fragment,
so the agreement partly measures one chainer agreeing with another. It would
catch a coding bug; it does not probe adversarial structure, and it gives no
coverage of the generated nonce theories where the certifier is actually used.

We therefore add two checks with different failure modes. Nine adversarial
theories: cyclic rules; a cycle that never reaches the query; a chain longer than
the round cap; derived negation; absent predicates and absent entities; a rule
that must fire only for the satisfying entity; a theory deriving an atom and its
negation, which must be \emph{rejected} rather than labelled; and a cap overrun,
which must report failure rather than a wrong answer. All nine pass. And a
\emph{differential} test on the generated panels against an independently written
reference implementation --- exhaustive ground instantiation over the Herbrand
base with a naive fixpoint, a deliberately different algorithm --- which agrees
with the certifier and the sealed authority on $192/192$ and $192/192$ items. That
reference encodes the same intended semantics, so it catches implementation error
rather than a misconception about the semantics; we claim the former only. No item
enters a sealed panel without a certification record.

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
$+27.1$pp.

The \textbf{interaction is $-29.2$pp}, larger in magnitude than either main
effect, and the design is \textbf{ceiling-limited}: \textsc{full} at $191/192$
($99.5\%$) leaves only $13.0$pp of headroom above \textsc{proof\_prefix}, so both
``other factor present'' edges are compressed and the averaged main effects are
correspondingly deflated. It follows that the ratio $12.50/41.67$ --- the answer
literal apparently retaining $30\%$ of its value once state is present --- is
substantially a measurement of remaining headroom rather than of channel
redundancy, and we do not draw a redundancy conclusion from it. A design with
\textsc{full} away from ceiling would be required to separate the two.

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
surface component of $+1.0$pp ($p = 1$, 95\% BCa $[+0.0, +3.1]$pp) and a validity
component of $+60.4$pp: a \textbf{validity share of $98.3\%$, 95\% BCa
$[94.4, 100.0]$}. The interval bootstraps the whole ratio over paired item
resamples rather than its numerator alone. \Cref{fig:arms} and \cref{tab:arms}
give the full arm set. \Cref{sec:replication} shows this share is specific to
this checkpoint and does not generalise.

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
($p = 6.8\times10^{-13}$, Holm $1.4\times10^{-12}$), so the model is not reading
a bag of statements. And depth is a cliff, not a slope:
$\textsc{truncate\_2} - \textsc{truncate\_1} = -61.5$pp
($p = 3.5\times10^{-18}$, Holm $1.0\times10^{-17}$), with \textsc{truncate\_2}
scoring identically to supplying no certificate at all. Holm adjustment is within
the secondary family declared in \cref{sec:measurement}; the four post hoc edges
of \cref{tab:edges} carry Holm values $6.6\times10^{-24}$, $4.5\times10^{-19}$,
$2.4\times10^{-7}$ and $6.1\times10^{-5}$. Five arms are indistinguishable ---
$96/192$, $0/96$ entailed, $d' = 0.000$, $c = 2.565$ --- so behaviour is binary:
either the supplied chain reaches one step from the answer, or the model is
blind to it.

\subsection{The validity share does not generalise}
\label{sec:replication}

The decomposition of \cref{sec:broken} was run on two further checkpoints: the
same model at bfloat16 rather than 4-bit, which isolates quantisation from model
identity, and a different family. \Cref{tab:replication} and \cref{fig:replication} report all three.

\begin{table}[t]
\centering
\caption{The same ten-arm decomposition on three checkpoints, entailed subset
($n = 96$). The validity share ranges from $40.4\%$ to $98.6\%$.}
\label{tab:replication}
\begin{tabular}{lrrrrrr}
\toprule
Checkpoint & \textsc{brk} & \textsc{tr\_1} & Total & Surface & Validity & Share \\
\midrule
Qwen2.5-3B 4-bit &  1 & 59 & $+61.5$ & $+1.0$  & $+60.4$ & $98.3\%$ \\
Qwen2.5-3B bf16  &  1 & 72 & $+75.0$ & $+1.0$  & $+74.0$ & $98.6\%$ \\
Gemma-3-4B       & \textbf{58} & 96 & $+97.9$ & $\mathbf{+58.3}$ & $+39.6$ & $\mathbf{40.4\%}$ \\
\bottomrule
\end{tabular}
\end{table}

\begin{figure}[t]
\centering
\includegraphics[width=\columnwidth]{figures/validity_share_replication.png}
\caption{The surface and validity components on three checkpoints. Gemma-3-4B's
surface component is $+58.3$pp against $+1.0$pp for the two Qwen checkpoints, and
its validity share is $40.4\%$ against $98.3\%$ and $98.6\%$.}
\label{fig:replication}
\end{figure}

Quantisation is the smaller effect. bfloat16 raises \textsc{truncate\_1} from 59
to 72 of 96 but leaves the share essentially unchanged ($98.6\%$ against
$98.3\%$), so precision moves the magnitude of the state effect without moving
its composition.

Model identity does not behave that way. Gemma-3-4B answers \textsc{broken\_chain}
correctly on \textbf{58 of 96} items where the other two checkpoints manage 1, so
its surface component is $+58.3$pp and its validity share $40.4\%$. The same
control that isolates inference on one checkpoint reveals substantial
surface exploitation on another.

\textbf{We therefore do not claim that solver-supplied state is used as inference
in general.} On the checkpoint of \cref{sec:broken} it overwhelmingly is; on the
strongest substrate in our sweep, most of the effect is surface overlap. What
generalises is the \emph{method} --- the control separates the two wherever it is
applied --- not the value it returns.

One result does replicate without exception, and it is the negative one. The
\textsc{misleading} arm scores $3$, $6$ and $0$ of $192$ across the three
checkpoints, with $d'$ of $-4.36$, $-4.06$ and $-5.13$. The model that exploits
surface overlap most is also the one most completely misled.

\subsection{Following a corrupted apparatus}
\label{sec:corruption}

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

\subsection{The model does not detect invalidity}
\label{sec:detection}

A natural reading of \cref{sec:broken} is that the model detects a broken chain.
The binary design cannot support that reading, because the correct answer under a
broken certificate \emph{is} the model's default label: ``detected the break'' and
``found no pattern to complete'' predict the same response.

We separated them. The \textsc{broken\_chain} items, whose displayed lines are
certified undetermined, were rescored with three candidates rather than two ---
theories, certificates and queries byte-identical, only the instruction line and
candidate set changed. A validity tracker should answer \texttt{Unknown}; a
pattern completer should answer its default. \Cref{tab:detection} and \cref{fig:detection}
report the outcome.

\begin{table}[t]
\centering
\caption{Three-candidate rescoring of the same items. Supplying a broken chain
\emph{lowers} the abstention rate.}
\label{tab:detection}
\begin{tabular}{lrrrr}
\toprule
Arm & \texttt{Yes} & \texttt{No} & \texttt{Unknown} & Unknown rate \\
\midrule
\textsc{irrelevant} (baseline) &  0 &  48 & 144 & $75.0\%$ \\
\textsc{broken\_chain}         &  1 & 110 &  81 & $42.2\%$ \\
\textsc{truncate\_1}           & 61 & 110 &  21 & $10.9\%$ \\
\bottomrule
\end{tabular}
\end{table}

\begin{figure}[t]
\centering
\includegraphics[width=\columnwidth]{figures/detection_response_distribution.png}
\caption{Three-candidate response distribution. Supplying a broken chain lowers
the abstention rate from the $75.0\%$ baseline to $42.2\%$ --- the opposite of the
direction validity detection predicts.}
\label{fig:detection}
\end{figure}

The abstention rate under \textsc{broken\_chain} is $42.2\%$ against a $75.0\%$
baseline --- $-32.8$pp, the opposite of the direction detection predicts. And
\texttt{No} is $110$ of $192$ under \textbf{both} \textsc{broken\_chain} and
\textsc{truncate\_1}; the arms differ only in \texttt{Yes} ($1$ against $61$).

\textbf{Detection is refuted, not merely unsupported.} What the data support is
narrower: the model completes a final inference when both premises are present
and adjacent, and does not when they are not. Its failure on
\textsc{broken\_chain} is a failure to complete, not a detection of invalidity.
This is consistent with \cref{sec:corruption}: a model that verified validity
would reject a certificate whose final rule is fabricated and absent from the
theory, and it does not.

\subsection{Which models can serve as the interface}

Experiment 3 scores ten models on the three-class panel in all five arms. We
declared in advance that a model relays non-determination if it reaches
$\geq 80\%$ recall on undetermined items with full solver material. \textbf{Eight
of ten passed, and the criterion was invalid.} It measures recall on a single
class, which a model answering \texttt{Unknown} to everything maximises while
discriminating nothing --- and four models do exactly that, emitting
\texttt{Unknown} on $62$--$96\%$ of items, three never emitting \texttt{No}. This
is the failure of \cref{tab:sdt} mirrored onto a different label.

We replace it \textbf{post hoc} with a floor on every class: minimum per-class
recall at least $0.50$. Both verdicts are retained in the released results.
\Cref{tab:models} reports all five arms for all ten models.

\begin{table}[t]
\centering
\caption{All five arms, all ten models. Balanced accuracy (\%), chance $=33.3$.
Viability is reported per arm, because it is not a property of the model.}
\label{tab:models}
\begin{tabular}{lrrrrrrl}
\toprule
Model & B & \textsc{none} & \textsc{irrel} & \textsc{concl} & \textsc{prefix} & \textsc{full} & Viable in \\
\midrule
Qwen2.5-0.5B & 0.5 & 35.4 & 34.9 & 41.1 & 43.2 & 63.5 & --- \\
OLMo-2-1B    & 1.0 & 35.9 & 33.3 & 53.6 & 34.9 & 42.2 & --- \\
Llama-3.2-1B & 1.2 & 33.9 & 33.9 & 57.8 & 36.5 & 37.0 & --- \\
Qwen2.5-1.5B & 1.5 & 33.3 & 33.3 & 43.2 & 34.9 & 37.0 & --- \\
SmolLM2-1.7B & 1.7 & 33.3 & 33.3 & 45.3 & 39.6 & 69.3 & --- \\
Qwen2.5-3B   & 3.0 & 41.1 & 39.1 & \textbf{96.4} & 74.0 & 90.6 & concl, prefix, full \\
Llama-3.2-3B & 3.2 & 45.8 & 43.2 & 67.2 & 55.2 & 80.7 & --- \\
Phi-4-mini   & 3.8 & 44.8 & 39.6 & 68.2 & 71.9 & 90.6 & full \\
Gemma-3-4B   & 4.3 & 63.5 & 51.0 & \textbf{100.0} & 84.4 & 96.4 & concl, prefix, full \\
Qwen2.5-7B   & 7.6 & 33.3 & 33.3 & \textbf{97.9} & 67.2 & 71.4 & \textbf{concl only} \\
\bottomrule
\end{tabular}
\end{table}

\textbf{Viability is a property of (model $\times$ arm), not of a model.} The
decisive row is Qwen2.5-7B. Under \textsc{full} it has minimum per-class recall
$0.141$ and emits \texttt{Unknown} on $62.0\%$ of items. Under
\textsc{conclusion\_only} the same model reaches $97.9\%$ balanced accuracy with
minimum per-class recall $0.938$ --- it clears the floor comfortably and is the
second-best model in the sweep. Its contradicted-class recall falls from $0.938$
to $0.141$ \emph{when the proof state is supplied}.

So Qwen2.5-7B is not an interface that cannot express three outcomes. It is an
interface that the proof state breaks. \textbf{Supplying proof state degrades
three of ten models} --- Gemma-3-4B, Qwen2.5-3B and Qwen2.5-7B --- measured as the
drop in minimum per-class recall from \textsc{conclusion\_only} to \textsc{full},
and two of those three are otherwise among the strongest substrates.

This bounds a claim we would otherwise have made. There is a floor near 3B
\emph{for tolerating full certificates}: below 1.7B no arm clears it. But that is
not a floor for serving as an interface, and the effect is not monotonic in
scale. Model is not a randomised factor here, so these comparisons are
descriptive and we make no significance claim about scale.

\begin{figure*}[t]
\centering
\includegraphics[width=0.92\textwidth]{figures/substrate_size_curve.png}
\caption{All five arms for all ten models, ordered by parameter count. Chance is
$33.3\%$. Bar colour gives the per-arm viability verdict. Qwen2.5-7B is viable
under \textsc{conclusion\_only} and not under \textsc{full}: viability is a
property of (model $\times$ arm).}
\label{fig:size}
\end{figure*}

\subsection{The same \texorpdfstring{$2\times2$}{2x2} across ten models}
\label{sec:tenmodel}

Experiment 3's five arms are the $2\times2$ of \cref{sec:decomposition} plus a
baseline, on ten models. Computing it costs nothing further and turns a
single-checkpoint decomposition into a ten-model one (\cref{sec:tenmodel} is
computed from the same receipts as \cref{tab:models}).

The mean state main effect is $+8.7$pp and the mean answer main effect $+21.6$pp,
with a mean interaction of $-15.9$pp. \textsc{conclusion\_only} exceeds
\textsc{proof\_prefix} in \textbf{8 of 10} models and equals or exceeds
\textsc{full} in $6$ of $10$.

Two things follow, both visible in \cref{tab:models} and \cref{fig:size}. The answer channel
dominates the state channel across the model set, which is a more general form of the pattern
\cref{tab:edges} shows on one model. And Experiment 1's state main effect of
$+22.4$pp is not typical: the ten-model mean is less than half of it. A
single-model estimate of how much the state channel contributes should not be
read as characteristic, ours included.

\section{Limitations}

\subsection{Scope of the mechanism claim}

The inference we measure is \emph{exactly one step deep}. \textsc{truncate\_2}
scores identically to supplying no certificate, so ``validity tracking'' should
be read narrowly: the model completes a final inference when both premises are
present and adjacent, and does not when they are not. It cannot chain two steps.
It also does not \emph{detect} invalidity --- \cref{sec:detection} tests that
directly and refutes it. That is a hard bound on how this result may be
described, and \cref{sec:replication} bounds it further: the share attributable
to inference ranges from $40.4\%$ to $98.6\%$ across three checkpoints.

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

This is one task family, small models only, and synthetic panels. Nonce
vocabularies establish item novelty, not independence from all relevant
pretraining patterns \citep{golchin2023time,deng2024investigating}.

\textbf{Quantisation.} Experiments 1 and 2 use a 4-bit checkpoint and
Experiment 3 bfloat16, so the mechanism result and the substrate sweep describe
different artefacts of the same model. 4-bit quantisation moves next-token
margins and criterion placement, which is precisely what we measure.
\Cref{sec:replication} quantifies it: bfloat16 raises \textsc{truncate\_1} from
59 to 72 of 96 while leaving the validity share essentially unchanged, so
precision affects magnitude more than composition. We nonetheless do not treat
the two as one artefact.

\textbf{Prior report.} Experiment 1's per-arm counts and prespecified primary
contrast appeared in an earlier unpublished report by the same authors, cited
here anonymously; the $2\times2$ reading, the response-bias finding and all of
Experiments 2, 3 and 4 are new. That report concluded the 3B checkpoint failed an
open-world unknown gate, whereas Experiment 3 finds the same family viable on the
three-class panel. Panels, candidate sets and quantisation all differ, which
plausibly accounts for the discrepancy, but we flag it rather than leave it to a
reader who finds both.

An undetermined \textsc{proof\_prefix} cannot contain the query predicate ---
the solver has nothing to say about it --- whereas entailed and contradicted
prefixes can. Undetermined items therefore offer fewer surface cues, and a
surface-matching model will look worse on them for reasons unrelated to
abstention; per-arm entity-mention counts are recorded so this is analysable.

Finally, every theory here arrives \emph{already formalised}. Nothing here tests
whether a model can turn a framework described in prose into the solver's input,
the step on which any claim of working in an unfamiliar framework depends.
\Cref{sec:closure} and the corruption result make that gap consequential rather
than merely open: a formalisation error would not be caught downstream, but
followed.

\section{Conclusion}

Solver assistance improves a small model's accuracy on rule-chaining queries, and
end-to-end accuracy cannot say why. The decomposition we propose can: arrange the
arms so that each contrast moves one factor, and hold every surface property
fixed while destroying validity alone. It needs no new data collection, only that
the arms be laid out correctly.

What it returns is model-specific. On one checkpoint $98.3\%$ of the state effect
survives the surface-matched control; on the strongest substrate in our sweep,
$40.4\%$ does. Across ten models the answer channel dominates the state channel
in $8$ of $10$, and the mean state main effect is less than half the single-model
estimate. We therefore offer the method as the contribution and decline to
generalise its value --- including our own.

Two findings do hold on every checkpoint. The inference is one step deep, and it
is not detection: rescoring the broken-chain items with a third candidate
\emph{lowers} the abstention rate, so the model completes when it can and falls
back when it cannot. And the architecture has no defence against a wrong
apparatus --- given a valid-looking certificate whose fabricated final rule
establishes the negation, the three checkpoints answer incorrectly on $189$,
$186$ and $192$ of $192$ items, the surface-exploiting model most completely of
all. Where reasoning is externalised to a verified component and the model is the
interface, that is the operationally important result: the interface inherits the
apparatus's errors in full, and more proof state degrades three of the ten
interfaces we measured rather than helping them.

Two prespecified criteria failed on us. An arm at $50.0\%$ accuracy with
$d' = 0.00$ was a degenerate responder, not a chance-level one, and a viability
threshold declared in advance was maximised by a model answering \texttt{Unknown}
to everything. Reporting sensitivity alongside accuracy caught both; we report
them rather than repair them, and recommend the practice --- and the
decomposition --- to anyone whose tool-augmented system returns a large headline
number.

\section*{Reproducibility Statement}

\textbf{Code and data.} The supplementary material accompanying this submission
is self-contained: sealed panels and answer authorities, all $12{,}480$
per-response receipts, the generators, runners, audits and analysis scripts, and
the forward-closure certifier with its validation against the public corpus.
Every number in this paper can be re-derived from a fresh unpack with no network
access, no model weights and no external packages --- the audits use the Python
standard library only, so verification does not depend on resolving an
environment. Panels are hash-stamped and the runners refuse a modified panel;
each receipt carries a SHA-256 of its own contents, and all $12{,}480$ verified
with zero failures. Model weights are not redistributed, but each run records the
pinned revision and a hash of the weight files before those files are deleted. A
permanent archive with a DOI will accompany the camera-ready version.

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
