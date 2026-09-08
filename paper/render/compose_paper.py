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
                      "\\setcounter{topnumber}{4}\n"
                      "\\setcounter{dbltopnumber}{4}\n"
                      "\\setcounter{totalnumber}{6}\n"
                      "\\renewcommand{\\dbltopfraction}{0.85}\n"
                      "\\renewcommand{\\dblfloatpagefraction}{0.7}", 1)
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
    # Only the two wide tables span both columns. tab:edges and tab:panels were
    # full-width too, which put eight double-column floats into seven available
    # page-tops -- arithmetic no amount of prose cutting fixes, and two figures
    # were deferred past the references. Set in one column at \footnotesize they
    # can also reach a column bottom, which is four times the placement freedom.
    SPANNING = tuple((lab, "table") for lab in (
        "tab:panels", "tab:edges", "tab:arms", "tab:models")) + tuple(
        # #52: both were authored ~6in and placed at \columnwidth, a 44-54%
        # shrink that set 8.5pt type at 3-5pt. They are appendix floats, so
        # full width costs no body space.
        (lab, "figure") for lab in ("fig:replication", "fig:detection"))
    for label, env in SPANNING:
        span = float_block(src, label, env)
        if span is None:
            continue
        start, end = span
        block = src[start:end]
        src = src[:start] + block.replace("\\begin{" + env + "}[t]", "\\begin{" + env + "*}[t]", 1) \
                                 .replace("\\end{" + env + "}", "\\end{" + env + "*}", 1) + src[end:]
    # figure widths for a narrow column
    src = src.replace("width=\\textwidth]{figures/arm_decomposition",
                      "width=0.86\\textwidth]{figures/arm_decomposition")
    src = src.replace("width=0.8\\textwidth]{figures/substrate_size_curve",
                      "width=0.92\\textwidth]{figures/substrate_size_curve")
    src = src.replace("width=\\columnwidth]{figures/validity_share_replication",
                      "width=0.92\\textwidth]{figures/validity_share_replication")
    src = src.replace("width=\\columnwidth]{figures/detection_response_distribution",
                      "width=0.92\\textwidth]{figures/detection_response_distribution")
    # Every table and figure is now in the main text. The prose was cut roughly
    # in half in the readability pass, which freed the column space they needed,
    # so there is no appendix: a reader never leaves the argument to find the
    # evidence. Guard against silently losing one in a future rewrite.
    for lab in ("tab:panels", "tab:edges", "tab:sdt", "tab:arms", "tab:models",
                "fig:replication", "fig:order", "fig:detection"):
        assert "\\label{" + lab + "}" in src, lab + ": lost in the rewrite"

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
mechanisms give the same number: reading a supplied answer, and reasoning over
supplied state. The standard control, a same-shape irrelevant record, separates
neither. We build one that does, holding every surface property we could
enumerate and audit fixed while destroying validity alone, across four sealed
experiments and two robustness checks: $NSCOREDRESPONSES$ scored responses,
re-derivable from released receipts.

Asked what a model does with a certificate, the instrument returns a different
answer for almost every checkpoint, arm and inference runtime. The share of the
state effect that survives destroying validity is $98.3\%$ on one checkpoint and
$40.4$--$51.4\%$ on another. Inference depth is one step on two checkpoints and
not on a third; one model is a usable interface under one inference stack and
degenerate under another, on identical weights. Two criteria we had prespecified
were gamed by label collapse.

One result does not move. Given a certificate whose fabricated final rule
establishes the query's negation, all three checkpoints answer incorrectly on
$189$, $186$ and $192$ of $192$ items, and the strongest abstains on $0$ of
$192$ broken certificates. Mechanism claims about solver assistance do not
transfer between checkpoints. The failure to check the solver does.
""".strip()

BODY = r"""
\section{Method}

\subsection{The answer-evidence decomposition}
\label{sec:decomposition}

A solver certificate carries two things: the \emph{answer} to the query, and the
\emph{state} that answer follows from. End-to-end accuracy conflates them. We
separate them with a $2\times2$ of answer evidence by proof state
(\cref{fig:factorial}), with a no-material baseline outside it.
\textsc{irrelevant} supplies a valid derivation for a different entity,
\textsc{conclusion\_only} the derived terminal literal alone,
\textsc{proof\_prefix} the chain with that literal withheld, and \textsc{full}
both. An \emph{edge} moves one factor and therefore attributes; the
\emph{diagonal} moves two and cannot. The experiment we reanalyse chose that
diagonal as its primary contrast.

\textbf{Why the usual control is not enough.} Take a theory in which Kexil is
dovrant, every dovrant thing is plesh, and every plesh thing is marn, with the
query \emph{is Kexil marn?} The standard control gives a same-shape derivation
about a different entity, fixing length, format and generic validity. But the
arm it is compared against ends on \emph{Kexil is plesh}, one line from a rule
naming \emph{marn}: the query's subject and its predicate sit in adjacent lines.
A model that never performs the last step, and only registers that the two terms
co-occur where a derivation is heading, reproduces every number a model
completing it would. The square localises the gain to state; it cannot show the
state was used as inference.

\subsection{Surface-matched invalidity: the word-matching test}
\label{sec:broken}

\begin{table*}[tb]
\centering\footnotesize
\caption{\textbf{What the model sees}, from sealed item \texttt{b15-4ef53c71}.
Every prompt is the same 18-line theory in invented vocabulary, then one solver
record, then the query. Only the record changes between arms. Left: the
\textsc{full} record, a complete four-step derivation. Right: what each other
arm does to it. \textsc{broken\_chain} is the word-matching test --- it replaces
line 6 with a different \emph{real} rule of the theory, one that does not fire,
so the chain stops reaching the query, while line 8 still names the query's
predicate and the entity still appears four times, exactly as in
\textsc{truncate\_1}. \textsc{misleading} instead invents a rule the theory does
not contain.}
\label{tab:stimulus}
\begin{minipage}[t]{0.42\textwidth}
\vspace{0pt}
\ttfamily\scriptsize
\textrm{\textbf{Query:}} Bimol is vrinpek. \textrm{(true)}\\[3pt]
\textrm{\textbf{\textsc{full} record}}\\
1\ \ Bimol is vrasler.\\
2\ \ All vrasler people are deinmal.\\
3\ \ Bimol is deinmal.\\
4\ \ All deinmal people are kuthbror.\\
5\ \ Bimol is kuthbror.\\
6\ \ All kuthbror people are gasplaek.\\
7\ \ Bimol is gasplaek.\\
8\ \ All gasplaek people are vrinpek.\\
9\ \ Bimol is vrinpek.
\end{minipage}\hfill
\begin{minipage}[t]{0.55\textwidth}
\vspace{0pt}
\begin{tabular}{@{}ll@{}}
\toprule
Arm & Record supplied \\
\midrule
\textsc{none}        & no record at all \\
\textsc{irrelevant}  & same shape, a different entity throughout \\
\textsc{same\_entity\_irrel.} & same entity, an unrelated predicate \\
\textsc{truncate\_1} & lines 1--8: the answer line withheld \\
\textsc{truncate\_2} & lines 1--6: two steps withheld \\
\textsc{truncate\_3} & lines 1--4: three steps withheld \\
\textsc{shuffled}    & lines 1--8 in seeded random order \\
\textsc{broken\_chain} & lines 1--8, but 6 becomes \texttt{All foskdem} \\
                     & \texttt{people are zuftbas.} and 7 becomes \\
                     & \texttt{Bimol is zuftbas.} Line 8 unchanged \\
\textsc{misleading}  & lines 1--9, but 8 becomes \texttt{All gasplaek} \\
                     & \texttt{people are not vrinpek.} and 9 becomes \\
                     & \texttt{Bimol is not vrinpek.} \\
\textsc{full}        & lines 1--9 \\
\bottomrule
\end{tabular}
\end{minipage}
\end{table*}

\Cref{tab:stimulus} shows one sealed item and every record we supply for it.
Call the prefix that stops one step short \textsc{truncate\_1}: it is the
strongest arm that withholds the answer, and the one a surface-matching model
can still exploit. \textsc{broken\_chain} is built to strip that exploit. We cut
one intermediate link, so the displayed lines no longer reach the query, while
holding fixed against \textsc{truncate\_1} the query-entity occurrence count
(audited per item), the query predicate in the final rule, the line count and
the fact/rule/literal sequence. Every rule displayed is a real rule of the
theory; exactly one derived literal is false. All $192$ items are certified to
leave the query undecided under the displayed lines. That gives
\begin{align}
\text{total state} &= \textsc{truncate\_1} - \textsc{irrelevant},\\
\text{surface} &= \textsc{broken\_chain} - \textsc{irrelevant},\\
\text{validity} &= \textsc{truncate\_1} - \textsc{broken\_chain}.
\end{align}
Five companion arms separate the rest.
\textsc{same\_entity\_irrelevant} isolates entity repetition, naming the query
subject four times where \textsc{irrelevant} names it none.
\textsc{shuffled} keeps \textsc{truncate\_1}'s eight lines in seeded random
order. \textsc{truncate\_2} and \textsc{truncate\_3} withhold two and three
steps, giving a depth ladder. And \textsc{misleading} is the corrupted-solver
arm: one fabricated final rule, absent from the theory, establishes the query's
negation, so following the supplied record means answering incorrectly while the
true answer is unchanged.

\subsection{Certifying that nothing decides a query}
\label{sec:closure}

Showing a query is derivable is easy: exhibit the proof. Showing nothing decides
it requires saturating the theory's forward closure. Our certifier works under
open-world semantics with explicit negation, so a negative literal holds only if
something derives it, never by failure to prove the positive. It agrees with a
public corpus \citep{tafjord2020proofwriter} on $23{,}240$ of $23{,}240$
questions, including $10{,}440$ undecided; passes nine adversarial theories
probing cycles, round-cap overruns, derived negation and absent symbols; and
agrees with an independently written reference on $192$ of $192$ items. No item
enters a sealed panel without a certification record.

\section{Experimental Setup}

Every experiment asks a rule-chaining query over a small theory of facts and
universally quantified rules. \Cref{tab:panels} names the six and says what each
one does.

\begin{table}[t]
\centering
\caption{\textbf{The four experiments and two robustness checks.} Sealed panels
use per-item invented vocabularies, are mutually disjoint, and fix derivation
depth at four. The public corpus validates the certifier only: no item from it
is scored by any model here.}
\label{tab:panels}
\footnotesize
\begin{tabular}{@{}llll@{}}
\toprule
Panel & Items & Experiment & What it does \\
\midrule
\texttt{b14} & 192 binary & the reanalysis & re-reads a published five-arm factorial as the $2\times2$ of \cref{fig:factorial} \\
\texttt{b15} & 192 binary & the validity control & ten matched arms (\cref{tab:stimulus}) on three checkpoints \\
\texttt{b16} & 192 three-class & the model sweep & ten models $\times$ five arms, with an \texttt{Unknown} class \\
\texttt{b17}, \texttt{b17b} & \texttt{b15} items & the abstention rescoring & re-scores the broken certificates with \texttt{Unknown} allowed \\
\midrule
\texttt{b18} & \texttt{b15} items & line-order check & eight permutations of each record \\
\texttt{b16} on CUDA & as \texttt{b16} & runtime check & \texttt{transformers} rather than \texttt{mlx-lm}, plus two larger models \\
\midrule
ProofWriter OWA & 23{,}240 & \multicolumn{2}{l}{certifier validation only \citep{tafjord2020proofwriter}} \\
\bottomrule
\end{tabular}
\end{table}

\textbf{The abstention rescoring} generates no panel. It rescores the validity
control's items with a third candidate available, changing only the instruction line and the candidate set on
byte-identical inputs, and its \textsc{none} arm fixes the abstention floor
under that same instruction. On the sweep's $64$ undecidable items there is
no terminal literal to supply, so those two cells instantiate the $2\times2$
less exactly than the rest. Two robustness checks reuse these panels: one
rescores the validity control's items under eight permutations of the certificate's
lines each, recording where the final rule and its premise land; the other
rescores the sweep's panel through \texttt{transformers} on CUDA rather than
\texttt{mlx-lm}, and there adds Llama-3.1-8B and Qwen2.5-14B.

Responses are scored by direct next-token likelihood over verified single-token
candidates: \texttt{Yes}/\texttt{No} for the first two,
\texttt{Yes}/\texttt{No}/\texttt{Unknown} for the others. The model generates no
free text, so nothing is parsed and no verdict is inferred from prose. Every
prompt is instruction, theory, solver record and query, and the theory is
visible in every arm. In the reanalysis the record's header differs between arms
as well as its content, a confound on that experiment's primary contrast, removed
everywhere after it.

\textbf{Models.} The reanalysis and the validity control use one frozen 3B instruction-tuned
checkpoint at 4-bit precision \citep{team2024qwen}, pinned to byte-identical
weights. The sweep scores ten instruction-tuned models from $0.5$B to $7.6$B across six
families, Qwen2.5, Llama-3.2, Gemma-3, Phi-4-mini, OLMo-2 and SmolLM2
\citep{team2024qwen,grattafiori2024llama,team2025gemma,microsoft2025phi,team2024olmo,allal2025smollm},
through \texttt{mlx-lm} from pinned mirrors; the runner did not record a dtype,
so we claim no uniform precision across the ten. No gate blocks that run:
delivery is itself the capability under test, so a model that cannot emit a
verdict reliably is a finding rather than an exclusion.

\textbf{Sensitivity, not accuracy.} Accuracy on a balanced panel is
uninterpretable when the responder is biased. One arm below scores $50.0\%$ with
an identical $9/96$ ``Yes'' rate in \emph{both} classes: $d' = 0.00$, no
discriminative signal at all, at or below answering one label to everything. We
therefore report $d'$ and criterion $c$ for every arm
\citep{macmillan1991detection,stanislaw1999calculation} using the loglinear
correction, balanced accuracy for the three-class panel (chance $33.3\%$), the
exact two-sided McNemar test \citep{mcnemar1947note} as the decision criterion,
and seeded paired bootstrap intervals \citep{efron1987better} adjusted for
multiple comparisons within declared families.

\section{Results}

\subsection{The state effect is real, and it is validity}

The reanalysis begins from a null. Its prespecified primary contrast,
$\textsc{proof\_prefix} - \textsc{conclusion\_only} = -4.7$pp (exact McNemar
$p = 0.078$), was reported as no effect. Read through the square, that contrast
is the diagonal: it moves both factors at once, so the null attributes to
neither.

\textbf{Both channels carry real effect, and they are not additive.} The state
main effect is $+22.4$pp, the answer main effect $+27.1$pp, and the interaction
$-29.2$pp, larger than either; \cref{tab:edges} gives the four edges. This
reading is post hoc, re-derived from the 960 raw receipts by a script that
asserts it reproduces all five published per-arm counts before reporting. The
design is ceiling-limited, \textsc{full} reaching $191/192$, so both
``other factor present'' edges are compressed and the averaged main effects
deflated with them.

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

\textbf{The baseline description was also wrong.} The model answers \texttt{No}
to $88\%$ of items, and \textsc{irrelevant} returns an identical $9/96$ ``Yes''
rate in both classes at $d' = 0.00$ (\cref{tab:sdt}), below a trivial
always-\texttt{No} strategy's $96/192$.

\begin{table}[t]
\centering
\caption{Signal detection for the reanalysis; hits and false alarms out of 96
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

\textbf{Destroying validity alone removes almost all of the state effect.}
$\textsc{truncate\_1} - \textsc{broken\_chain} = +60.4$pp (exact McNemar
$p = 6.9\times10^{-18}$, BCa $[+49.0, +68.8]$, entailed subset $n = 96$ as
declared before the run), with $d'$ dropping $2.446$, so this is a change in
discrimination and not in criterion. The total state effect of $+61.5$pp is
therefore $+1.0$pp of surface overlap ($p = 1$) and $+60.4$pp of validity: a
\textbf{validity share of $98.3\%$}, 95\% percentile $[94.4, 100.0]$.
\Cref{tab:arms} gives the full arm set on three checkpoints.

Two supporting contrasts. Entity repetition explains nothing
($+0.0$pp, $p = 1$) despite one arm naming the query subject four times and the
other not at all. And depth is a cliff rather than a slope: withholding two
steps instead of one scores identically to supplying no certificate.

\begin{table}[t]
\centering\small
\caption{The validity control: ten matched arms scored on three checkpoints, entailed
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

\subsection{Almost nothing the instrument returns transfers}

\textbf{The instrument transfers; the number it returns does not.} The
decomposition was run on two further checkpoints: the same model at bfloat16,
which isolates quantisation from model identity, and a different family.
\Cref{fig:replication} plots the split.

Quantisation is the smaller effect and leaves the share unchanged. Model
identity is not like that.
Gemma-3-4B answers \textsc{broken\_chain} correctly on \textbf{$58$ of $96$}
items where the other two manage $1$, so the same control that isolates
inference on one checkpoint exposes substantial surface exploitation on another.
Its share is $40.4\%$ against the \textsc{irrelevant} control and $51.4\%$
against what it manages unaided; the divergence is the finding rather than either
number. The control is not inert on a model like that either, costing Gemma most
of its own competence, so any effect measured against it there is inflated.
Order-sensitivity does not replicate alongside the share either
(\cref{tab:arms}).

\begin{figure}[t]
\centering
\includegraphics[width=\columnwidth]{figures/validity_share_replication.png}
\caption{The surface and validity components on three checkpoints. Gemma-3-4B's
surface component is $+58.3$pp against $+1.0$pp for the two Qwen checkpoints.
Bars give the decomposition against the \textsc{irrelevant} control; the share
annotation gives both denominators, $40.4\%$ against that control and $51.4\%$
against what the model manages unaided. The two coincide on the Qwen checkpoints,
which score $0/96$ with no certificate, and diverge only where a model has
competence of its own.}
\label{fig:replication}
\end{figure}

\textbf{The square itself is no steadier.} Read across ten models, post hoc from
receipts already collected, the mean state main effect is $+8.7$pp against a
mean answer main effect of $+21.6$pp: the answer channel dominates, and
the reanalysis's $+22.4$pp is not typical of the set. Excluding four responders
degenerate in every arm gives $+14.7$pp against $+28.5$pp, and the ordering
survives either subset.

\textbf{Whether a model can serve as the interface at all varies the same way.}
We had declared that a model relays non-determination at $\geq 80\%$ recall on
undecidable items with full solver material. Eight of ten passed and the
criterion was invalid: single-class recall is maximised by answering
\texttt{Unknown} to everything, which four models approach. We replace it
\textbf{post hoc} with a floor on every class, minimum per-class recall
$\geq 0.50$, retaining both verdicts in the released results. A second
prespecified criterion, a paired $\textsc{full} - \textsc{none}$ of $20$pp on
the undecidable items, is met by five of ten under Holm, two of which the
replacement floor rejects: the same gameability by another route.
\Cref{tab:models} gives all five arms for all twelve models.

\begin{table}[t]
\centering
\caption{All five arms, all twelve models. Each cell is balanced accuracy
(\%, chance $=33.3$) $/$ minimum per-class recall; bold clears the $0.50$ recall
floor, so \textsc{viable in} is derivable from the cells beside it. Shaded rows
are the scale extension on a second runtime: the parameter
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

Read by row, \textbf{viability is a property of (model $\times$ arm $\times$
runtime), not of a model.} Qwen2.5-7B falls from second best in the sweep under
\textsc{conclusion\_only} to $0.141$ minimum per-class recall under
\textsc{full}: supplying the proof state is what breaks it, and it breaks three
of ten models here. Nothing below $3$B clears the floor in any arm, but that is a
floor for \emph{tolerating full certificates} rather than a size law:
Llama-3.1-8B is degenerate in every arm, and Qwen2.5-14B never clears it.

\textbf{The third factor is the inference stack.} Re-scoring the same sealed
panel, same weights and same prompt bytes through \texttt{transformers} on CUDA
covers nine of the ten. Eight agree on $95.5$--$99.7\%$ of individual responses
with no verdict moving. Phi-4-mini agrees on $87.9\%$, and its \textsc{full} arm
is viable under one stack and not the other: minimum per-class recall $0.719$
against $0.219$, on identical weights, with flips reaching $3.0$ logits.
Gemma-3-4B, the checkpoint carrying the $40.4$--$51.4\%$ share, is the one model
this check cannot cover, so that share has no runtime replication.

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

\subsection{What does not vary}

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

\textbf{Reversing the final rule and the premise it fires on costs accuracy on
every checkpoint; separating them does not.} The split is post hoc:
\textsc{shuffled} is one seeded permutation per item and moves three things at
once, so we re-scored the same items under eight permutations each on all three
checkpoints, recording where those two lines landed. An identity arm reproduces
\textsc{truncate\_1}'s bytes and returns its receipts $192/192$ throughout.
Distance is flat; direction is not (\cref{fig:order}). Rule \emph{after} its
premise gives $26.8$, $22.4$ and $94.9\%$ across the three checkpoints against
$5.8$, $4.8$ and $84.9\%$ for rule \emph{before}; paired within item on the
4-bit checkpoint, $45$ items favour rule-after against $2$
($p = 1.6\times10^{-11}$). The direction holds everywhere, its size does not: a
$4.6\times$ ratio on the Qwen checkpoints is a $10$pp modulation on Gemma-3-4B.

\textbf{Nothing defends against a wrong solver.} The \textsc{misleading} arm is
identical to \textsc{full} except in its last two sentences: a fabricated final
rule, absent from the theory, and the inverted literal it licenses. The
ground-truth answer is unchanged. All three checkpoints answer incorrectly on
\textbf{$189$, $186$ and $192$ of $192$} items, at $d'$ of $-4.36$, $-4.06$ and
$-5.13$, so the model exploiting surface overlap most is also the one most
completely misled. The class split is sharper still. This model's standing prior
is \texttt{No}: under \textsc{none} it answers \texttt{No} to all $192$ items,
at $c = 2.565$. Under \textsc{misleading} it answers \texttt{Yes} on
\textbf{$93$ of the $96$ contradicted items}. A fabricated rule inverts a
near-total prior.

\textbf{Whether any model notices, we cannot say.} Rescoring the
\textsc{broken\_chain} items with an \texttt{Unknown} candidate available should
raise abstention if the model tracks validity. It falls by $37.5$ and $32.8$
points against \textsc{none} and \textsc{irrelevant} and \emph{rises} by
$31.2$ against the surface-matched \textsc{truncate\_1}
(\cref{fig:detection}): the sign is a function of the reference,
and neither reference is clean. We draw no conclusion from it and withdraw the
claim that it refutes detection. What needs no reference is that the most capable
of the three abstains \textbf{$0$ times in $192$} on a broken certificate and
answers \texttt{Yes} on $76$. We find no positive evidence that any checkpoint
verifies validity, and the direct evidence is the corruption arm above, which a
model checking validity would not fail.

\section{Limitations}
\label{sec:limits}

\textbf{Scope of the mechanism claim.} On both Qwen checkpoints the inference is
exactly one step deep: withholding two steps scores identically to supplying no
certificate ($0/96$). Gemma-3-4B is not in that position ($4/96$ against $22/96$
unaided), so depth is checkpoint-specific, as is the share, which spans
$40.4$--$98.6\%$ against the \textsc{irrelevant} control and $51.4$--$98.6\%$
against unaided. The full theory is visible in every arm, so breaking a
certificate is diagnostic only where the model scores $0/96$ from the theory
alone, true of both Qwen checkpoints and not of Gemma-3-4B, where $20$ of its
$22$ unaided successes recur under \textsc{broken\_chain}; a model using a broken
certificate as a pointer back into the theory would be doing inference of a
different kind, and we record that as an interpretation caveat rather than a
controlled alternative. \textsc{truncate\_2} and \textsc{truncate\_3} also drop
the query predicate, so the depth ladder confounds depth with predicate
presence, and an undecidable \textsc{proof\_prefix} cannot contain that
predicate either, so such items offer fewer surface cues.

\textbf{Post hoc analyses and superseded criteria.} The $2\times2$ reading of
the reanalysis, the sweep's replacement viability criterion and the
gap-versus-direction split are all post hoc and labelled where used; the
originals are retained in the released results. The reanalysis carries five
defects we report rather than repair: a prespecified $15$pp target with only
$8.3$pp of headroom above the $91.7\%$ arm it applied to; no recorded proof
depth, so its failures cannot be stratified; task identifiers encoding the
semantic class; a release as a flat receipt export with no sealed panel, so its
answer key is reconstructed from those identifiers; and a screen for response
tokens leaking into a certificate that was a malformed regular expression and
never fired (the released certificates contain none, checked after the fact).
Every later experiment fixes all five.

\textbf{Generalisation.} One task family, small models, synthetic panels.
Invented vocabularies establish item novelty, not independence from every
relevant pretraining pattern \citep{golchin2023time,deng2024investigating}, and
model is not randomised, so cross-model comparisons are descriptive. The
abstention rescoring changes the instruction and candidate set, and response
distributions move substantially \citep{zhao2021calibrate,zheng2023large}, so
its contrasts hold but its absolute rates do not. The reanalysis and the
validity control use a 4-bit checkpoint and the model sweep bfloat16, so they
describe different artefacts of one model, and the sweep found which models could
do the job before the validity control's checkpoints were chosen, which left
Phi-4-mini unrun on those arms. Every response is a forced choice among verified
single-token candidates, which no deployed solver-augmented setup does. At
$n = 96$ the loglinear correction censors $d'$ at $\pm 5.13$ and eight cells of
\cref{tab:arms} sit on it, so $d'$ differences involving a saturated arm are
bounds. The reanalysis's per-arm counts and primary contrast appeared in an
earlier unpublished report by the present authors, which concluded the 3B
checkpoint failed an open-world unknown gate where the sweep finds the family
viable; differing panels, candidate sets and quantisation plausibly explain it,
but we flag it rather than leave it to a reader who finds both. Finally, every
theory here arrives \emph{already formalised}: nothing tests whether a model can
turn a prose framework into solver input, which the corruption result makes
consequential.

\section{Conclusion}

End-to-end accuracy cannot say why solver assistance helps. The decomposition
can: arrange the arms so each contrast moves one factor, and break validity
while holding surface form fixed. Applied across twelve models, two inference
stacks and $NSCOREDRESPONSES$ responses, it returns a different answer almost
every time it is asked. The validity share is $98.3\%$ on one checkpoint and
$40.4$--$51.4\%$ on another; inference depth, order-sensitivity and viability
itself are properties of a checkpoint, an arm and a runtime. We offer the method
and decline to generalise its value, ours included.

One result does not move. Given a certificate whose fabricated final rule
establishes the negation, the three checkpoints answer incorrectly on $189$,
$186$ and $192$ of $192$, inheriting the apparatus's errors in full, and none
abstains on a broken certificate. Mechanism claims about solver assistance do
not transfer between checkpoints; the failure to check the solver does. Report
both, per checkpoint, and always run a corrupted arm. Report sensitivity beside
accuracy while doing it: two criteria we had prespecified were gamed by label
collapse, and a baseline arm at $50.0\%$ had $d' = 0.00$.

\section*{Reproducibility Statement}

\textbf{Code and data.} The supplementary material accompanying this submission
is self-contained: sealed panels and answer authorities, all $NSCOREDRESPONSES$
per-response receipts, the generators, runners, audits and analysis scripts, and
the forward-closure certifier with its validation against the public corpus.
Every number in this paper can be re-derived from a fresh unpack with no network
access, no model weights and no external packages; the audits use the Python standard
library only, so verification does not depend on resolving an
environment. Panels are hash-stamped, and the runners for the validity control and the model sweep refuse a panel
whose hash does not match, while the others record the hash without enforcing it.
The answer authority is opened after all receipts are written, by convention in
the analysis order rather than by a gate in the code. Scoring takes the
highest-likelihood candidate token; on an exact tie the first candidate in the
declared order wins, which across the validity control's $5{,}760$ prospective responses
occurs twice. Each receipt carries a SHA-256 of its own contents,
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
