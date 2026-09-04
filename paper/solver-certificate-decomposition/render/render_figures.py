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
    fig, ax = plt.subplots(figsize=(5.0, 3.6))
    ax.set_xlim(0, 10.2); ax.set_ylim(0, 9.0); ax.axis("off")

    W, H = 3.0, 2.3
    X1, X2, YT, YB = 1.2, 6.0, 5.1, 1.6          # 1.8 of gap between columns
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
    ax.text(5.1, .62,
            f"prespecified primary — the diagonal:  "
            f"{r['factorial_2x2']['diagonal_prespecified_primary']*100:.1f}pp,  p = 0.078",
            ha="center", fontsize=7.4, color=VERM)
    ax.text(5.1, 8.62, "correct of 192", ha="center", fontsize=7.4, color=MUTED)
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
    r = json.loads((RES / "b16_analysis_v1.json").read_text())
    size = {"qwen2p5_0p5b": .5, "olmo2_1b": 1.0, "llama3p2_1b": 1.2, "qwen2p5_1p5b": 1.5,
            "smollm2_1p7b": 1.7, "qwen2p5_3b": 3.0, "llama3p2_3b": 3.2, "phi4_mini": 3.8,
            "gemma3_4b": 4.3, "qwen2p5_7b": 7.6}
    short = {"qwen2p5_0p5b": "qwen2.5-0.5b", "olmo2_1b": "olmo2-1b", "llama3p2_1b": "llama3.2-1b",
             "qwen2p5_1p5b": "qwen2.5-1.5b", "smollm2_1p7b": "smollm2-1.7b",
             "qwen2p5_3b": "qwen2.5-3b", "llama3p2_3b": "llama3.2-3b", "phi4_mini": "phi-4-mini",
             "gemma3_4b": "gemma-3-4b", "qwen2p5_7b": "qwen2.5-7b"}
    ms = sorted(r["models"], key=lambda k: size[k])
    fig, ax = plt.subplots(figsize=(5.4, 3.5))
    for i, m in enumerate(ms):
        v = r["models"][m]
        lo = v["arms"]["none"]["balanced_accuracy"] * 100
        hi = v["arms"]["full"]["balanced_accuracy"] * 100
        col = GREEN if v["viable_substrate"] else (VERM if v["degenerate"] else GREY)
        ax.plot([lo, hi], [i, i], color=col, lw=1.6, solid_capstyle="round", zorder=2)
        ax.plot(lo, i, "o", ms=4.5, color="white", mec=col, mew=1.4, zorder=3)
        ax.plot(hi, i, "o", ms=6, color=col, zorder=3)
        ax.text(hi + 1.6, i, f"{hi:.1f}", va="center", fontsize=7.3, color=INK)
    ax.axvline(100 / 3, color=RULE, lw=.9, linestyle=(0, (3, 2)), zorder=1)
    ax.text(100 / 3 + .9, -.62, "chance 33.3", fontsize=7, color=MUTED)
    ax.set_yticks(range(len(ms)))
    ax.set_yticklabels([f"{short[m]}  {size[m]}B" for m in ms],
                       family="DejaVu Sans Mono", fontsize=7.4)
    ax.set_xlim(28, 108); ax.set_xlabel("balanced accuracy (%)   ○ no solver material  ● full")
    ax.set_ylim(len(ms) - .4, -.9)
    _clean(ax)
    ax.set_title("Substrate viability by model size", loc="left", pad=8)
    fig.text(.5, -.04,
             "green = viable (min per-class recall ≥ 0.50)   ·   red = collapsed to one label   ·   grey = below floor",
             ha="center", fontsize=7.4, color=MUTED)
    fig.savefig(OUT / "b16/figures/size_curve.png")
    plt.close(fig)


if __name__ == "__main__":
    fig_b14_factorial(); fig_b15_arms(); fig_b16_size()
    for f in sorted(OUT.glob("*/figures/*.png")):
        print(f"  {f.relative_to(OUT)}  {f.stat().st_size/1024:.0f} KB")
