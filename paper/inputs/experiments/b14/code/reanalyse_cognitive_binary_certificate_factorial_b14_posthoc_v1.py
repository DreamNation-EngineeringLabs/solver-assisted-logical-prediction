#!/usr/bin/env python3
"""POST HOC reanalysis of the sealed b14 factorial as a 2x2 of answer evidence
x proof state.

This script does not re-run, re-score, or alter b14. It reads the exported raw
prospective receipts, reconstructs the answer authority from the class token
embedded in each task_id, and hard-asserts that the reconstruction reproduces
the five published per-arm counts before reporting anything.

Every quantity below is POST HOC with respect to the sealed b14 protocol. The
protocol prespecified one primary contrast (proof_prefix - conclusion_only) and
two Holm-adjusted secondaries. Nothing here may be presented as confirmatory.
Stdlib only, no model calls.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path
from statistics import NormalDist
from typing import Any, Mapping, Sequence

VERSION = "binary-certificate-factorial-b14-posthoc-reanalysis-v1"
ARMS = ("none", "irrelevant", "conclusion_only", "proof_prefix", "full")
PUBLISHED = {"none": 91, "irrelevant": 96, "conclusion_only": 176, "proof_prefix": 167, "full": 191}
CLASS_TO_ANSWER = {"entailed": "Yes", "contradicted": "No"}
BOOTSTRAP_SEED = 2026090134          # the b14 protocol seed
BOOTSTRAP_RESAMPLES = 100_000
NORM = NormalDist()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _rows(path: Path) -> list[Mapping[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _verify_digests(rows: Sequence[Mapping[str, Any]]) -> None:
    for row in rows:
        body = {k: v for k, v in row.items() if k != "receipt_id"}
        if hashlib.sha256(_canonical(body)).hexdigest() != row.get("receipt_id"):
            raise RuntimeError(f"receipt digest mismatch on {row.get('task_id')}/{row.get('arm')}")


def _exact_mcnemar(left_only: int, right_only: int) -> float:
    d = left_only + right_only
    if d == 0:
        return 1.0
    tail = sum(math.comb(d, k) for k in range(min(left_only, right_only) + 1))
    return min(1.0, 2.0 * tail / (2 ** d))


def _bca(diffs: Sequence[int], rng: random.Random) -> tuple[float, float]:
    """Seeded BCa interval for the mean of per-item paired differences in {-1,0,1}."""
    n = len(diffs)
    theta = sum(diffs) / n
    n_plus, n_minus = diffs.count(1), diffs.count(-1)
    p_plus, p_minus = n_plus / n, n_minus / n
    reps: list[float] = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        plus = rng.binomialvariate(n, p_plus)
        rest = n - plus
        minus = rng.binomialvariate(rest, p_minus / (1 - p_plus)) if rest and p_plus < 1 else 0
        reps.append((plus - minus) / n)
    reps.sort()
    below = sum(1 for r in reps if r < theta) / len(reps)
    if below <= 0 or below >= 1:                      # degenerate: fall back to percentile
        lo = reps[int(0.025 * (len(reps) - 1))]
        hi = reps[int(0.975 * (len(reps) - 1))]
        return lo, hi
    z0 = NORM.inv_cdf(below)
    # jackknife acceleration; theta_(i) = (n*theta - d_i)/(n-1)
    jack = [(n * theta - d) / (n - 1) for d in diffs]
    jbar = sum(jack) / n
    num = sum((jbar - j) ** 3 for j in jack)
    den = 6.0 * (sum((jbar - j) ** 2 for j in jack) ** 1.5)
    a = num / den if den else 0.0
    out: list[float] = []
    for q in (0.025, 0.975):
        z = NORM.inv_cdf(q)
        adj = z0 + (z0 + z) / (1 - a * (z0 + z))
        idx = min(max(int(NORM.cdf(adj) * (len(reps) - 1)), 0), len(reps) - 1)
        out.append(reps[idx])
    return out[0], out[1]


def _contrast(left: str, right: str, correct: Mapping[str, Mapping[str, bool]],
              ids: Sequence[str], rng: random.Random) -> Mapping[str, Any]:
    both = lo = ro = neither = 0
    diffs: list[int] = []
    for t in ids:
        l, r = correct[left][t], correct[right][t]
        if l and r:
            both += 1; diffs.append(0)
        elif l:
            lo += 1; diffs.append(1)
        elif r:
            ro += 1; diffs.append(-1)
        else:
            neither += 1; diffs.append(0)
    ci = _bca(diffs, rng)
    return {
        "left": left, "right": right,
        "left_correct": both + lo, "right_correct": both + ro,
        "paired_table": {"both_correct": both, "left_only_correct": lo,
                         "right_only_correct": ro, "neither_correct": neither},
        "paired_risk_difference": (lo - ro) / len(ids),
        "exact_two_sided_mcnemar_p": _exact_mcnemar(lo, ro),
        "bca_95": [round(ci[0], 6), round(ci[1], 6)],
    }


def _holm(pvals: Mapping[str, float]) -> Mapping[str, float]:
    ordered = sorted(pvals.items(), key=lambda kv: kv[1])
    m, out, running = len(ordered), {}, 0.0
    for i, (k, p) in enumerate(ordered):
        running = max(running, min(1.0, (m - i) * p))
        out[k] = running
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Post hoc 2x2 reanalysis of sealed b14 receipts.")
    ap.add_argument("--receipts", type=Path,
                    default=Path("results/b14_raw_model_calls_960.jsonl"))
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    rows = _rows(args.receipts)
    if len(rows) != 960:
        raise RuntimeError(f"expected 960 receipts, found {len(rows)}")
    _verify_digests(rows)
    if {r["stage"] for r in rows} != {"prospective"} or any(r["raw_generation_used"] for r in rows):
        raise RuntimeError("receipts are not the pure prospective direct-likelihood set")

    ids = sorted({str(r["task_id"]) for r in rows})
    if len(ids) != 192:
        raise RuntimeError(f"expected 192 items, found {len(ids)}")
    authority = {t: CLASS_TO_ANSWER[t.split("-")[2]] for t in ids}

    chosen: dict[str, dict[str, str]] = {a: {} for a in ARMS}
    for r in rows:
        chosen[str(r["arm"])][str(r["task_id"])] = str(r["candidate"])
    for arm in ARMS:
        if set(chosen[arm]) != set(ids):
            raise RuntimeError(f"{arm} does not cover all 192 items")

    correct = {a: {t: chosen[a][t] == authority[t] for t in ids} for a in ARMS}
    counts = {a: sum(correct[a].values()) for a in ARMS}
    if counts != PUBLISHED:
        raise RuntimeError(f"reconstructed authority does not reproduce published counts: {counts}")

    rng = random.Random(BOOTSTRAP_SEED)
    pairs = [(l, r) for i, l in enumerate(ARMS) for r in ARMS[i + 1:]]
    contrasts = {f"{l}__minus__{r}": _contrast(l, r, correct, ids, rng) for l, r in pairs}

    # 2x2 of answer evidence x proof state; `irrelevant` is the empty cell.
    cell = {"answer_no_state": counts["irrelevant"], "answer_yes_state_no": counts["conclusion_only"],
            "state_yes_answer_no": counts["proof_prefix"], "both": counts["full"]}
    n = len(ids)
    factorial = {
        "cells": {"minus_answer_minus_state": counts["irrelevant"],
                  "plus_answer_minus_state": counts["conclusion_only"],
                  "minus_answer_plus_state": counts["proof_prefix"],
                  "plus_answer_plus_state": counts["full"],
                  "no_material_baseline": counts["none"]},
        "edges": {
            "state_effect_without_answer": (counts["proof_prefix"] - counts["irrelevant"]) / n,
            "state_effect_with_answer": (counts["full"] - counts["conclusion_only"]) / n,
            "answer_effect_without_state": (counts["conclusion_only"] - counts["irrelevant"]) / n,
            "answer_effect_with_state": (counts["full"] - counts["proof_prefix"]) / n,
        },
        "diagonal_prespecified_primary": (counts["proof_prefix"] - counts["conclusion_only"]) / n,
    }
    factorial["main_effect_state"] = (factorial["edges"]["state_effect_without_answer"]
                                     + factorial["edges"]["state_effect_with_answer"]) / 2
    factorial["main_effect_answer"] = (factorial["edges"]["answer_effect_without_state"]
                                      + factorial["edges"]["answer_effect_with_state"]) / 2
    factorial["interaction"] = ((counts["full"] - counts["proof_prefix"])
                               - (counts["conclusion_only"] - counts["irrelevant"])) / n
    aw, an = counts["full"] - counts["proof_prefix"], counts["conclusion_only"] - counts["irrelevant"]
    factorial["answer_value_retained_when_state_present"] = aw / an
    sw = counts["full"] - counts["conclusion_only"]
    factorial["state_value_retained_when_answer_present"] = sw / (counts["proof_prefix"] - counts["irrelevant"])

    # class stratification (descriptive)
    strata = {}
    for cls in ("entailed", "contradicted"):
        sub = [t for t in ids if t.split("-")[2] == cls]
        strata[cls] = {"n": len(sub), **{a: sum(correct[a][t] for t in sub) for a in ARMS}}

    # Signal detection decomposition. Accuracy on a balanced panel conflates
    # discriminative sensitivity with response bias; d' and criterion separate them.
    # Loglinear (x+0.5)/(n+1) correction handles the 0/96 false-alarm cells.
    sdt: dict[str, Any] = {}
    ent = [t for t in ids if t.split("-")[2] == "entailed"]
    con = [t for t in ids if t.split("-")[2] == "contradicted"]
    for arm in ARMS:
        hits = sum(1 for t in ent if chosen[arm][t] == "Yes")
        fas = sum(1 for t in con if chosen[arm][t] == "Yes")
        h = (hits + 0.5) / (len(ent) + 1)
        f = (fas + 0.5) / (len(con) + 1)
        zh, zf = NORM.inv_cdf(h), NORM.inv_cdf(f)
        sdt[arm] = {"hits": hits, "n_signal": len(ent), "false_alarms": fas,
                    "n_noise": len(con), "hit_rate": hits / len(ent),
                    "false_alarm_rate": fas / len(con), "d_prime": zh - zf,
                    "criterion_c": -0.5 * (zh + zf),
                    "yes_rate_overall": sum(1 for t in ids if chosen[arm][t] == "Yes") / n}
    always_no = sum(1 for t in ids if authority[t] == "No")
    sdt["_trivial_always_no_baseline"] = {"correct": always_no, "accuracy": always_no / n}

    # decision-margin descriptives from the raw candidate scores
    margins: dict[str, Any] = {}
    for arm in ARMS:
        vals = sorted(float(r["top_two_margin"]) for r in rows if r["arm"] == arm)
        margins[arm] = {"median": vals[len(vals) // 2],
                        "mean": sum(vals) / len(vals),
                        "min": vals[0], "max": vals[-1]}

    holm_family = {k: contrasts[k]["exact_two_sided_mcnemar_p"] for k in (
        "irrelevant__minus__proof_prefix", "conclusion_only__minus__full",
        "irrelevant__minus__conclusion_only", "proof_prefix__minus__full")}
    report = {
        "version": VERSION,
        "status": "post_hoc_reanalysis_of_sealed_b14_no_model_calls",
        "analysis_class": "POST HOC - not prespecified in the b14 protocol",
        "n": n,
        "authority_source": "reconstructed from task_id class token; validated against published per-arm counts",
        "per_arm_correct": counts,
        "factorial_2x2": factorial,
        "contrasts_all_pairs": contrasts,
        "holm_adjusted_edge_family": _holm(holm_family),
        "class_strata": strata,
        "signal_detection": sdt,
        "top_two_margin": margins,
        "bootstrap": {"seed": BOOTSTRAP_SEED, "resamples": BOOTSTRAP_RESAMPLES, "method": "paired BCa"},
    }
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
