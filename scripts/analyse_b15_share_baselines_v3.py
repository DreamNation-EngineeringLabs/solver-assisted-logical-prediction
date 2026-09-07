#!/usr/bin/env python3
"""The validity share against two baselines, on all three b15 checkpoints.

Peer review, round 2: the published share divides by the effect measured against
the `irrelevant` arm. On the Qwen checkpoints that is also the unaided score, so
the choice is invisible. Gemma-3-4b answers 22 of 96 entailed items with no
certificate at all, and 20 of those 22 are also correct under `broken_chain` --
so a share computed against `irrelevant` charges Gemma's own competence to
surface exploitation.

Both baselines are reported here because they answer different questions:

  irrelevant : what did this certificate's CONTENT add over a same-shape control
  none       : what did the certificate add over the model working unaided

Neither is "the" right denominator. The finding is that they diverge exactly
when the substrate has unaided competence, which the first checkpoint did not.
"""
from __future__ import annotations

import argparse, json
from pathlib import Path

B15 = Path("data/cognitive_core/binary_certificate_factorial_b15")
RUNS = Path("runs/cognitive_core/binary_certificate_factorial_b15")
CHECKPOINTS = ("qwen2p5_3b_4bit", "qwen2p5_3b_bf16", "gemma3_4b_b15")


def _rows(p: Path):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> None:
    ap = argparse.ArgumentParser(description="Validity share against both baselines.")
    ap.add_argument("--project", type=Path, default=Path("."))
    root = ap.parse_args().project.resolve()

    authority = {r["task_id"]: r["answer"] for r in _rows(root / B15 / "sealed/authority.jsonl")}
    entailed = [t for t, a in authority.items() if a == "Yes"]
    n = len(entailed)

    out = {"version": "b15-share-baselines-v3", "n_entailed": n, "checkpoints": {}}
    for key in CHECKPOINTS:
        arms = {f.stem.replace("prospective-", ""):
                {r["task_id"]: r["candidate"] for r in _rows(f)}
                for f in sorted((root / RUNS / key / "receipts").glob("prospective-*.jsonl"))}
        correct = {a: sum(arms[a][t] == authority[t] for t in entailed) for a in arms}
        none, irr, brk, tr1 = (correct["none"], correct["irrelevant"],
                               correct["broken_chain"], correct["truncate_1"])
        overlap = sum(arms["none"][t] == authority[t] and arms["broken_chain"][t] == authority[t]
                      for t in entailed)
        out["checkpoints"][key] = {
            "correct_entailed": correct,
            "unaided_also_correct_under_broken_chain": overlap,
            "share_vs_irrelevant": (tr1 - brk) / (tr1 - irr) if tr1 != irr else None,
            "share_vs_none": (tr1 - brk) / (tr1 - none) if tr1 != none else None,
            "surface_vs_irrelevant": (brk - irr) / (tr1 - irr) if tr1 != irr else None,
            "surface_vs_none": (brk - none) / (tr1 - none) if tr1 != none else None,
        }

    g = out["checkpoints"]["gemma3_4b_b15"]
    out["interpretation"] = (
        "The two baselines agree on both Qwen checkpoints (unaided score 0/96) and diverge on "
        f"gemma-3-4b: {g['share_vs_irrelevant']*100:.1f}% against `irrelevant`, "
        f"{g['share_vs_none']*100:.1f}% against `none`. Under the second, the split between "
        "surface overlap and inference is close to even rather than surface-dominated, so the "
        "claim 'most of the effect is surface overlap' does not survive the more conservative "
        "denominator and is not made. What survives on either baseline is that the share is "
        "checkpoint-specific.")
    path = root / "results/b15_share_baselines_v3.json"
    path.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out["checkpoints"], indent=1, sort_keys=True))
    print(out["interpretation"])


if __name__ == "__main__":
    main()
