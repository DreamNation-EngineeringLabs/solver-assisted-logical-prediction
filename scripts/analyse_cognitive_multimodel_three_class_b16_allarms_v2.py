#!/usr/bin/env python3
"""b16 v2 — all five arms, all ten models, plus the ten-model 2x2 replication.

Written in response to peer review. v1 reported `none` and `full` only, which
(a) withheld three arms that were run and (b) let a per-arm property be stated as
a per-model one: Qwen2.5-7B "collapses" under `full` but clears the viability
floor comfortably under `conclusion_only`. Viability is a property of
(model x arm).

It also folds in the replication the released data already contained: b16's five
arms ARE the answer-evidence x proof-state 2x2 plus a baseline, on ten models.
That turns the single-checkpoint decomposition of Experiment 1 into a ten-model
one at no additional compute.
"""
from __future__ import annotations

import argparse, collections, hashlib, json
from pathlib import Path
from typing import Any, Mapping

from cc_instruments import paired, sdt

VERSION = "multimodel-three-class-b16-analysis-v2-allarms"
DATA = Path("data/cognitive_core/multimodel_three_class_b16")
RUN = Path("runs/cognitive_core/multimodel_three_class_b16")
ARMS = ("none", "irrelevant", "conclusion_only", "proof_prefix", "full")
CLASSES = ("entailed", "contradicted", "undetermined")
LABEL = {"entailed": "Yes", "contradicted": "No", "undetermined": "Unknown"}
SEED = 2026090316


def _canon(v): return json.dumps(v, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
def _rows(p): return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    root = a.project.resolve()
    out = a.out or root / "results/b16_analysis_v2_allarms.json"

    panel = {r["task_id"]: r for r in _rows(root / DATA / "public/panel.jsonl")}
    models = sorted(p.parent.parent.name for p in (root / RUN).glob("*/control/complete.json"))
    chosen: dict[str, dict[str, dict[str, str]]] = {}
    for m in models:
        chosen[m] = {}
        for arm in ARMS:
            rows = _rows(root / RUN / m / f"receipts/prospective-{arm}.jsonl")
            for r in rows:
                body = {k: v for k, v in r.items() if k != "receipt_id"}
                if hashlib.sha256(_canon(body)).hexdigest() != r["receipt_id"]:
                    raise RuntimeError(f"{m}/{arm}: digest mismatch")
            chosen[m][arm] = {r["task_id"]: r["candidate"] for r in rows}

    auth = {r["task_id"]: r for r in _rows(root / DATA / "sealed/authority.jsonl")}
    truth = {t: LABEL[v["semantic_class"]] for t, v in auth.items()}
    cls = {t: v["semantic_class"] for t, v in auth.items()}
    ids = sorted(panel)
    by_class = {c: [t for t in ids if cls[t] == c] for c in CLASSES}

    res: dict[str, Any] = {"version": VERSION, "n": len(ids), "arms": list(ARMS),
                           "chance_balanced_accuracy": 1 / 3, "models": {}}

    for m in models:
        rec: dict[str, Any] = {"arms": {}}
        for arm in ARMS:
            pick = chosen[m][arm]
            recalls = {c: sum(1 for t in by_class[c] if pick[t] == LABEL[c]) / len(by_class[c]) for c in CLASSES}
            dist = {k: v / len(ids) for k, v in collections.Counter(pick[t] for t in ids).items()}
            rec["arms"][arm] = {
                "balanced_accuracy": sum(recalls.values()) / 3,
                "accuracy": sum(1 for t in ids if pick[t] == truth[t]) / len(ids),
                "per_class_recall": recalls,
                "min_per_class_recall": min(recalls.values()),
                "max_label_share": max(dist.values()),
                "response_distribution": dist,
                # the corrected criterion, now stated PER ARM
                "viable": min(recalls.values()) >= 0.50,
                "degenerate": max(dist.values()) >= 0.50,
            }
        rec["viable_in_arms"] = [x for x in ARMS if rec["arms"][x]["viable"]]
        rec["viable_any_arm"] = bool(rec["viable_in_arms"])
        rec["viable_under_full"] = rec["arms"]["full"]["viable"]
        # does supplying proof state HURT this model? (conclusion_only -> full)
        rec["state_harms_under_answer"] = (rec["arms"]["full"]["min_per_class_recall"]
                                           - rec["arms"]["conclusion_only"]["min_per_class_recall"])

        # ---- the 2x2, per model: answer evidence x proof state ---------------
        ba = {x: rec["arms"][x]["balanced_accuracy"] for x in ARMS}
        rec["factorial_2x2"] = {
            "cells": {"minus_answer_minus_state": ba["irrelevant"],
                      "plus_answer_minus_state": ba["conclusion_only"],
                      "minus_answer_plus_state": ba["proof_prefix"],
                      "plus_answer_plus_state": ba["full"],
                      "no_material": ba["none"]},
            "state_effect_without_answer": ba["proof_prefix"] - ba["irrelevant"],
            "state_effect_with_answer": ba["full"] - ba["conclusion_only"],
            "answer_effect_without_state": ba["conclusion_only"] - ba["irrelevant"],
            "answer_effect_with_state": ba["full"] - ba["proof_prefix"],
        }
        f = rec["factorial_2x2"]
        f["main_effect_state"] = (f["state_effect_without_answer"] + f["state_effect_with_answer"]) / 2
        f["main_effect_answer"] = (f["answer_effect_without_state"] + f["answer_effect_with_state"]) / 2
        f["interaction"] = f["answer_effect_with_state"] - f["answer_effect_without_state"]
        f["diagonal_proof_prefix_minus_conclusion_only"] = ba["proof_prefix"] - ba["conclusion_only"]

        corr = {x: {t: chosen[m][x][t] == truth[t] for t in ids} for x in ARMS}
        rec["paired_full_minus_conclusion_only"] = paired.contrast(corr["full"], corr["conclusion_only"], ids, SEED, resamples=20000)
        rec["paired_proof_prefix_minus_irrelevant"] = paired.contrast(corr["proof_prefix"], corr["irrelevant"], ids, SEED, resamples=20000)
        res["models"][m] = rec

    # ---- cross-model summary of the replication ------------------------------
    ms = list(res["models"])
    res["replication_summary"] = {
        "n_models": len(ms),
        "viable_under_full": sum(res["models"][m]["viable_under_full"] for m in ms),
        "viable_under_any_arm": sum(res["models"][m]["viable_any_arm"] for m in ms),
        "viable_under_conclusion_only": sum(res["models"][m]["arms"]["conclusion_only"]["viable"] for m in ms),
        "models_state_hurts": [m for m in ms if res["models"][m]["state_harms_under_answer"] < -0.10],
        "conclusion_only_beats_proof_prefix": sum(
            res["models"][m]["arms"]["conclusion_only"]["balanced_accuracy"]
            > res["models"][m]["arms"]["proof_prefix"]["balanced_accuracy"] for m in ms),
        "conclusion_only_at_least_full": sum(
            res["models"][m]["arms"]["conclusion_only"]["balanced_accuracy"]
            >= res["models"][m]["arms"]["full"]["balanced_accuracy"] for m in ms),
        "mean_main_effect_state": sum(res["models"][m]["factorial_2x2"]["main_effect_state"] for m in ms) / len(ms),
        "mean_main_effect_answer": sum(res["models"][m]["factorial_2x2"]["main_effect_answer"] for m in ms) / len(ms),
        "mean_interaction": sum(res["models"][m]["factorial_2x2"]["interaction"] for m in ms) / len(ms),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"written -> {out}")


if __name__ == "__main__":
    main()
