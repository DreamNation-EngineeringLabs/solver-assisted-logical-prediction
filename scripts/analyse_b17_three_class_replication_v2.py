#!/usr/bin/env python3
"""Is the detection refutation checkpoint-specific? b17 on all available runs.

Peer review, round 2: b17 existed only for the 4-bit Qwen checkpoint, yet the
Conclusion claimed the finding held "on every checkpoint". Worse, it was missing
on gemma-3-4b -- the one model that answers broken certificates correctly on 58
of 96 entailed items, and therefore the only checkpoint where "detects the
break" and "fails to complete" make visibly different predictions.

The discriminating quantity is the Unknown rate under `broken_chain` against the
`irrelevant` baseline, which fixes the model's default under three candidates:

  a validity tracker  -> abstains MORE when the chain is broken   (rate goes up)
  a pattern completer -> falls back to its default                (rate flat/down)
"""
from __future__ import annotations

import argparse, json
from pathlib import Path

RUN = Path("runs/cognitive_core/three_class_broken_chain_b17")
ARMS = ("irrelevant", "broken_chain", "truncate_1")


def _rows(p: Path):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> None:
    ap = argparse.ArgumentParser(description="b17 across every checkpoint that has run.")
    ap.add_argument("--project", type=Path, default=Path("."))
    root = ap.parse_args().project.resolve()

    out = {"version": "b17-three-class-replication-v2", "checkpoints": {}}
    for run_dir in sorted((root / RUN).iterdir()):
        if not (run_dir / "control/complete.json").exists():
            continue
        arms = {}
        for arm in ARMS:
            rows = _rows(run_dir / f"receipts/prospective-{arm}.jsonl")
            counts = {c: sum(r["candidate"] == c for r in rows) for c in ("Yes", "No", "Unknown")}
            arms[arm] = {"n": len(rows), **counts,
                         "unknown_rate": counts["Unknown"] / len(rows)}
        delta = arms["broken_chain"]["unknown_rate"] - arms["irrelevant"]["unknown_rate"]
        out["checkpoints"][run_dir.name] = {
            "arms": arms,
            "broken_chain_minus_irrelevant_unknown_rate": delta,
            # A checkpoint that already abstains rarely cannot show a large drop,
            # so the delta understates the effect where the baseline is low. The
            # absolute count is the honest companion figure.
            "baseline_unknown_rate": arms["irrelevant"]["unknown_rate"],
            "broken_chain_unknown_count": arms["broken_chain"]["Unknown"],
            "verdict": "detection_refuted" if delta < 0 else "detection_supported",
        }

    verdicts = {k: v["verdict"] for k, v in out["checkpoints"].items()}
    # One checkpoint is not a replication, whatever the sign agreement says.
    out["replicates"] = len(verdicts) > 1 and len(set(verdicts.values())) == 1
    per_checkpoint = "; ".join(
        f"{k} {v['broken_chain_minus_irrelevant_unknown_rate']*100:+.1f}pp ({v['verdict']})"
        for k, v in out["checkpoints"].items())
    if len(verdicts) < 2:
        tail = ("Only one checkpoint has run, so this is a single-model result and the paper "
                "must say so.")
    elif out["replicates"]:
        tail = ("The sign is the same on all %d checkpoints, so the refutation is not an artefact "
                "of one model." % len(verdicts))
    else:
        tail = ("The sign differs across checkpoints, so the finding is checkpoint-specific and "
                "must be reported as such.")
    out["n_checkpoints"] = len(verdicts)
    out["interpretation"] = (
        "Unknown rate under `broken_chain` minus the `irrelevant` baseline, per checkpoint: "
        + per_checkpoint + ". " + tail)
    path = root / "results/b17_replication_v2.json"
    path.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out["checkpoints"], indent=1, sort_keys=True))
    print("\n" + out["interpretation"])


if __name__ == "__main__":
    main()
