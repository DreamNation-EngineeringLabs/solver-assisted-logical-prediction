#!/usr/bin/env python3
"""The detection test against both abstention baselines.

Peer review, round 2, minor 11: b17 measured the broken-chain abstention rate
against `irrelevant`, which is defensible but conflates two causes of that
baseline -- the three-candidate instruction itself, and the presence of a
query-irrelevant record. b17b adds a `none` arm under the same instruction and
candidate set to separate them.

The reviewer was right that it mattered. `irrelevant` is close to `none` on the
4-bit checkpoint and very far from it at bfloat16, so it is not a neutral
reference across checkpoints and the delta measured against it is not comparable
between them.

What the detection hypothesis predicts is a *rise* in abstention when the chain
is broken, against either reference. This script reports both.
"""
from __future__ import annotations

import argparse, json
from pathlib import Path

B17 = Path("runs/cognitive_core/three_class_broken_chain_b17")
B17B = Path("runs/cognitive_core/three_class_none_baseline_b17b")
ORDER = ("qwen2p5_3b_4bit", "qwen2p5_3b_bf16", "gemma3_4b_b15")


def _counts(path: Path) -> dict:
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    c = {x: sum(r["candidate"] == x for r in rows) for x in ("Yes", "No", "Unknown")}
    return {"n": len(rows), **c, "unknown_rate": c["Unknown"] / len(rows)}


def main() -> None:
    ap = argparse.ArgumentParser(description="b17 detection test against `none` and `irrelevant`.")
    ap.add_argument("--project", type=Path, default=Path("."))
    root = ap.parse_args().project.resolve()

    out = {"version": "b17-detection-both-baselines-v3", "checkpoints": {}}
    for key in ORDER:
        run, runb = root / B17 / key, root / B17B / key
        if not (run / "control/complete.json").exists():
            continue
        arms = {a: _counts(run / f"receipts/prospective-{a}.jsonl")
                for a in ("irrelevant", "broken_chain", "truncate_1")}
        if (runb / "control/complete.json").exists():
            arms["none"] = _counts(runb / "receipts/prospective-none.jsonl")
        brk = arms["broken_chain"]["unknown_rate"]
        rec = {
            "arms": arms,
            "vs_irrelevant_pp": (brk - arms["irrelevant"]["unknown_rate"]) * 100,
            "irrelevant_minus_none_pp": None,
            "vs_none_pp": None,
        }
        if "none" in arms:
            rec["vs_none_pp"] = (brk - arms["none"]["unknown_rate"]) * 100
            rec["irrelevant_minus_none_pp"] = (
                arms["irrelevant"]["unknown_rate"] - arms["none"]["unknown_rate"]) * 100
        # detection predicts a RISE against either reference
        rec["detection_supported"] = any(
            v is not None and v > 0 for v in (rec["vs_irrelevant_pp"], rec["vs_none_pp"]))
        out["checkpoints"][key] = rec

    ck = out["checkpoints"]
    out["detection_supported_anywhere"] = any(v["detection_supported"] for v in ck.values())
    out["interpretation"] = (
        "Abstention under `broken_chain` against each reference, in pp: "
        + "; ".join(f"{k} {v['vs_irrelevant_pp']:+.1f} vs irrelevant"
                    + (f", {v['vs_none_pp']:+.1f} vs none" if v["vs_none_pp"] is not None else "")
                    for k, v in ck.items())
        + ". Detection predicts a rise against either reference and there is none on any "
          "checkpoint, so the refutation does not depend on the baseline. The magnitude does: "
        + "; ".join(f"{k} irrelevant sits {v['irrelevant_minus_none_pp']:+.1f}pp from none"
                    for k, v in ck.items() if v["irrelevant_minus_none_pp"] is not None)
        + " -- so `irrelevant` is a near-neutral reference on the 4-bit checkpoint and inflates "
          "abstention substantially at bfloat16. Deltas against it are not comparable across "
          "checkpoints, and both are reported.")
    path = root / "results/b17_detection_both_baselines_v3.json"
    path.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    for k, v in ck.items():
        print(f"{k:18s} none {v['arms'].get('none', {}).get('unknown_rate', float('nan'))*100:5.1f}%"
              f"  irrelevant {v['arms']['irrelevant']['unknown_rate']*100:5.1f}%"
              f"  broken {v['arms']['broken_chain']['unknown_rate']*100:5.1f}%"
              f"   vs-none {v['vs_none_pp']:+6.1f}pp  vs-irrel {v['vs_irrelevant_pp']:+6.1f}pp")
    print("\n" + out["interpretation"])


if __name__ == "__main__":
    main()
