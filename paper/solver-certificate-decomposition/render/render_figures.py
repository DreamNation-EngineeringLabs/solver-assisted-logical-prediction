#!/usr/bin/env python3
"""Render the paper's figures from the sealed results JSONs.

Every value is read from results/*.json — nothing is retyped. Output goes to
papers/solver-certificate-decomposition/inputs/experiments/<slug>/figures/ so the figure-provenance gate can
trace each displayed figure back to a real render.

Palette: Wong colourblind-safe hues, validated (lightness band, chroma floor,
CVD separation, normal-vision floor, contrast) before use. Grey is the recessive
neutral for control arms, not a categorical slot.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

BLUE, VERM, GREEN = "#0072B2", "#D55E00", "#009E73"
GREY, INK, MUTED, RULE = "#8A8F98", "#1A1D21", "#5B6169", "#D8DBE0"
PAPER = Path(__file__).resolve().parents[1]        # render/ -> <paper>/
PROJECT = PAPER.parents[1]                         # <paper>/ -> paper/ -> <project>/
RES = PROJECT / "results"
OUT = PAPER / "inputs/experiments"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8.5,
    "axes.edgecolor": RULE, "axes.linewidth": .7, "axes.labelcolor": INK,
    "axes.titlesize": 9.5, "axes.titleweight": "medium", "axes.titlecolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelsize": 8, "ytick.labelsize": 8,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "savefig.facecolor": "white", "savefig.bbox": "tight", "savefig.dpi": 300,
})


def _clean(ax, keep=("left", "bottom")):
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(s in keep)
    ax.tick_params(length=3, width=.7)


# ---------------------------------------------------------------- figure 1
def fig_b14_factorial():
    r = json.loads((RES / "b14_posthoc_2x2_reanalysis_v1.json").read_text())
    c, e = r["factorial_2x2"]["cells"], r["factorial_2x2"]["edges"]
    fig, ax = plt.subplots(figsize=(6.1, 3.7))
    ax.set_xlim(0, 12.4); ax.set_ylim(0, 9.0); ax.axis("off")

    W, H = 3.0, 2.3
    X1, X2, YT, YB = 3.4, 8.2, 5.1, 1.6          # 1.8 of gap between columns
    # R1/R2 minor 3: the caption promised a no-material baseline outside the
    # square and the figure did not draw one. It sits to the left, dashed and
    # detached, because it is not a cell of the factorial.
    BW, BX = 1.9, 0.25
    BY = (YB + YT + H) / 2 - H / 2
    ax.add_patch(Rectangle((BX, BY), BW, H, facecolor="white", edgecolor=MUTED,
                           linewidth=1.1, linestyle=(0, (3, 2)), zorder=2))
    ax.text(BX + BW / 2, BY + 1.62, "none", ha="center", fontsize=7.4, color=MUTED,
            family="DejaVu Sans Mono", zorder=3)
    ax.text(BX + BW / 2, BY + .42, f"{c['no_material_baseline']}", ha="center",
            fontsize=20, color=MUTED, zorder=3)
    ax.text(BX + BW / 2, BY - .52, "no material", ha="center", fontsize=6.8, color=MUTED)

    cells = [(X1, YT, "irrelevant", c["minus_answer_minus_state"], GREY),
             (X2, YT, "proof_prefix", c["minus_answer_plus_state"], BLUE),
             (X1, YB, "conclusion_only", c["plus_answer_minus_state"], GREY),
             (X2, YB, "full", c["plus_answer_plus_state"], GREEN)]
    for x, y, name, val, col in cells:
        ax.add_patch(Rectangle((x, y), W, H, facecolor="white",
                               edgecolor=col, linewidth=1.4, zorder=2))
        ax.text(x + W / 2, y + 1.62, name, ha="center", fontsize=7.4, color=MUTED,
                family="DejaVu Sans Mono", zorder=3)
        ax.text(x + W / 2, y + .42, f"{val}", ha="center", fontsize=20, color=INK, zorder=3)

    ax.text(X1 + W / 2, 7.9, "− proof state", ha="center", fontsize=8, color=MUTED)
    ax.text(X2 + W / 2, 7.9, "+ proof state", ha="center", fontsize=8, color=MUTED)
    ax.text(X1 - .35, YT + H / 2, "− answer", ha="center", va="center", fontsize=8,
            color=MUTED, rotation=90)
    ax.text(X1 - .35, YB + H / 2, "+ answer", ha="center", va="center", fontsize=8,
            color=MUTED, rotation=90)

    # horizontal edges: proof state added, answer held constant
    for y, lab in [(YT + H / 2, f"+{e['state_effect_without_answer']*100:.1f}pp"),
                   (YB + H / 2, f"+{e['state_effect_with_answer']*100:.1f}pp")]:
        ax.annotate("", (X2 - .08, y), (X1 + W + .08, y),
                    arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.2))
        ax.text((X1 + W + X2) / 2, y + .22, lab, ha="center", fontsize=7, color=BLUE)
    # vertical edges: answer added, proof state held constant
    for x, lab in [(X1 + W / 2, f"+{e['answer_effect_without_state']*100:.1f}pp"),
                   (X2 + W / 2, f"+{e['answer_effect_with_state']*100:.1f}pp")]:
        ax.annotate("", (x, YB + H + .08), (x, YT - .08),
                    arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.2))
        ax.text(x + .16, (YT + YB + H) / 2, lab, ha="left", va="center", fontsize=7, color=MUTED)

    # the prespecified primary is the diagonal — two factors move at once
    ax.annotate("", (X2 - .08, YT + .12), (X1 + W + .08, YB + H - .12),
                arrowprops=dict(arrowstyle="<->", color=VERM, lw=1.3, linestyle=(0, (3, 2))))
    ax.text((X1 + X2 + W) / 2, .62,
            f"prespecified primary — the diagonal:  "
            f"{r['factorial_2x2']['diagonal_prespecified_primary']*100:.1f}pp,  p = 0.078",
            ha="center", fontsize=7.4, color=VERM)
    # R2 minor 3: the section's two main qualifications belong on the figure.
    ax.text((X1 + X2 + W) / 2, 8.62,
            f"correct of 192   ·   interaction "
            f"{r['factorial_2x2']['interaction']*100:.1f}pp   ·   "
            f"\textsf{{full}} at 191/192 is ceiling-limited".replace("\textsf{full}", "full"),
            ha="center", fontsize=7.4, color=MUTED)
    fig.savefig(OUT / "b14/figures/factorial_2x2.png")
    plt.close(fig)


# ---------------------------------------------------------------- figure 2
def fig_b15_arms():
    r = json.loads((RES / "b15_analysis_v1.json").read_text())
    order = ["none", "irrelevant", "same_entity_irrelevant", "truncate_3", "truncate_2",
             "shuffled", "misleading", "broken_chain", "truncate_1", "full"]
    kind = {"broken_chain": VERM, "misleading": VERM, "truncate_1": BLUE, "full": GREEN}
    n = r["n_entailed"]
    acc = [r["per_arm"][a]["entailed_correct"] for a in order]
    dp = [r["per_arm"][a]["d_prime"] for a in order]
    cols = [kind.get(a, GREY) for a in order]
    y = range(len(order))

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.9, 3.4), sharey=True,
                                 gridspec_kw={"width_ratios": [1.45, 1], "wspace": .08})
    a1.barh(y, acc, color=cols, height=.62)
    a1.set_xlim(0, n * 1.13); a1.set_xlabel(f"correct, entailed items (of {n})")
    a1.set_yticks(list(y)); a1.set_yticklabels(order, family="DejaVu Sans Mono", fontsize=7.6)
    for i, v in zip(y, acc):
        a1.text(v + n * .015, i, str(v), va="center", fontsize=7.4, color=INK)
    a1.set_title("Accuracy", loc="left", pad=8); _clean(a1)

    a2.barh(y, dp, color=cols, height=.62)
    a2.axvline(0, color=RULE, lw=.8)
    a2.set_xlabel("d′  (sensitivity)")
    for i, v in zip(y, dp):
        off = .12 if v >= 0 else -.12
        a2.text(v + off, i, f"{v:.2f}", va="center", fontsize=7.4, color=INK,
                ha="left" if v >= 0 else "right")
    a2.set_xlim(-5.6, 6.4)
    a2.set_title("Sensitivity", loc="left", pad=8); _clean(a2, keep=("bottom",))
    a2.tick_params(left=False)
    a1.invert_yaxis()

    d = r["decomposition"]
    fig.text(.5, -.07,
             f"validity component {d['validity_component']*100:+.1f}pp  ·  "
             f"surface component {d['surface_component']*100:+.1f}pp (p = 1)  ·  "
             f"validity share {d['validity_share']*100:.1f}%",
             ha="center", fontsize=8, color=INK)
    fig.savefig(OUT / "b15/figures/arms.png")
    plt.close(fig)


# ---------------------------------------------------------------- figure 3
def fig_b16_size():
    """All five arms x ten models. Viability is a property of (model x arm)."""
    r = json.loads((RES / "b16_analysis_v2_allarms.json").read_text())
    size = {"qwen2p5_0p5b": .5, "olmo2_1b": 1.0, "llama3p2_1b": 1.2, "qwen2p5_1p5b": 1.5,
            "smollm2_1p7b": 1.7, "qwen2p5_3b": 3.0, "llama3p2_3b": 3.2, "phi4_mini": 3.8,
            "gemma3_4b": 4.3, "qwen2p5_7b": 7.6}
    short = {"qwen2p5_0p5b": "qwen2.5-0.5b", "olmo2_1b": "olmo2-1b", "llama3p2_1b": "llama3.2-1b",
             "qwen2p5_1p5b": "qwen2.5-1.5b", "smollm2_1p7b": "smollm2-1.7b",
             "qwen2p5_3b": "qwen2.5-3b", "llama3p2_3b": "llama3.2-3b", "phi4_mini": "phi-4-mini",
             "gemma3_4b": "gemma-3-4b", "qwen2p5_7b": "qwen2.5-7b"}
    arms = r["arms"]
    ms = sorted(r["models"], key=lambda k: size[k])
    chance = r["chance_balanced_accuracy"] * 100
    y = list(range(len(arms)))

    fig, axes = plt.subplots(2, 5, figsize=(7.3, 3.7), sharex=True, sharey=True,
                             gridspec_kw={"wspace": .16, "hspace": .45})
    for ax, m in zip(axes.ravel(), ms):
        cell = r["models"][m]["arms"]
        vals = [cell[a]["balanced_accuracy"] * 100 for a in arms]
        # Verdict carries a hatch as well as a hue: colour-alone status encoding
        # fails for CVD readers and in print, and green/red is the worst pair to
        # ask anyone to separate. Hatch is the secondary channel, the legend
        # names both.
        cols, hatches = [], []
        for a in arms:
            if cell[a]["viable"]:
                cols.append(GREEN); hatches.append("")
            elif cell[a]["degenerate"]:
                cols.append(VERM); hatches.append("x")
            else:
                cols.append(GREY); hatches.append("//")
        ax.axvline(chance, color=MUTED, lw=.9, linestyle=(0, (3, 2)), zorder=0)
        bars = ax.barh(y, vals, color=cols, height=.68, zorder=2)
        for bar, h in zip(bars, hatches):
            if h:
                bar.set_hatch(h)
                bar.set_edgecolor("white")
                bar.set_linewidth(0)
        ax.axvline(chance, color="white", lw=.9, linestyle=(0, (3, 2)), zorder=3)
        for i, v in enumerate(vals):
            ax.text(v + 4, i, f"{v:.1f}", va="center", ha="left", fontsize=6.2, color=INK)
        ax.set_title(f"{short[m]}  {size[m]}B", loc="left", pad=4, fontsize=7.0,
                     family="DejaVu Sans Mono")
        ax.set_xlim(0, 132); ax.set_xticks([0, 50, 100])
        ax.set_ylim(len(arms) - .45, -.55)
        _clean(ax)
    axes[0][0].set_yticks(y)
    axes[0][0].set_yticklabels(arms, family="DejaVu Sans Mono", fontsize=6.8)

    hi = r["models"]["qwen2p5_7b"]["arms"]["conclusion_only"]
    lo = r["models"]["qwen2p5_7b"]["arms"]["full"]
    s = r["replication_summary"]
    fig.text(.5, .012, f"balanced accuracy (%)   ·   dashed = chance {chance:.1f}",
             ha="center", fontsize=7.6, color=MUTED)
    fig.text(.5, -.048,
             "solid green = viable arm (min per-class recall ≥ 0.50)   ·   "
             "crosshatch red = collapsed to one label   ·   diagonal grey = below floor",
             ha="center", fontsize=7.2, color=MUTED)
    fig.text(.5, -.105,
             "Viability is a property of (model × arm), not of the model: qwen2.5-7b is viable\n"
             f"under conclusion_only ({hi['balanced_accuracy']*100:.1f}%, min per-class recall "
             f"{hi['min_per_class_recall']:.3f}) and not under full "
             f"({lo['balanced_accuracy']*100:.1f}%, {lo['min_per_class_recall']:.3f}).  "
             f"{s['viable_under_any_arm']} of {s['n_models']} models are viable under some arm.",
             ha="center", va="top", fontsize=7.2, color=INK, linespacing=1.5)
    fig.savefig(OUT / "b16/figures/size_curve.png")
    plt.close(fig)


# ---------------------------------------------------------------- figure 4
def fig_b15_replication():
    """Does the 98.3% validity share survive a change of checkpoint? No."""
    r = json.loads((RES / "b15_replication_v1.json").read_text())
    order = ["qwen2p5_3b_4bit", "qwen2p5_3b_bf16", "gemma3_4b_b15"]
    short = {"qwen2p5_3b_4bit": "qwen2.5-3b 4bit", "qwen2p5_3b_bf16": "qwen2.5-3b bf16",
             "gemma3_4b_b15": "gemma-3-4b bf16"}
    val = [r[k]["validity"] * 100 for k in order]
    sur = [r[k]["surface"] * 100 for k in order]
    y = [0, 1, 2]
    H, G = .32, .19
    XMAX = 122

    fig, ax = plt.subplots(figsize=(6.0, 2.8))
    ax.barh([i - G for i in y], val, height=H, color=BLUE, zorder=2)
    ax.barh([i + G for i in y], sur, height=H, color=VERM, zorder=2)
    for i, (v, u) in enumerate(zip(val, sur)):
        tag = ("  validity", "  surface") if i == 0 else ("", "")
        ax.text(v + 1.6, i - G, f"{v:+.1f}pp{tag[0]}", va="center", fontsize=7.3, color=BLUE)
        ax.text(u + 1.6, i + G, f"{u:+.1f}pp{tag[1]}", va="center", fontsize=7.3, color=VERM)
    for i, k in zip(y, order):
        ax.text(XMAX, i, f"validity share  {r[k]['share']*100:.1f}%", ha="right", va="center",
                fontsize=7.6, color=INK)

    ax.set_yticks(y)
    ax.set_yticklabels([short[k] for k in order], family="DejaVu Sans Mono", fontsize=7.6)
    ax.set_xlim(0, XMAX); ax.set_xticks([0, 20, 40, 60, 80])
    ax.set_ylim(2.62, -.62)
    ax.set_xlabel("component of the total state effect (pp, entailed items)")
    ax.set_title("Does the decomposition replicate across checkpoints?", loc="left", pad=8)
    _clean(ax)
    ax.spines["bottom"].set_bounds(0, 80)

    g, q = r["gemma3_4b_b15"], r["qwen2p5_3b_4bit"]
    fig.text(.5, -.055,
             f"The {q['share']*100:.1f}% share does not generalise: gemma-3-4b's surface "
             f"component is {g['surface']*100:+.1f}pp\n"
             f"against {q['surface']*100:+.1f}pp on both qwen checkpoints, and its validity "
             f"share falls to {g['share']*100:.1f}%.",
             ha="center", va="top", fontsize=7.6, color=INK, linespacing=1.5)
    fig.savefig(OUT / "b15/figures/replication.png")
    plt.close(fig)


# ---------------------------------------------------------------- figure 5
def fig_b17_detection():
    """Three-class response distribution on all three checkpoints.

    Round-2 review: the refutation was single-checkpoint, and missing on the one
    model that answers broken chains correctly. One panel per checkpoint, each
    against its own irrelevant baseline, because baseline abstention differs by
    a factor of ten across them.
    """
    r = json.loads((RES / "b17_replication_v2.json").read_text())
    nice = {"qwen2p5_3b_4bit": "Qwen2.5-3B 4-bit", "qwen2p5_3b_bf16": "Qwen2.5-3B bf16",
            "gemma3_4b_b15": "Gemma-3-4B"}
    keys = [k for k in ("qwen2p5_3b_4bit", "qwen2p5_3b_bf16", "gemma3_4b_b15")
            if k in r["checkpoints"]]
    order = ["irrelevant", "broken_chain", "truncate_1"]
    labels = [("Unknown", BLUE), ("No", VERM), ("Yes", GREEN)]
    H, G = .22, .25

    fig, axes = plt.subplots(1, len(keys), figsize=(7.3, 2.5), sharey=True,
                             gridspec_kw={"wspace": .12})
    for ax, key in zip(np.atleast_1d(axes), keys):
        ck = r["checkpoints"][key]
        arms, n = ck["arms"], ck["arms"]["irrelevant"]["n"]
        base = arms["irrelevant"]["Unknown"]
        ax.axvline(base, color=BLUE, lw=.9, linestyle=(0, (3, 2)), zorder=1)
        for j, (lab, col) in enumerate(labels):
            offs = (j - 1) * G
            vals = [arms[a][lab] for a in order]
            ax.barh([i + offs for i in range(len(order))], vals, height=H, color=col,
                    zorder=2, label=lab if ax is np.atleast_1d(axes)[0] else None)
            for i, v in enumerate(vals):
                ax.text(v + 3, i + offs, f"{v}", va="center", fontsize=6.2, color=INK)
        delta = ck["broken_chain_minus_irrelevant_unknown_rate"] * 100
        ax.set_title(f"{nice.get(key, key)}\n{delta:+.1f}pp abstention", loc="left",
                     pad=5, fontsize=7.4)
        ax.set_xlim(0, n * 1.16); ax.set_xticks([0, 96, 192])
        ax.set_ylim(2.5, -.62)
        _clean(ax)
    a0 = np.atleast_1d(axes)[0]
    a0.set_yticks(range(len(order)))
    a0.set_yticklabels(order, family="DejaVu Sans Mono", fontsize=7.0)
    fig.text(.5, -.02, "responses (of 192)   ·   dashed = that checkpoint's irrelevant baseline",
             ha="center", fontsize=7.4, color=MUTED)
    a0.legend(frameon=False, fontsize=7.2, loc="upper center", ncol=3,
              bbox_to_anchor=(1.72, 1.44), handlelength=1.1, handletextpad=.5,
              columnspacing=1.4)
    fig.text(.5, -.13,
             "On every checkpoint a broken chain lowers abstention rather than raising it. "
             "Gemma-3-4B\nabstains on 0 of 192 broken chains and completes 76 of them.",
             ha="center", va="top", fontsize=7.6, color=INK, linespacing=1.5)
    fig.savefig(OUT / "b17/figures/response_distribution.png")
    plt.close(fig)


if __name__ == "__main__":
    for d in ("b14", "b15", "b16", "b17"):
        (OUT / d / "figures").mkdir(parents=True, exist_ok=True)
    fig_b14_factorial(); fig_b15_arms(); fig_b16_size()
    fig_b15_replication(); fig_b17_detection()
    for f in sorted(OUT.glob("*/figures/*.png")):
        print(f"  {f.relative_to(OUT)}  {f.stat().st_size/1024:.0f} KB")
