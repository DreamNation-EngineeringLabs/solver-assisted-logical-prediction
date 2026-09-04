#!/usr/bin/env python3
"""Score the sealed b16 sweep. Opens the authority; makes no model calls.

Hard precondition: all 50 receipt files must exist, cover the panel exactly, and
carry valid digests. The authority is not read until that passes.

Accuracy is never reported alone. b14's `irrelevant` arm scored 50.0% with
d' = 0.00, so a balanced panel plus a biased responder looks like competence.
Headline scalar is balanced accuracy (mean per-class recall, 33.3% = chance).
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from cc_instruments import paired, sdt

VERSION = "multimodel-three-class-b16-analysis-v1"
DATA = Path("data/cognitive_core/multimodel_three_class_b16")
RUN = Path("runs/cognitive_core/multimodel_three_class_b16")
ARMS = ("none", "irrelevant", "conclusion_only", "proof_prefix", "full")
CLASSES = ("entailed", "contradicted", "undetermined")
LABEL = {"entailed": "Yes", "contradicted": "No", "undetermined": "Unknown"}
BOOTSTRAP_SEED = 2026090316


def _canon(v: Any) -> bytes:
    return json.dumps(v, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()


def _rows(p: Path) -> list[Mapping[str, Any]]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, default=Path("results/b16_analysis_v1.json"))
    args = ap.parse_args()
    root = args.project.resolve()

    panel = {r["task_id"]: r for r in _rows(root / DATA / "public/panel.jsonl")}
    models = sorted(p.parent.parent.name for p in (root / RUN).glob("*/control/complete.json"))

    chosen: dict[str, dict[str, dict[str, str]]] = {}
    for m in models:
        chosen[m] = {}
        for arm in ARMS:
            rows = _rows(root / RUN / m / f"receipts/prospective-{arm}.jsonl")
            if len(rows) != len(panel) or {r["task_id"] for r in rows} != set(panel):
                raise RuntimeError(f"{m}/{arm}: receipts do not cover the panel")
            for r in rows:
                body = {k: v for k, v in r.items() if k != "receipt_id"}
                if hashlib.sha256(_canon(body)).hexdigest() != r["receipt_id"]:
                    raise RuntimeError(f"{m}/{arm}: receipt digest mismatch")
            chosen[m][arm] = {r["task_id"]: r["candidate"] for r in rows}
    if len(models) != 10:
        raise RuntimeError(f"only {len(models)} models complete; refusing to score a partial sweep")

    # ---- authority opens here ----------------------------------------------
    auth = {r["task_id"]: r for r in _rows(root / DATA / "sealed/authority.jsonl")}
    truth = {t: LABEL[a["semantic_class"]] for t, a in auth.items()}
    cls = {t: a["semantic_class"] for t, a in auth.items()}
    ids = sorted(panel)
    by_class = {c: [t for t in ids if cls[t] == c] for c in CLASSES}

    out: dict[str, Any] = {"version": VERSION, "n": len(ids), "models": {},
                           "chance_balanced_accuracy": 1 / 3,
                           "criterion_note": ("prespecified >=80% undetermined recall is INVALID "
                                              "(gamed by all-Unknown collapse); corrected criterion "
                                              "is min per-class recall >= 0.50, applied post hoc")}
    for m in models:
        rec: dict[str, Any] = {"arms": {}}
        for arm in ARMS:
            pick = chosen[m][arm]
            conf = collections.Counter((cls[t], pick[t]) for t in ids)
            recalls = {c: sum(1 for t in by_class[c] if pick[t] == LABEL[c]) / len(by_class[c])
                       for c in CLASSES}
            binary = [t for t in ids if cls[t] != "undetermined"]
            b_pick = {t: pick[t] for t in binary}
            b_truth = {t: truth[t] for t in binary}
            try:
                s = sdt.summarise(b_pick, b_truth)
                dp, cr = s["d_prime"], s["criterion_c"]
            except ValueError:
                dp = cr = None
            rec["arms"][arm] = {
                "confusion": {f"{a}->{b}": n for (a, b), n in sorted(conf.items())},
                "per_class_recall": recalls,
                "balanced_accuracy": sum(recalls.values()) / len(recalls),
                "accuracy": sum(1 for t in ids if pick[t] == truth[t]) / len(ids),
                "response_distribution": {k: v / len(ids) for k, v in
                                          collections.Counter(pick[t] for t in ids).items()},
                "binary_subset_d_prime": dp, "binary_subset_criterion": cr,
            }
        # primary: paired full - none on undetermined items
        und = by_class["undetermined"]
        corr = {a: {t: chosen[m][a][t] == truth[t] for t in und} for a in ("full", "none",
                                                                          "conclusion_only")}
        rec["primary_full_minus_none_undetermined"] = paired.contrast(
            corr["full"], corr["none"], und, BOOTSTRAP_SEED, resamples=20000)
        rec["secondary_full_minus_conclusion_only_undetermined"] = paired.contrast(
            corr["full"], corr["conclusion_only"], und, BOOTSTRAP_SEED, resamples=20000)
        # ---- verdicts ------------------------------------------------------
        # PRESPECIFIED (retained for the record, and INVALID -- see below).
        acc = rec["arms"]["full"]["per_class_recall"]["undetermined"]
        rec["undetermined_accuracy_full"] = acc
        rec["prespecified_relay_verdict"] = ("relays" if acc >= 0.80 else
                                             "partial" if acc >= 0.20 else "architecture_breaking")

        # POST HOC CORRECTION (2026-09-03). The prespecified threshold is a
        # single-class recall measure, and a model that answers `Unknown` to
        # everything scores 100% on it while discriminating nothing. Four of ten
        # models do exactly that (62-96% Unknown; three never emit `No` at all).
        # This is b14's No-bias trap mirrored, and the threshold walked into it.
        #
        # Replacement: a model is a viable substrate only if it clears a floor on
        # EVERY class. That cannot be gamed by collapsing onto one label.
        full = rec["arms"]["full"]
        recalls = full["per_class_recall"]
        dist = full["response_distribution"]
        rec["min_per_class_recall"] = min(recalls.values())
        rec["max_response_share"] = max(dist.values())
        rec["degenerate"] = rec["max_response_share"] >= 0.50
        rec["viable_substrate"] = rec["min_per_class_recall"] >= 0.50
        rec["relay_verdict_corrected"] = (
            "collapsed" if rec["degenerate"] else
            "viable_relays" if rec["viable_substrate"] and acc >= 0.80 else
            "viable_partial_relay" if rec["viable_substrate"] else
            "discriminating_but_below_floor")
        out["models"][m] = rec

    fam = {m: out["models"][m]["primary_full_minus_none_undetermined"]["exact_two_sided_mcnemar_p"]
           for m in models}
    out["holm_primary_across_models"] = paired.holm(fam)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"written -> {args.out}")


if __name__ == "__main__":
    main()
