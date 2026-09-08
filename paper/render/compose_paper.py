#!/usr/bin/env python3
"""Step 4 — compose paper.tex from intro_relwork.tex plus the remaining sections.

Preamble, Introduction and Related Work are preserved verbatim from Step 3.
Every numeric value below traces to inputs/experimental_log.md. LaTeX patterns
follow paper/tex_profile.json (cleveref, nicefrac, microtype, T1 all True).
"""
import json, pathlib, re

PAPER = pathlib.Path(__file__).resolve().parents[1]
PROJECT = PAPER.parent

# Round-2 review: the manuscript quoted three different response totals and none
# matched the receipts. The counts are now read from the census rather than
# typed, so a new run cannot leave the paper describing the old corpus.
CENSUS = json.loads((PROJECT / "results/receipt_census_v1.json").read_text())
WORDS = {12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen", 16: "sixteen",
         17: "seventeen", 18: "eighteen", 19: "nineteen", 20: "twenty"}


def counts(text: str) -> str:
    """Substitute the census into the manuscript's response and run counts."""
    total = CENSUS["total_scored_responses"]
    runs = CENSUS["model_runs"]
    grouped = f"{total // 1000}{{,}}{total % 1000:03d}" if total >= 1000 else str(total)
    text = text.replace("NSCOREDRESPONSES", grouped)
    text = text.replace("NMODELRUNS", WORDS.get(runs, str(runs)))
    assert "NSCOREDRESPONSES" not in text and "NMODELRUNS" not in text
    return text


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
    # The venue forbids altering margins, font sizes or line spacing. The
    # template's geometry line is therefore left exactly as supplied, and
    # columnsep keeps the class default rather than a widened value.
    src = src.replace("\\setlength{\\parskip}{2pt}",
                      "\\setlength{\\parskip}{2pt}\n\\sloppy\n\\emergencystretch=2em\n"
                      "\\setcounter{topnumber}{3}\n"
                      "\\setcounter{dbltopnumber}{3}\n"
                      "\\setcounter{totalnumber}{4}", 1)
    # Audit #46: the type1 Times from \\usepackage{times} emits fi/fl as
    # U+FB01/FB02 with no ToUnicode map, so a reviewer searching the PDF for
    # "certificate" got zero hits (53 word-forms affected). newtxtext is the
    # same Times design with a proper map. Rejected alternatives: Times New
    # Roman via fontspec fixes extraction but has no small-caps face, and the
    # paper sets every arm name in \\textsc; STIX Two Text loses them as well.
    src = src.replace("\\usepackage{times}", "\\usepackage{newtxtext}", 1)
    # A heading must not be the last thing on a page. The appendix heading was
    # stranded at the foot of the references page with every one of its floats
    # overleaf; \clearpage starts it on its own page. The two penalties stop the
    # same thing happening to a section or subsection heading in the body: TeX
    # will not break within four lines of one, and the -3000 makes breaking just
    # after a heading effectively forbidden.
    src = src.replace("\\setlength{\\parskip}{2pt}",
                      "\\setlength{\\parskip}{2pt}\n"
                      "\\clubpenalty=10000\n\\widowpenalty=10000\n"
                      "\\displaywidowpenalty=10000\n"
                      "\\makeatletter\\@secpenalty=-3000\\makeatother\n", 1)
    src = src.replace("\\usepackage{xcolor}",
                      "\\usepackage{xcolor}\n\\usepackage{colortbl}\n\\usepackage{microtype}\n"
                      # OPEN, audit #46: xdvipdfmx emits fi/fl as the precomposed
                      # U+FB01/FB02, so a reviewer searching the PDF for
                      # "certificate" gets zero hits (53 word-forms affected).
                      # Tried and rejected: \\XeTeXgenerateactualtext (not honoured
                      # by this pipeline), microtype \\DisableLigatures (refuses
                      # under XeTeX), fontspec + TeX Gyre Termes (font absent from
                      # the tectonic bundle). Fix needs a full TeX Live with the
                      # OTF, or a pdflatex build.

                      "\\usepackage{nicefrac}\n\\usepackage{url}\n\\usepackage{cleveref}", 1)
    # tables compact
    src = src.replace("\\begin{table}[t]\n\\centering\n\\caption",
                      "\\begin{table}[t]\n\\centering\\small\n\\caption")
    # the two widest objects span both columns
    # Every table here is wider than a 3.2in column, and fig:arms needs the
    # full measure. Promote them by name, so adding a float cannot silently
    # change the placement of another one.
    # tab:sdt is narrow enough to set in one column at
    # \footnotesize, which removes two full-width bands and lets them float
    # beside the text that discusses them instead of queueing at a page top.
    for label in ("tab:sdt",):
        span = float_block(src, label, "table")
        assert span is not None, f"{label}: not found"
        start, end = span
        src = src[:start] + src[start:end].replace("\\centering\\small",
                                                   "\\centering\\footnotesize", 1) + src[end:]
    SPANNING = tuple((lab, "table") for lab in (
        "tab:panels", "tab:edges", "tab:arms",
        "tab:models")) + tuple(
        # #52: both were authored ~6in and placed at \columnwidth, a 44-54%
        # shrink that set 8.5pt type at 3-5pt. They are appendix floats, so
        # full width costs no body space.
        (lab, "figure") for lab in ("fig:arms", "fig:replication", "fig:detection"))
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
                      "width=0.92\\textwidth]{figures/substrate_size_curve")
    src = src.replace("width=\\columnwidth]{figures/validity_share_replication",
                      "width=0.92\\textwidth]{figures/validity_share_replication")
    src = src.replace("width=\\columnwidth]{figures/detection_response_distribution",
                      "width=0.92\\textwidth]{figures/detection_response_distribution")
    # --- supporting floats to an appendix -----------------------------------
    # The venue caps main text at 9 pages; references and appendix are exempt.
    # These six are supporting: four figures whose numbers already appear in a
    # main-text table, the dataset inventory, and the SDT breakdown whose
    # headline values are quoted in prose.
    # Round-2 review: tab:sdt and fig:detection carry primary
    # results and were pushed out by a page squeeze. They come back; what stays
    # is the dataset inventory and three figures whose numbers are already in a
    # main-text table.
    # tab:edges joins them: the rebuilt Figure 1 now carries all four edges, the
    # diagonal, the interaction and the ceiling, so the table adds only exact
    # p-values, which the prose quotes.
    # tab:sdt joins them. Round 3 asked for it in the body and it was there for
    # two revisions; the body has since gained the ordering result and the
    # runtime check, and its five rows are quoted in the prose that cites it.
    # tab:models now lists every model, including the two scored on the second
    # runtime, so a separate scale table would repeat it; the harm ladder reads
    # fine as five numbers in §5.6. tab:arms stays in the body -- it is where
    # §5.2 gets its primary contrast and §5.4's "which baseline" argument.
    # #48: tab:sdt is the one appendix float the body can still take -- measured,
    # it lands on p5 beside the section that cites it and the body still ends p9.
    # The other eight each push the body to p10.
    # tab:detection is slimmed to the three deltas but stays here: measured, a
    # fourth body float pushes the body to p10 and no amount of prose cutting
    # brings it back -- the cost is float placement, not words.
    # Order here fixes two things at once. Floats number by source order, so
    # putting fig:order second among the figures makes the figure numbers follow
    # the order the body cites them (it is cited in 5.3 but was numbered 5), and
    # placing the two single-column floats where they can share a page saves a
    # page: 17pp -> 16pp, measured.
    # tab:edges is Experiment 1's reanalysis headline and now sits beside the
    # section that reads it. fig:order was tested too and both together push the
    # body to p10, so it stays here. What remains is the dataset inventory, the
    # detection deltas (whose direction is reference-dependent anyway) and four
    # figures whose values are already tabulated in a body table.
    APPENDIX = (("tab:panels", "table"),
                ("tab:detection", "table"),
                ("fig:arms", "figure"), ("fig:order", "figure"),
                ("fig:replication", "figure"), ("fig:detection", "figure"),
                ("fig:size", "figure"))
    moved = []
    for label, env in APPENDIX:
        span = float_block(src, label, env)
        assert span is not None, f"{label}: not found for the appendix move"
        start, end = span
        moved.append(src[start:end])
        src = src[:start].rstrip("\n") + "\n\n" + src[end:].lstrip("\n")
    # The heading was stranded at the foot of the references page with every one
    # of its floats overleaf, because a heading cannot share a page with floats
    # and nothing else. The orienting paragraph gives it company, which fixes
    # the placement without a \clearpage -- measured, that costs a page more
    # for the same result.
    tail = ("\n\\appendix\n\\section{Supporting Tables and Figures}\n\n"
            "Supporting material for the results in the body. \\Cref{tab:panels} "
            "inventories the sealed panels; \\cref{tab:edges} gives the four edges "
            "of the $2\\times2$ with their adjusted $p$ values; \\cref{tab:detection} "
            "the abstention deltas of \\cref{sec:detection}. The four figures plot "
            "results whose values are already tabulated above: the ten arms "
            "(\\cref{fig:arms}), the validity share across checkpoints "
            "(\\cref{fig:replication}), the three-class response distribution "
            "(\\cref{fig:detection}), the order profile (\\cref{fig:order}) and the "
            "substrate ladder (\\cref{fig:size}).\n\n"
            + "\n\n".join(moved) + "\n\n")
    src = src.replace("\\end{document}", tail + "\\end{document}", 1)

    # Let floats reach the bottom of a column as well as the top. This must run
    # after the promotion and appendix passes, which match "[t]" exactly.
    for env in ("table", "figure", "table*", "figure*"):
        src = src.replace("\\begin{" + env + "}[t]", "\\begin{" + env + "}[tb]")

    return src



src = (PAPER / "drafts/intro_relwork.tex").read_text()

TITLE = ("What a Language Model Does with a Solver Certificate:\\\\\n"
         "An Answer-Evidence Decomposition Across Twelve Models")

ABSTRACT = r"""
Solver-, tool- and retrieval-augmented systems report large accuracy gains,
routinely read as evidence that the model used the supplied material. Two
mechanisms give the same number: reading a supplied answer, and reasoning over supplied state. The
standard control, a same-shape irrelevant record, separates neither. We build one that does, holding every surface property we could enumerate
and audit fixed
while destroying validity alone, across four sealed experiments and two
robustness studies: $NSCOREDRESPONSES$ scored responses, re-derivable from
released receipts.

The decomposition is the contribution; what it returns is not. The validity
share is $98.3\%$ on one checkpoint and $40.4$--$51.4\%$ on another, so a
single-model mechanism result should not be generalised, ours included. Two
negative results hold on every checkpoint: reversing a rule and the premise it
fires on costs accuracy, and all three follow a fabricated final rule to the wrong answer on $189$, $186$
and $192$ of $192$ items. We find no positive evidence that any checkpoint verifies validity (the strongest
abstains on $0$ of $192$ broken certificates), but report that the abstention
test's direction depends on which reference arm it uses.

We report the design's limits too: the $2\times2$ is ceiling-limited, viability
is a property of (model $\times$ arm $\times$ runtime) not of a model, and two
prespecified criteria of our own were invalidated by our own data.
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
literal withheld (state, no answer), and \textsc{full} both. An \emph{edge} of this square moves one factor; the \emph{diagonal} moves two, so
a null on it attributes to neither. This is identification, not statistics: the
prespecified primary contrast of the experiment we reanalyse,
\textsc{proof\_prefix} minus \textsc{conclusion\_only}, is that diagonal. The four
edges instead give a state main effect (the mean of the two
edges adding state) and an answer main effect defined symmetrically.

\subsection{Surface-matched invalidity}
\label{sec:broken}

A prefix that stops one step short is not a clean state manipulation. It still
names the query's subject and predicate in adjacent lines, so surface
co-occurrence remains available. To isolate validity we construct
\textsc{broken\_chain}: one intermediate link is cut so the displayed lines no
longer reach the query, while every surface property we enumerate below is held
fixed.

Concretely, against the matched \textsc{truncate\_1} arm we preserve the
query-entity occurrence count (audited per item, not approximately), the
presence of the query predicate in the final rule, the line count and the exact fact/rule/literal type sequence. Per-item character
lengths are recorded but not constrained.
Every \emph{rule} displayed is a real rule of the theory; exactly one derived
literal is false. All 192 items are certified by forward-closure saturation
(\cref{sec:closure}) to leave the query \emph{undetermined} under the displayed
lines. The decomposition follows:
\begin{align}
\text{total state} &= \textsc{truncate\_1} - \textsc{irrelevant},\\
\text{surface} &= \textsc{broken\_chain} - \textsc{irrelevant},\\
\text{validity} &= \textsc{truncate\_1} - \textsc{broken\_chain}.
\end{align}

Four companion arms separate the remaining confounds.
\textsc{same\_entity\_irrelevant} gives a valid derivation about the \emph{query}
entity toward an unrelated predicate. It names the query subject four times where \textsc{irrelevant} names it zero, and neither contains the query predicate, so the pair isolates entity repetition. \textsc{shuffled} presents
\textsc{truncate\_1}'s lines in seeded random order; \textsc{truncate\_2} and
\textsc{truncate\_3} withhold two and three steps, giving a depth ladder; and
\textsc{misleading} supplies a valid-looking chain whose single fabricated final
rule establishes the query's negation, leaving the ground-truth answer unchanged
so that following the supplied state means answering incorrectly.

\subsection{Certifying underdetermination}
\label{sec:closure}

Showing that a query \emph{is} derivable is easy: exhibit the proof. Showing it
is \emph{not} requires saturating the theory's forward closure. Our certifier operates under open-world semantics with explicit negation: a
negative literal is derivable only if something derives it, never by failure to
prove the positive. Antecedents are ordinary literals, with no negation as
failure, which makes naive forward chaining sound and complete here.

Two safeguards matter for generated theories: a round cap with a
\texttt{saturated} flag, so a malformed theory fails loudly rather than spinning,
and rejection of any theory deriving both an atom and its negation. An
item is \emph{undetermined} when neither the query nor its negation appears in
the closure.

Validation has three layers, because one would not be worth much. Against the
open-world splits of a public corpus \citep{tafjord2020proofwriter} at depths
$0$--$3$ and $5$, $23{,}240$ of $23{,}240$ questions agree, including $10{,}440$ undetermined. But those labels also come from forward chaining over the same
fragment, so this largely measures one chainer against another and covers none of
the nonce theories. Nine adversarial theories therefore probe cycles, chains past the round cap,
derived negation, absent symbols and entity-specific rules; all nine pass and the
cases are released. A \emph{differential} test against an independently written
reference agrees on $192/192$ items, which catches implementation error but not a
misconception about the semantics, since it encodes the same ones. No item enters a sealed panel
without a certification record.

\subsection{Measurement: sensitivity, not accuracy}
\label{sec:measurement}

Accuracy on a balanced panel is uninterpretable when the responder is biased. One
arm below scores $50.0\%$ with an identical $9/96$ ``Yes'' rate in \emph{both} classes: $d' = 0.00$, no discriminative signal at all, at or below the trivial
always-one-label strategy. We therefore report sensitivity $d'$ and criterion $c$ alongside
accuracy for every arm \citep{macmillan1991detection,stanislaw1999calculation},
using the loglinear correction for extreme rates. For the three-class panel the headline scalar is balanced accuracy, the mean of
per-class recalls: chance is $33.3\%$, and a single-label responder scores exactly
chance.

Paired contrasts report the complete $2\times2$ table, the exact two-sided
McNemar test \citep{mcnemar1947note} as the decision criterion, and a seeded $20{,}000$-resample paired bootstrap interval (bias-corrected and
accelerated for paired differences \citep{efron1987better}, percentile for the
share ratio, which is a ratio of differences), with Holm adjustment within
declared families.

\section{Experimental Setup}

\subsection{Task, panels and scoring}

Every experiment and study here uses rule-chaining queries over small theories of
facts and universally quantified rules. \Cref{tab:panels} lists the panels. The sealed
panels are procedurally generated after model release with per-item nonce
vocabularies, are mutually disjoint, and fix derivation depth at four by
construction, recorded per item. The public corpus is used \emph{only} to
validate the certifier; no item from it is scored by any model here.

Experiment 4 generates no panel: it rescores Experiment 2's items with a third
candidate available. On Experiment 3's $64$ undetermined items there is no terminal literal to supply,
so \textsc{conclusion\_only} states that the query is not derivable and
\textsc{proof\_prefix} is truncated at a random point; those two cells instantiate
the $2\times2$ less exactly than the other thirds. Theories, certificates and queries are
byte-identical; only the instruction line and candidate set change, and the
change is recorded in the seal. Its \textsc{none} arm withholds the record under that same instruction, fixing
the abstention floor.

Two robustness studies reuse these panels. \Cref{sec:order} re-scores Experiment 2's items under eight permutations of the
certificate's lines each, recording where the final rule and its premise land.
\Cref{sec:runtime} re-scores Experiment 3's panel through a second inference
stack, \texttt{transformers} on CUDA rather than \texttt{mlx-lm}, and there extends
the sweep with Llama-3.1-8B and Qwen2.5-14B.

\begin{table}[t]
\centering
\caption{Datasets. The sealed panels are nonce-generated and disjoint; the
public corpus validates the certifier only. Experiment 4 rescores Experiment 2's
items rather than generating new ones.}
\label{tab:panels}
\begin{tabular}{llrl}
\toprule
Panel & Classes & Items & Used by \\
\midrule
\texttt{b14} & entailed / contradicted & 192 & Experiment 1 \\
\texttt{b15} & entailed / contradicted & 192 & Experiment 2 \\
\texttt{b16} & entailed / contradicted / undetermined & 192 & Experiment 3 \\
\texttt{b17}, \texttt{b17b} & \texttt{b15} items, three candidates & 192 & Experiment 4 \\
\texttt{b18} & \texttt{b15} items, 8 line orders each & 192 & \cref{sec:order} \\
\texttt{b16} on a second stack & as \texttt{b16} & 192 & \cref{sec:runtime} \\
ProofWriter OWA \citep{tafjord2020proofwriter} & three-way & 23{,}240 & certifier validation \\
\bottomrule
\end{tabular}
\end{table}

Responses are scored by direct next-token likelihood over verified single-token
candidates: \texttt{Yes}/\texttt{No} for Experiments 1 and 2,
\texttt{Yes}/\texttt{No}/\texttt{Unknown} for Experiments 3 and 4. The model generates
no free text, so nothing is parsed and no verdict is inferred from prose. Every prompt is instruction, theory, solver record and query, with the record
line omitted entirely in \textsc{none}; the theory is visible in all arms. In
Experiment 1 the arms differ in the record's header as well as its content, one of which names the truncation, a confound on that experiment's prespecified
primary contrast, removed in Experiments 2--4.

\subsection{Models}

Experiments 1 and 2 use the same frozen 3B instruction-tuned checkpoint at
4-bit precision \citep{team2024qwen}, pinned to byte-identical weights, so the
anchors of the first transfer to the second without a weights caveat.
Experiment 3 scores ten instruction-tuned models from $0.5$B to $7.6$B
\citep{team2024qwen,grattafiori2024llama,team2025gemma,microsoft2025phi,team2024olmo,allal2025smollm},
all loaded through \texttt{mlx-lm} from the pinned mirrors in
\texttt{models.toml}. The runner did not record a dtype, so we do not claim
uniform precision across the ten. An
eligibility screen confirmed that all ten load, complete a forward pass, and
tokenise all three candidates as single distinct tokens.

\subsection{Sealed protocol}

Scoring takes the highest-likelihood candidate token; on an exact tie the first
candidate in the declared order wins, which across Experiment 2's $5{,}760$
prospective responses occurs twice. Panels are hash-stamped before scoring;
Experiments 2 and 3 refuse a panel whose hash does not match, while the others
record the hash without enforcing it. The answer authority is opened after all
receipts are written, but by convention in the analysis order rather than by a
gate in the code, and we state it as a convention. 

Experiment 3 makes a deliberate protocol change: \emph{no gate blocks the run}.
Where earlier practice excluded a model that failed a delivery screen, delivery
is itself the capability under test here, so a model that cannot emit a verdict
reliably is a finding about substrate viability rather than a reason to drop it.
Tooling failures (a model that will not load, or whose tokeniser cannot represent
the candidates) remain exclusions and are not findings; the screen found none.


\section{Results}

\subsection{Reading the factorial as a \texorpdfstring{$2\times2$}{2x2}}

\Cref{fig:factorial} arranges Experiment 1's five arms by
\cref{sec:decomposition}. Its prespecified primary contrast,
$\textsc{proof\_prefix} - \textsc{conclusion\_only} = -4.7$pp (exact McNemar
$p = 0.078$), was reported as a null. It is the diagonal.

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

The four edges are reported in \cref{tab:edges}. \textbf{This reading is post hoc}: a different analysis of sealed data, not a
re-run. Every value is re-derived from the 960 raw receipts by a script that asserts it
reproduces all five published per-arm counts before reporting. The state main effect is $+22.4$pp and the answer main effect
$+27.1$pp.

The \textbf{interaction is $-29.2$pp}, larger than either main effect. The design
is also \textbf{ceiling-limited}: \textsc{full} reaches $191/192$ ($99.5\%$), only $13.0$pp above
\textsc{proof\_prefix}'s $86.98\%$. Both
``other factor present'' edges are therefore compressed, and the averaged main
effects deflated with them.

The answer literal appears to retain $30\%$ of its value once state is present
($12.50/41.67$), but with \textsc{full} at ceiling that ratio measures the
headroom left rather than redundancy, so we draw no conclusion from it.
Separating the channels needs \textsc{full} away from ceiling.

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
\texttt{No} to $88\%$ of items, and \cref{tab:sdt} shows \textsc{irrelevant}
returning an identical $9/96$ ``Yes'' rate in both classes at $d' = 0.00$, below a trivial always-\texttt{No} strategy's $96/192$. The contradicted class
contributed $0$ of the $21$ discordant pairs, so the effective sample was $96$.

\begin{table}[t]
\centering
\caption{Signal detection for Experiment 1; hits and false alarms out of 96
each. Apparent chance and zero
sensitivity are not the same thing.}
\label{tab:sdt}
\begin{tabular}{lrrrr}
\toprule
Arm & Hits & FA & $d'$ & $c$ \\
\midrule
\textsc{none} & 9 & 14 & $-0.25$ & $+1.17$ \\
\textsc{irrelevant}      &  9 &  9 & $\mathbf{0.00}$ & $+1.29$ \\
\textsc{conclusion\_only}& 80 &  0 & $+3.52$ & $+0.81$ \\
\textsc{proof\_prefix}   & 71 &  0 & $+3.20$ & $+0.97$ \\
\textsc{full}            & 95 &  0 & $+4.72$ & $+0.20$ \\
\bottomrule
\end{tabular}
\end{table}

\subsection{Validity versus surface overlap}

Experiment 2 holds surface form fixed and destroys validity alone. The primary
contrast is $\textsc{truncate\_1} - \textsc{broken\_chain} = +60.4$pp: exact
McNemar $p = 6.9\times10^{-18}$, BCa $[+49.0, +68.8]$, from a paired table of $1$
both correct, $58$ \textsc{truncate\_1}-only, $0$ \textsc{broken\_chain}-only and
$37$ neither, on the entailed subset ($n = 96$) as declared before the run since
the contradicted class contributes no discordance. Sensitivity moves with it
($d'$ drops $2.446$), so this is a change in discrimination, not criterion.

The decomposition is therefore a total state effect of $+61.5$pp comprising
$+1.0$pp of surface overlap ($p = 1$, 95\% percentile $[+0.0, +3.1]$pp) and $+60.4$pp of
validity: a \textbf{validity share of $98.3\%$, 95\% percentile $[94.4, 100.0]$},
bootstrapping the whole ratio rather than its numerator. \Cref{tab:arms} and
\cref{fig:arms} give the full arm set, and \cref{sec:replication} shows the
share is specific to this checkpoint.

\begin{figure}[t]
\centering
\includegraphics[width=\textwidth]{figures/arm_decomposition.png}
\caption{Ten matched arms on one item set, differing only in the solver record.
Left: correct on the entailed subset (of 96). Right: sensitivity $d'$, signed.
Destroying validity alone removes almost the whole effect \emph{on this
checkpoint}; on gemma-3-4b it does not, see \cref{sec:replication}. The
\textsc{misleading} arm, whose fabricated final rule points the wrong way, is
followed to the wrong answer on 189 of 192 items.}
\label{fig:arms}
\end{figure}

\begin{table}[t]
\centering\small
\caption{Experiment 2: ten matched arms scored on three checkpoints, entailed
subset (correct of 96, with signed $d'$). Only the solver record differs between
arms. The share rows give the validity component as a fraction of the total state
effect, against the \textsc{irrelevant} control and against the unaided
\textsc{none} arm; the two coincide wherever unaided competence is zero.}
\label{tab:arms}
\begin{tabular}{lrrrrrr}
\toprule
& \multicolumn{2}{c}{Qwen2.5-3B 4-bit} & \multicolumn{2}{c}{Qwen2.5-3B bf16}
& \multicolumn{2}{c}{Gemma-3-4B} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-7}
Arm & /96 & $d'$ & /96 & $d'$ & /96 & $d'$ \\
\midrule
\textsc{none}                    &  0 & $0.00$ &  0 & $0.00$ & \textbf{22} & $1.83$ \\
\textsc{irrelevant}              &  0 & $0.00$ &  0 & $0.00$ &  2 & $0.62$ \\
\textsc{same\_entity\_irrelevant}&  0 & $0.00$ &  0 & $0.00$ &  3 & $0.77$ \\
\textsc{truncate\_3}             &  0 & $0.00$ &  0 & $0.00$ &  4 & $0.88$ \\
\textsc{truncate\_2}             &  0 & $0.00$ &  0 & $0.00$ &  4 & $0.88$ \\
\textsc{truncate\_1}             & 59 & $2.85$ & 72 & $3.23$ & 96 & $5.13$ \\
\textsc{broken\_chain}           &  1 & $0.41$ &  1 & $0.41$ & \textbf{58} & $2.83$ \\
\textsc{shuffled}                & 14 & $1.53$ & 12 & $1.43$ & \textbf{86} & $3.80$ \\
\textsc{misleading}              &  0 & $-4.36$ &  0 & $-4.06$ &  0 & $-5.13$ \\
\textsc{full}                    & 96 & $5.13$ & 96 & $5.13$ & 96 & $5.13$ \\
\midrule
Validity share vs \textsc{irrelevant} & \multicolumn{2}{c}{$98.3\%$}
 & \multicolumn{2}{c}{$98.6\%$} & \multicolumn{2}{c}{$\mathbf{40.4\%}$} \\
Validity share vs \textsc{none}       & \multicolumn{2}{c}{$98.3\%$}
 & \multicolumn{2}{c}{$98.6\%$} & \multicolumn{2}{c}{$\mathbf{51.4\%}$} \\
\bottomrule
\end{tabular}
\end{table}

Three supporting contrasts sharpen the reading. Entity repetition explains
nothing: $\textsc{same\_entity\_irrelevant} - \textsc{irrelevant} = +0.0$pp
($p = 1$), despite the former naming the query subject four times and the latter
not at all. Order matters \emph{on this checkpoint}:
$\textsc{truncate\_1} - \textsc{shuffled} = +46.9$pp
($p = 6.8\times10^{-13}$, Holm $1.4\times10^{-12}$), so it is not reading a bag of statements, though \cref{sec:replication} shows this too is
checkpoint-specific, and \cref{sec:order} shows \emph{order} is the wrong word
for it. And depth is a cliff, not a slope:
$\textsc{truncate\_2} - \textsc{truncate\_1} = -61.5$pp
($p = 3.5\times10^{-18}$, Holm $1.0\times10^{-17}$), with \textsc{truncate\_2}
scoring identically to supplying no certificate at all. Holm adjustment is within the family declared in \cref{sec:measurement};
\cref{tab:edges} carries the adjusted values for the four post hoc edges. Five arms are indistinguishable at $96/192$, $0/96$ entailed, $d' = 0.000$,
$c = 2.565$: behaviour is binary: the chain reaches one step from the answer,
or the model is blind to it.

\subsection{Not adjacency, but direction}
\label{sec:order}

\textbf{The gap-versus-direction split here is post hoc.} \textsc{shuffled} is one
seeded permutation per item, and scrambling moves three
things at once: the gap between the final rule and the premise it fires on, the
order of that pair, and everything else. We re-scored the same items under eight
permutations each on all three checkpoints, recording where those two lines
landed. An identity arm reproduces \textsc{truncate\_1}'s bytes and returns its
receipts $192/192$ throughout. Over eight permutations the effect spans $[+41.7, +50.0]$, $[+60.4, +63.5]$ and
$[+6.2, +13.5]$pp on the three checkpoints, each range containing its published
single draw ($+46.9$, $+62.5$, $+10.4$pp).

\begin{figure}[tb]
\centering
\includegraphics[width=\columnwidth]{figures/order_profile.png}
\caption{Accuracy against the gap between the final rule and the premise it fires on: all seven gaps, all
three checkpoints, each checkpoint's canonical-order
score dashed. Distance is flat. Direction is not: rule-after scores $26.8$,
$22.4$ and $94.9\%$ against $5.8$, $4.8$ and $84.9\%$ for rule-before. Gemma-3-4B
still answers $84.9\%$ of rule-before items correctly, so reversal degrades
rather than prevents.}
\label{fig:order}
\end{figure}

\textbf{Direction separates the arms; distance does not.} Accuracy does not
decline with the gap: on the 4-bit checkpoint it is $18.1\%$ at gap $1$ and
$24.0\%$ at gap $7$, though that cell is $6$ of $25$, so we draw no trend from it beyond the absence
of visible harm (\cref{fig:order}). Reversing
them does. Rule \emph{after} its premise gives $26.8\%$, $22.4\%$ and $94.9\%$
across the three checkpoints against $5.8\%$, $4.8\%$ and $84.9\%$ for rule
\emph{before}; paired within item on the 4-bit checkpoint, $45$ items favour
rule-after against $2$ ($p = 1.6\times10^{-11}$).

The direction of that effect holds on all three checkpoints, but its size does
not: a $4.6$--$4.7\times$ ratio on the Qwen checkpoints is a $10$pp modulation on
Gemma-3-4B, which is near ceiling throughout. So ordering is not a \emph{requirement} everywhere; what generalises is that reversing the pair
costs accuracy, not that the model cannot proceed without it. Canonical order is better again ($61.5\%$ against ${\sim}27\%$), so the chain before the last step matters
too.

\subsection{The validity share does not generalise}
\label{sec:replication}

The decomposition of \cref{sec:broken} was run on two further checkpoints: the
same model at bfloat16 rather than 4-bit, which isolates quantisation from model
identity, and a different family. \Cref{tab:arms} carries all three; \cref{fig:replication} plots the split.

\begin{figure}[t]
\centering
\includegraphics[width=\columnwidth]{figures/validity_share_replication.png}
\caption{The surface and validity components on three checkpoints. Gemma-3-4B's
surface component is $+58.3$pp against $+1.0$pp for the two Qwen checkpoints.
Bars give the decomposition against the \textsc{irrelevant} control; the share
annotation gives both denominators, $40.4\%$ against that control and $51.4\%$
against what the model manages unaided. The two coincide on the Qwen checkpoints,
which score $0/96$ with no certificate, and diverge only where a substrate has
competence of its own.}
\label{fig:replication}
\end{figure}

Quantisation is the smaller effect: bfloat16 raises \textsc{truncate\_1} from 59
to 72 of 96 while leaving the share essentially unchanged. One pair supports no
general claim about precision. Model identity does
not behave that way. Gemma-3-4B answers \textsc{broken\_chain} correctly on
\textbf{58 of 96} items where the other two manage 1, so the same control that
isolates inference on one checkpoint exposes substantial surface exploitation on
another.

\textbf{Which baseline.} The share divides by the effect against
\textsc{irrelevant}, which on the Qwen checkpoints also scores $0/96$, so the
choice is invisible there. Gemma-3-4B answers $22$ of $96$ entailed items with no certificate at all, so
against \textsc{none} its share is $51.4\%$, not $40.4\%$. Both are in
\cref{tab:arms}, and we make no claim that most of its effect is surface overlap.
\textbf{The control is also not inert on such a substrate}: Gemma scores $2/96$
under \textsc{irrelevant} and $4/96$ under \textsc{truncate\_2} against $22/96$
unaided, so an uninformative record costs it most of its own competence, and any
effect measured against \textsc{irrelevant} on a competent substrate is inflated
by that cost.
The divergence is the finding, not either number.

Order-sensitivity fails to replicate alongside the share: \textsc{shuffled}
scores $14$ and $12$ of $96$ on the Qwen checkpoints and $86$ on Gemma-3-4B.
Reading a certificate as a bag of statements is a checkpoint-level property too.

\textbf{We therefore do not claim that solver-supplied state is used as inference
in general.} On the checkpoint of \cref{sec:broken} it overwhelmingly is; on the strongest substrate in our sweep, between two-fifths and half survives. What generalises is the \emph{method}, not the value it returns.

One result does replicate without exception, and it is the negative one
(\cref{sec:corruption}).

\subsection{Following a corrupted apparatus}
\label{sec:corruption}

The \textsc{misleading} arm supplies a chain identical to \textsc{full} except in
its last two sentences: a fabricated final rule, absent from the theory, and the
terminal literal it licenses, both inverted. The ground-truth answer is unchanged. The model scores $3$ of $192$ against \textsc{full}'s $192$, a paired difference
of $-98.4$pp on all items and $-100$pp on the entailed subset, where the exact
test gives $p = 2.5\times10^{-29}$, with $d' = -4.363$. It replicates without exception: the arm scores $3$, $6$ and
$0$ of $192$ across the three checkpoints, at $d'$ of $-4.36$, $-4.06$ and
$-5.13$, so the model exploiting surface overlap most is also the one most
completely misled.

The class split is the sharper evidence. This model's standing prior is \texttt{No}: under \textsc{none} it answers
\texttt{No} to all $192$ items, at $c = 2.565$. Under
\textsc{misleading} it answers \texttt{Yes} on \textbf{93 of the 96 contradicted
items}, inverting a near-total prior because a fabricated rule told it to.
Corrupted solver output does not merely fail to help; it overrides the model's
own strong default.

The model therefore follows a valid-looking certificate that points the wrong
way on 189 of 192 items. Against the $98.3\%$ share the two are jointly informative: what the model does
with a supplied derivation is sensitive to whether it reaches the query, and
offers no defence when it reaches the wrong conclusion.
\Cref{sec:detection} shows that sensitivity is completion rather than verification, so the certificate is followed, not checked.

\subsection{Abstention does not identify detection}
\label{sec:detection}

A natural reading of \cref{sec:broken} is that the model detects a broken chain.
The binary design cannot support that reading, because the correct answer under a
broken certificate \emph{is} the model's default label: ``detected the break'' and
``found no pattern to complete'' predict the same response.

We separated them by rescoring the \textsc{broken\_chain} items with three
candidates rather than two. A validity tracker abstains \emph{more} when the
chain is broken; a pattern completer falls back to its default, which
\textsc{irrelevant} and \textsc{none} fix from either side.
\Cref{tab:detection} and \cref{fig:detection} give all three checkpoints on all
four arms.

\begin{table}[t]
\centering\small
\caption{Three-candidate rescoring: the change in \texttt{Unknown} rate under
\textsc{broken\_chain}, in points of 192, against each of three references.
Detection predicts a \emph{rise}. It falls against the two records carrying no
query-relevant material and rises against the surface-matched \textsc{trunc\_1},
so the sign is a function of the reference. Per-arm rates are in \cref{sec:detection}.}
\label{tab:detection}
\begin{tabular}{lrrr}
\toprule
Checkpoint & $\Delta_{\textsc{none}}$ & $\Delta_{\textsc{irrel.}}$ & $\Delta_{\textsc{trunc\_1}}$ \\
\midrule
Qwen2.5-3B 4-bit & $-37.5$ & $-32.8$ & $\mathbf{+31.2}$ \\
Qwen2.5-3B bf16  & $-3.6$  & $-38.5$ & $\mathbf{+11.5}$ \\
Gemma-3-4B       & $-0.5$  & $-7.8$  & $0.0$ \\
\bottomrule
\end{tabular}
\end{table}

\begin{figure}[t]
\centering
\includegraphics[width=\columnwidth]{figures/detection_response_distribution.png}
\caption{Three-candidate response distribution, three checkpoints, four arms.
Dotted and dashed lines mark the \textsc{none} and \textsc{irrelevant} abstention
baselines, $4.7$pp apart at 4-bit and $34.9$pp at bfloat16. A
broken chain lowers abstention against \emph{both} references on every checkpoint, the opposite of the
direction validity detection predicts.}
\label{fig:detection}
\end{figure}

\textbf{The sign of the effect depends on the reference.} Against the two records
carrying no query-relevant material, \textsc{none} and \textsc{irrelevant},
abstention falls on every checkpoint. Against \textsc{truncate\_1}, the surface-matched
\emph{valid} partner of \cref{sec:broken}, it \emph{rises}, by
$31.2$ and $11.5$pp on the two checkpoints with any abstention headroom. Neither comparison is clean. The unmatched references differ from
\textsc{broken\_chain} in content as well as validity, and are themselves $4.7$pp
apart at 4-bit against $34.9$pp at bfloat16; \textsc{truncate\_1} is matched but is
an arm the model can complete, so its low abstention reflects success, not a
neutral baseline.
\textbf{We therefore draw no conclusion from the abstention delta, and withdraw
the claim that it refutes detection.}

What does not depend on a reference is what the strongest substrate does with a
broken certificate: it abstains \textbf{$0$ times in $192$} and answers
\texttt{Yes} on $76$. The 4-bit checkpoint shows the same behaviour in its counts:
\texttt{No} is $110$ of $192$ under \textbf{both} \textsc{broken\_chain} and
\textsc{truncate\_1}, the arms differing only in \texttt{Yes}, $1$ against $61$.

\textbf{We find no positive evidence that any checkpoint verifies validity}, but
we no longer claim this test refutes detection. The direct evidence is
\cref{sec:corruption}, where all three follow a fabricated final rule to the wrong
answer, which a model checking validity would not. \Cref{sec:mechanism} notes the design limit behind this.

\subsection{Which models can serve as the interface}

Experiment 3 scores ten models on the three-class panel in all five arms;
\cref{sec:runtime} adds two more on a second runtime, twelve in all, nine common
to both (one of the ten does not load there). We had
declared that a model relays non-determination at $\geq 80\%$ recall on
undetermined items with full solver material. \textbf{Eight of ten passed, and
the criterion was invalid}: single-class recall is maximised by answering \texttt{Unknown} to everything,
which four models approach: they emit \texttt{Unknown} on $54$--$97\%$ of items
averaged over arms, and never emit \texttt{No} at all. We replace it \textbf{post hoc} with a floor on every class, minimum per-class
recall $\geq 0.50$, retaining both verdicts in the released results. A second
criterion was prespecified and we report it here rather than let it disappear: a
per-model paired \textsc{full} $-$ \textsc{none} on the $64$ undetermined items,
exact McNemar, target $20$pp. Five of ten meet it under Holm ($+53.1$, $+48.4$,
$+46.9$, $+37.5$ and $+20.3$pp; the other five reach $\leq +9.4$pp and none
survives adjustment). Two of those five are rejected by the replacement criterion,
at $0.375$ and $0.422$ minimum per-class recall: the same
gameability by a different route.
\Cref{tab:models} gives all five arms for every model with its per-arm verdict.

\begin{table}[t]
\centering
\caption{All five arms, all twelve models. Each cell is balanced accuracy
(\%, chance $=33.3$) $/$ minimum per-class recall; bold clears the $0.50$ recall
floor, so \textsc{viable in} is derivable from the cells beside it. Shaded rows
are the scale extension on a second runtime (\cref{sec:runtime}): the parameter
ladder continues, the numbers are not comparable across the rule. Viability is
per arm because it is a property of (model $\times$ arm $\times$ runtime), not of
a model.}
\label{tab:models}
\begin{tabular}{lrccccc@{\hskip 1em}l}
\toprule
Model & B & \textsc{none} & \textsc{irrel} & \textsc{concl} & \textsc{prefix} & \textsc{full} & \textsc{viable in} \\
\midrule
Qwen2.5-0.5B &  0.5 & 35.4/0.00 & 34.9/0.00 & 41.1/0.00 & 43.2/0.00 & 63.5/0.00 & --- \\
OLMo-2-1B    &  1.0 & 35.9/0.00 & 33.3/0.00 & 53.6/0.00 & 34.9/0.00 & 42.2/0.00 & --- \\
Llama-3.2-1B &  1.2 & 33.9/0.00 & 33.9/0.00 & 57.8/0.00 & 36.5/0.00 & 37.0/0.00 & --- \\
Qwen2.5-1.5B &  1.5 & 33.3/0.00 & 33.3/0.00 & 43.2/0.00 & 34.9/0.00 & 37.0/0.00 & --- \\
SmolLM2-1.7B &  1.7 & 33.3/0.00 & 33.3/0.00 & 45.3/0.00 & 39.6/0.00 & 69.3/0.38 & --- \\
Qwen2.5-3B   &  3.0 & 41.1/0.00 & 39.1/0.00 & \textbf{96.4/0.91} & \textbf{74.0/0.56} & \textbf{90.6/0.72} & concl, prefix, full \\
Llama-3.2-3B &  3.2 & 45.8/0.00 & 43.2/0.02 & 67.2/0.02 & 55.2/0.02 & 80.7/0.42 & --- \\
Phi-4-mini   &  3.8 & 44.8/0.00 & 39.6/0.00 & 68.2/0.05 & 71.9/0.33 & \textbf{90.6/0.72} & full \\
Gemma-3-4B   &  4.3 & 63.5/0.36 & 51.0/0.06 & \textbf{100.0/1.00} & \textbf{84.4/0.53} & \textbf{96.4/0.89} & concl, prefix, full \\
Qwen2.5-7B   &  7.6 & 33.3/0.00 & 33.3/0.00 & \textbf{97.9/0.94} & 67.2/0.02 & 71.4/0.14 & \textbf{concl only} \\
\midrule
\rowcolor{black!7} Llama-3.1-8B &  8.0 & 38.5/0.00 & 34.4/0.00 & 65.6/0.00 & 64.6/0.00 & 66.7/0.00 & --- \\
\rowcolor{black!7} Qwen2.5-14B  & 14.7 & 57.3/0.00 & 35.4/0.00 & 80.7/0.42 & 70.3/0.12 & 82.8/0.48 & --- \\
\bottomrule
\end{tabular}
\end{table}

\textbf{Viability is a property of (model $\times$ arm $\times$ runtime), not of a model}. The third factor is \cref{sec:runtime}'s. The decisive row is Qwen2.5-7B: minimum per-class recall falls from $0.938$ under
\textsc{conclusion\_only}, where it is second best in the sweep, to $0.141$ under
\textsc{full}. Its contradicted-class recall collapses \emph{when the proof state is supplied}: it can express three
outcomes, and the state is what breaks it. \textbf{Supplying proof state degrades three of ten
models} here, two of them otherwise among the strongest substrates. On the CUDA re-scoring the same measure gives two of eleven, which is
\cref{sec:runtime}'s runtime factor again.

This bounds a claim we would otherwise have made. Nothing below $3$B clears the
floor in any arm, but that is a floor for \emph{tolerating full certificates},
not for serving as an interface, and the effect is not monotonic. On the Qwen2.5
ladder to $14.7$B, family and recipe fixed and the whole ladder on the second
runtime, the harm runs $0.000$, $0.000$, $-0.219$, $-0.688$, $+0.062$: it peaks in
a mid-range band and is \emph{absent} at the top. Neither new model clears the
floor, though. Llama-3.1-8B is \textbf{degenerate in every arm} despite balanced accuracies up to $66.7\%$, the strongest
single datum against a size floor. Qwen2.5-14B peaks at $0.484$, so ``absent at the top'' is not ``14B works''. 

\begin{figure*}[t]
\centering
\includegraphics[width=0.92\textwidth]{figures/substrate_size_curve.png}
\caption{All five arms for all ten models, ordered by parameter count. Chance is
$33.3\%$. Bar colour gives the per-arm viability verdict. Qwen2.5-7B is viable
under \textsc{conclusion\_only} and not under \textsc{full}: viability is a
property of (model $\times$ arm $\times$ runtime), not of a model.}
\label{fig:size}
\end{figure*}

\subsection{The runtime is a factor}
\label{sec:runtime}

Everything above is scored through \texttt{mlx-lm}. Re-scoring the same sealed
panel, same weights and same prompt bytes through \texttt{transformers} on CUDA
covers nine of the ten: \textsc{gemma-3-4b}'s weight mirror is an MLX conversion
the second stack cannot load, which is itself a limit on how far a table can be
moved between backends.

Eight of the nine agree on $95.5$--$99.7\%$ of individual responses with no
verdict moving. \textbf{Phi-4-mini does not.} It agrees on $87.9\%$ ($116$ flips of $960$), and its \textsc{full} arm is viable under one stack and not
the other: minimum per-class recall $0.719$ against $0.219$, balanced accuracy
$90.6\%$ against $74.0\%$, on identical weights. The flips reach $3.0$ logits, so this is not tie-breaking noise.

Two consequences. Viability is a property of (model $\times$ arm $\times$
\emph{runtime}), not of a model. And the checkpoint carrying the $40.4$--$51.4\%$
share of \cref{sec:replication} is \textsc{gemma-3-4b}, the one model this check cannot cover, so the
share itself has no runtime replication, and we do not
claim one.

\subsection{The same \texorpdfstring{$2\times2$}{2x2} across ten models}

Experiment 3's five arms are the $2\times2$ of \cref{sec:decomposition} plus a
baseline, on ten models, from receipts already collected. \textbf{This reading is
post hoc}, like \cref{sec:decomposition}'s. The mean state main
effect is $+8.7$pp against a mean answer main effect of $+21.6$pp, with a mean
interaction of $-15.9$pp; \textsc{conclusion\_only} exceeds
\textsc{proof\_prefix} in \textbf{8 of 10} models and equals or exceeds
\textsc{full} in $6$ of $10$. The answer channel dominates the state channel across the model set, and
Experiment 1's state main effect of $+22.4$pp is not typical of it. That mean
averages over four responders degenerate in every arm, three with negative state
effects; excluding them gives $+14.7$pp against $+28.5$pp, so the cross-model
state effect is not less than half the single-model estimate and we do not claim
it is. The ordering survives either subset.

\section{Limitations}

\subsection{Scope of the mechanism claim}
\label{sec:mechanism}

On both Qwen checkpoints the inference is \emph{exactly one step deep}:
\textsc{truncate\_2} scores identically to supplying no certificate ($0/96$), so
the model completes a final inference when both premises are present and cannot
chain two steps. Gemma-3-4B is not in that position
($4/96$ against $22/96$ unaided), so depth is checkpoint-specific. \Cref{sec:order}
tests the ordering directly: reversing the final rule and its premise costs
accuracy on every checkpoint, while separating them does not, which rules out
the adjacency reading we first gave this. Nor does it \emph{detect} invalidity, which
\cref{sec:detection} tests directly and cannot establish, in either direction. \Cref{sec:replication} bounds
the claim further: against the \textsc{irrelevant} control the share of the state effect that survives destroying validity spans
$40.4$--$98.6\%$ against \textsc{irrelevant}, $51.4$--$98.6\%$ against unaided.

The full theory is visible in every arm, so the query stays derivable whatever
the certificate says, and breaking a certificate is diagnostic only where the
model scores $0/96$ from the theory alone, true of both Qwen checkpoints and
not of Gemma-3-4B. A model using a broken
certificate as a pointer back into the theory would be doing inference of a
different kind; on Gemma-3-4B that is a live alternative rather than a
hypothetical one, since $20$ of its $22$ unaided successes recur under
\textsc{broken\_chain}. We record it as an interpretation caveat, not a
controlled alternative. \textsc{truncate\_2} and \textsc{truncate\_3} also drop the query predicate, which
lives in the final rule, so the depth ladder confounds depth with predicate
presence and must be read against \textsc{same\_entity\_irrelevant}.

\subsection{Post hoc analyses and superseded criteria}

Four analyses are post hoc and labelled where used: the $2\times2$ reading of
Experiment 1 is a different analysis of sealed data, not a re-run; Experiment 3's
viability criterion replaced a prespecified threshold the data showed to be
invalid (the original is retained in the released results); and \cref{sec:order}'s gap-versus-direction split is read off eight orderings per
item that happened to land in each cell, not a design that fixed them.

Experiment 1 also carries five defects we report rather than repair: the
unreachable $15$pp target noted above; no recorded proof depth, so its failures
cannot be stratified; task identifiers encoding the semantic class; a release as
a flat receipt export with no sealed panel, so its answer key is reconstructed
from those identifiers rather than read from an authority; and a screen for
response tokens leaking into a certificate that was a malformed regular expression and never fired
(the released certificates contain none, checked after the fact). Experiments 2--4 fix all five.

\subsection{Generalisation}

One task family, small models, synthetic panels. Nonce vocabularies establish
item novelty, not independence from every relevant pretraining pattern
\citep{golchin2023time,deng2024investigating}, and model is not randomised, so
cross-model comparisons are descriptive.

\textbf{Prompt format.} Experiment 4 changes only the instruction and candidate
set on byte-identical inputs, and the response distribution moves substantially
\citep{zhao2021calibrate,zheng2023large}. Its arms share a baseline under that
instruction, so the contrast holds but the absolute rates do not.



\textbf{Quantisation.} Experiments 1 and 2 use a 4-bit checkpoint and Experiment
3 bfloat16, so they describe different artefacts of the same model.
\Cref{sec:replication} bounds the difference; we do not treat the two as one.

\textbf{Prior report.} Experiment 1's per-arm counts and prespecified primary
contrast appeared in an earlier unpublished report by the present authors;
everything else is new. That report concluded the 3B checkpoint failed an
open-world unknown gate, whereas Experiment 3 finds the same family viable.
Panels, candidate sets and quantisation all differ, which plausibly explains it,
but we flag it rather than leave it to a reader who finds both.

An undetermined \textsc{proof\_prefix} cannot contain the query predicate, so such
items offer fewer surface cues and a surface-matching model looks worse on them
for reasons unrelated to abstention.

\textbf{Scoring regime.} Every response is a forced choice among verified
single-token candidates. No deployed solver-augmented pipeline works this way, so
transfer of these results to a generative one is untested.

\textbf{Checkpoint selection.} Experiment 2's three checkpoints were chosen
\emph{after} Experiment 3 identified viable substrates and cover two families;
Phi-4-mini, the third viable substrate, was never run on those arms.

\textbf{$d'$ ceiling.} At $n = 96$ the loglinear correction censors $d'$ at
$\pm 5.13$, and eight cells of \cref{tab:arms} sit on it, so $d'$
\emph{differences} involving a saturated arm, \cref{sec:broken}'s
$2.446$ included, are bounds. Finally, every theory here arrives \emph{already
formalised}: nothing tests whether a model can turn a prose framework into solver
input, which \cref{sec:corruption} makes consequential.

\section{Conclusion}

\looseness=-1
Solver assistance improves a small model's accuracy on rule-chaining queries, and
end-to-end accuracy cannot say why. The decomposition can: arrange the arms so each
contrast moves one factor, and break validity while holding surface form fixed.
What it returns is model-specific: $98.3\%$ of
the state effect survives on one checkpoint and $40.4$--$51.4\%$ on another, so we
offer the method as the
contribution and decline to generalise its value, ours included.

\looseness=-1
Two findings hold on every checkpoint, and both are negative. Accuracy degrades
when the final rule precedes the premise it fires on. And nothing defends against
a wrong apparatus. Given a certificate whose fabricated final rule
establishes the negation, the three checkpoints answer incorrectly on $189$, $186$
and $192$ of $192$, inheriting the apparatus's errors in full. Depth is one step
on the Qwen checkpoints but not on Gemma, and whether the model detects
invalidity our abstention test cannot settle: the delta changes sign with the
reference arm. Two criteria we had prespecified failed here: a recall floor on one class, gamed
by models answering that class almost everywhere, and a $15$pp target an arm at
$91.7\%$ could not reach. Both were caught only by reporting sensitivity and headroom beside accuracy, as was a baseline arm at $50.0\%$ with $d' = 0.00$.
We recommend that practice as standard.

\section*{Reproducibility Statement}

\textbf{Code and data.} The supplementary material accompanying this submission
is self-contained: sealed panels and answer authorities, all $NSCOREDRESPONSES$
per-response receipts, the generators, runners, audits and analysis scripts, and
the forward-closure certifier with its validation against the public corpus.
Every number in this paper can be re-derived from a fresh unpack with no network
access, no model weights and no external packages; the audits use the Python standard
library only, so verification does not depend on resolving an
environment. Panels are hash-stamped, and the runners for Experiments 2 and 3 refuse a panel
whose hash does not match. Each receipt carries a SHA-256 of its own contents,
and all $NSCOREDRESPONSES$ verified with zero failures. The count is not typed into the manuscript: it is
produced by \texttt{scripts/census\_receipts\_v1.py} from the released receipts
and substituted at compose time.

\textbf{Checking one number takes a minute.} \texttt{scripts/verify.py} recomputes each headline value and prints it beside the
value this paper states. Five of its seven claims re-derive from the receipts and
the sealed authority; the cross-model mean and the response census read released
analysis files, which the listed scripts regenerate:
\texttt{python3 scripts/verify.py validity-share} recomputes the $98.3\%$ of
\cref{sec:broken} and shows the four counts it came from.
\texttt{--all} does the same for the validity share, Gemma's two baselines, the
corruption counts, the detection direction on three checkpoints, the $2\times2$
state main effect, the cross-model mean and the response census. It uses the
standard library only, so a reviewer needs no environment beyond Python. Model weights are not redistributed, but each run records the
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

# --- preamble ---------------------------------------------------------------
# The tex_profile packages are added once, in apply_layout(). Doing it here too
# duplicated microtype, nicefrac and cleveref in the preamble, because the
# replacement text still contains the \usepackage{xcolor} anchor it matched on.
src = src.replace("\\title{TITLE}", "\\title{" + TITLE + "}")
src = src.replace("ABSTRACT", ABSTRACT)

# --- replace the empty section stubs with the body -------------------------
stub = re.compile(r"\\section\{Method\}.*?(?=\\bibliographystyle)", re.S)
assert stub.search(src), "section stubs not found"
src = stub.sub(lambda _m: BODY.strip() + "\n\n", src)   # lambda: LaTeX backslashes are not regex templates

src = counts(src)
src = apply_layout(src)

out = PAPER / "drafts/paper.tex"
out.write_text(src)
print(f"paper.tex written: {len(src)} chars, {src.count(chr(10))} lines")
for s in ("Introduction", "Related Work", "Method", "Experimental Setup", "Results",
          "Limitations", "Conclusion", "Reproducibility Statement", "AI-Use Statement"):
    print(f"  {'OK ' if ('section{'+s+'}' in src or 'section*{'+s+'}' in src) else 'MISSING'} {s}")
