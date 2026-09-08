#!/usr/bin/env python3
"""Score the sealed b15 factorial. Opens the authority; makes no model calls.

Primary contrast is `truncate_1` - `broken_chain` on the ENTAILED subset (n=96),
declared before the run: b14's receipts showed the contradicted class at ceiling
in every certificate arm, contributing zero discordance.

A validity claim requires the primary contrast AND a same-sign d' drop. An arm
that moves accuracy while leaving d' unchanged has moved the model's criterion,
not its sensitivity, and is reported as a bias result.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from cc_instruments import paired, sdt

VERSION = "binary-certificate-factorial-b15-analysis-v1"
DATA = Path("data/cognitive_core/binary_certificate_factorial_b15")
RUN = Path("runs/cognitive_core/binary_certificate_factorial_b15/qwen2p5_3b_4bit")
ARMS = ("none", "irrelevant", "same_entity_irrelevant", "truncate_3", "truncate_2",
        "truncate_1", "broken_chain", "misleading", "shuffled", "full")
SEED = 2026090315


def _canon(v: Any) -> bytes:
    return json.dumps(v, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()


def _rows(p: Path) -> list[Mapping[str, Any]]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, default=Path("results/b15_analysis_v1.json"))
    args = ap.parse_args()
    root = args.project.resolve()

    chosen: dict[str, dict[str, str]] = {}
    for arm in ARMS:
        rows = _rows(root / RUN / f"receipts/prospective-{arm}.jsonl")
        for r in rows:
            body = {k: v for k, v in r.items() if k != "receipt_id"}
            if hashlib.sha256(_canon(body)).hexdigest() != r["receipt_id"]:
                raise RuntimeError(f"{arm}: receipt digest mismatch")
        chosen[arm] = {r["task_id"]: r["candidate"] for r in rows}

    auth = {r["task_id"]: r for r in _rows(root / DATA / "sealed/authority.jsonl")}
    truth = {t: a["answer"] for t, a in auth.items()}
    ids = sorted(truth)
    ent = [t for t in ids if auth[t]["semantic_class"] == "entailed"]
    corr = {a: {t: chosen[a][t] == truth[t] for t in ids} for a in ARMS}

    per_arm = {}
    for a in ARMS:
        s = sdt.summarise(chosen[a], truth)
        per_arm[a] = {
            "correct": sum(corr[a].values()), "accuracy": sum(corr[a].values()) / len(ids),
            "entailed_correct": sum(corr[a][t] for t in ent), "entailed_n": len(ent),
            "d_prime": s["d_prime"], "criterion_c": s["criterion_c"],
            "response_distribution": {k: v / len(ids) for k, v in
                                      collections.Counter(chosen[a].values()).items()},
        }

    def c(l: str, r: str, subset):
        return paired.contrast(corr[l], corr[r], subset, SEED, resamples=20000)

    primary = c("truncate_1", "broken_chain", ent)
    contrasts = {
        "PRIMARY_truncate_1_minus_broken_chain_entailed": primary,
        "surface_broken_chain_minus_irrelevant_entailed": c("broken_chain", "irrelevant", ent),
        "total_truncate_1_minus_irrelevant_entailed": c("truncate_1", "irrelevant", ent),
        "repetition_same_entity_irrelevant_minus_irrelevant_entailed":
            c("same_entity_irrelevant", "irrelevant", ent),
        "order_truncate_1_minus_shuffled_entailed": c("truncate_1", "shuffled", ent),
        "ladder_truncate_2_minus_truncate_1_entailed": c("truncate_2", "truncate_1", ent),
        "ladder_truncate_3_minus_truncate_2_entailed": c("truncate_3", "truncate_2", ent),
        "misleading_minus_full_entailed": c("misleading", "full", ent),
    }
    holm = paired.holm({k: v["exact_two_sided_mcnemar_p"] for k, v in contrasts.items()
                        if k.startswith(("order_", "ladder_"))})

    t1e = per_arm["truncate_1"]["entailed_correct"] / len(ent)
    bce = per_arm["broken_chain"]["entailed_correct"] / len(ent)
    ire = per_arm["irrelevant"]["entailed_correct"] / len(ent)
    total = t1e - ire
    validity = t1e - bce
    verdict = ("construction_fault" if bce > t1e + 0.05 else
               "surface_overlap_dominant" if abs(bce - t1e) <= 0.05
               and primary["exact_two_sided_mcnemar_p"] >= 0.05 else
               "validity_tracking_dominant" if abs(bce - ire) <= 0.05 else "mixed")
    dp_drop = per_arm["truncate_1"]["d_prime"] - per_arm["broken_chain"]["d_prime"]

    out = {"version": VERSION, "n": len(ids), "n_entailed": len(ent), "per_arm": per_arm,
           "contrasts": contrasts, "holm_secondary": holm,
           "decomposition": {"total_state_effect": total, "surface_component": bce - ire,
                             "validity_component": validity,
                             "validity_share": validity / total if total else None},
           "d_prime_drop_truncate_1_minus_broken_chain": dp_drop,
           "same_sign_d_prime_drop": dp_drop > 0,
           "verdict": verdict}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"written -> {args.out}")


if __name__ == "__main__":
    main()
