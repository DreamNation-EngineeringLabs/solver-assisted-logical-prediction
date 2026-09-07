#!/usr/bin/env python3
"""The ten-model 2x2, with and without the degenerate responders.

Peer review, round 2: the cross-model mean state main effect (+8.7pp) averages
over four models whose minimum per-class recall is 0.000 in EVERY arm. Those
models emit one or two labels regardless of what the apparatus supplies, so
their per-arm balanced accuracies are artefacts of the panel's class balance,
not measurements of an interface. Three of them carry negative state effects,
which drag the mean.

Excluding them the mean state effect is +14.7pp, so the manuscript's claim that
the cross-model mean is "less than half" b14's single-model +22.4pp does not
hold and is removed. The qualitative point is unaffected and is what the paper
now states: the answer channel dominates the state channel either way.
"""
from __future__ import annotations

import argparse, json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description="Ten-model 2x2 with degenerate responders excluded.")
    ap.add_argument("--project", type=Path, default=Path("."))
    root = ap.parse_args().project.resolve()

    src = json.loads((root / "results/b16_analysis_v2_allarms.json").read_text())
    rows = {}
    for model, md in src["models"].items():
        arms = md["arms"]
        ba = {k: arms[k]["balanced_accuracy"] for k in arms}
        rows[model] = {
            # main effects of the 2x2: answer evidence x proof state
            "state_main_effect": ((ba["proof_prefix"] - ba["irrelevant"])
                                  + (ba["full"] - ba["conclusion_only"])) / 2,
            "answer_main_effect": ((ba["conclusion_only"] - ba["irrelevant"])
                                   + (ba["full"] - ba["proof_prefix"])) / 2,
            # degenerate: never discriminates a class, in any arm
            "degenerate_in_every_arm": all(arms[k]["min_per_class_recall"] == 0.0 for k in arms),
        }

    def mean(keys, field):
        return sum(rows[k][field] for k in keys) / len(keys)

    every = sorted(rows)
    live = sorted(k for k in rows if not rows[k]["degenerate_in_every_arm"])
    dead = sorted(k for k in rows if rows[k]["degenerate_in_every_arm"])

    out = {
        "version": "b16-state-effect-v3-degenerate-exclusion",
        "b14_single_model_state_main_effect": 0.224,
        "per_model": rows,
        "degenerate_models": dead,
        "all_models": {"n": len(every), "mean_state": mean(every, "state_main_effect"),
                       "mean_answer": mean(every, "answer_main_effect")},
        "excluding_degenerate": {"n": len(live), "mean_state": mean(live, "state_main_effect"),
                                 "mean_answer": mean(live, "answer_main_effect")},
        "answer_beats_state_count": sum(
            rows[k]["answer_main_effect"] > rows[k]["state_main_effect"] for k in every),
    }
    out["interpretation"] = (
        f"Across all {len(every)} models the mean state main effect is "
        f"{out['all_models']['mean_state']*100:+.1f}pp; excluding the {len(dead)} responders that "
        f"never discriminate a class in any arm it is {out['excluding_degenerate']['mean_state']*100:+.1f}pp, "
        f"against b14's single-model +22.4pp. The 'less than half' comparison therefore holds only "
        f"with the degenerate responders included and is not made. What holds on both subsets is "
        f"that the answer channel exceeds the state channel: "
        f"{out['excluding_degenerate']['mean_answer']*100:+.1f}pp against "
        f"{out['excluding_degenerate']['mean_state']*100:+.1f}pp on the non-degenerate models, and "
        f"in {out['answer_beats_state_count']} of {len(every)} models individually.")
    path = root / "results/b16_state_effect_v3.json"
    path.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("all_models", "excluding_degenerate",
                                          "degenerate_models", "answer_beats_state_count")}, indent=1))
    print(out["interpretation"])


if __name__ == "__main__":
    main()
