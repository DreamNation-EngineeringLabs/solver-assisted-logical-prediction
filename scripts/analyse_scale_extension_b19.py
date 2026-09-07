#!/usr/bin/env python3
"""Does supplying proof state hurt more as the interface gets larger?

b16 stopped at 7.6B and reported a count -- "proof state degrades three of ten
models". A count cannot say whether that is a property of scale. Within the b16
range the harm looked like it grew (-0.19 at 3B, -0.11 at 4.3B, -0.80 at 7.6B),
but three points at the top of a truncated range is a hypothesis, not a finding.

b19 extends the sweep on an A100 with Llama-3.1-8B and Qwen2.5-14B, and the
Qwen2.5 rows now form a within-family ladder -- 0.5, 1.5, 3, 7.6, 14.7B -- where
family, tokenizer and training recipe are fixed and only scale varies. That is
the comparison a mixed-family table cannot make.

Harm is the drop in minimum per-class recall from `conclusion_only` (answer, no
state) to `full` (answer plus state). Negative means proof state made the
interface worse.
"""
from __future__ import annotations

import argparse, json
from pathlib import Path

RUN = Path("runs/cognitive_core/multimodel_three_class_b19_cuda")
DATA = Path("data/cognitive_core/multimodel_three_class_b16")
ARMS = ("none", "irrelevant", "conclusion_only", "proof_prefix", "full")
SIZE = {"qwen2p5_0p5b": 0.5, "olmo2_1b": 1.0, "llama3p2_1b": 1.2, "qwen2p5_1p5b": 1.5,
        "smollm2_1p7b": 1.7, "qwen2p5_3b": 3.0, "llama3p2_3b": 3.2, "phi4_mini": 3.8,
        "gemma3_4b": 4.3, "qwen2p5_7b": 7.6, "llama3p1_8b": 8.0, "qwen2p5_14b": 14.7}
FAMILY = {"qwen2p5_0p5b": "qwen2.5", "qwen2p5_1p5b": "qwen2.5", "qwen2p5_3b": "qwen2.5",
          "qwen2p5_7b": "qwen2.5", "qwen2p5_14b": "qwen2.5"}


def _rows(p: Path):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _scores(recs, auth):
    per = {}
    for cls in ("Yes", "No", "Unknown"):
        items = [t for t, a in auth.items() if a == cls]
        per[cls] = sum(recs[t] == cls for t in items) / len(items)
    return sum(per.values()) / len(per), min(per.values()), per


def main() -> None:
    ap = argparse.ArgumentParser(description="Scale extension of Experiment 3.")
    ap.add_argument("--project", type=Path, default=Path("."))
    root = ap.parse_args().project.resolve()

    auth = {r["task_id"]: r["answer"] for r in _rows(root / DATA / "sealed/authority.jsonl")}
    out = {"version": "scale-extension-b19-v1", "backend": "transformers+cuda", "models": {}}

    for d in sorted((root / RUN).iterdir()):
        if not (d / "control/complete.json").exists():
            continue
        arms = {}
        for arm in ARMS:
            recs = {r["task_id"]: r["candidate"]
                    for r in _rows(d / f"receipts/prospective-{arm}.jsonl")}
            ba, mr, per = _scores(recs, auth)
            arms[arm] = {"balanced_accuracy": ba, "min_per_class_recall": mr,
                         "per_class_recall": per, "viable": mr >= 0.5}
        harm = arms["full"]["min_per_class_recall"] - arms["conclusion_only"]["min_per_class_recall"]
        out["models"][d.name] = {
            "params_b": SIZE.get(d.name), "family": FAMILY.get(d.name), "arms": arms,
            "state_harm_min_recall": harm,
            "viable_in": [a for a in ARMS if arms[a]["viable"]],
        }

    rows = sorted(out["models"].items(), key=lambda kv: kv[1]["params_b"] or 0)
    print(f"{'model':16s} {'B':>5} {'concl':>7} {'full':>7} {'harm':>7}   viable in")
    for k, v in rows:
        a = v["arms"]
        print(f"{k:16s} {v['params_b']:5.1f} "
              f"{a['conclusion_only']['min_per_class_recall']:7.3f} "
              f"{a['full']['min_per_class_recall']:7.3f} "
              f"{v['state_harm_min_recall']:+7.3f}   {','.join(v['viable_in']) or '-'}")

    fam = [(v["params_b"], k, v["state_harm_min_recall"])
           for k, v in out["models"].items() if v["family"] == "qwen2.5"]
    fam.sort()
    print("\nQwen2.5 within-family ladder (family, tokenizer, recipe fixed):")
    for b, k, h in fam:
        print(f"  {b:5.1f}B  {k:14s} harm {h:+.3f}")
    hurt = [k for k, v in out["models"].items() if v["state_harm_min_recall"] < -0.05]
    out["degraded_by_proof_state"] = hurt
    out["qwen_ladder"] = [{"params_b": b, "key": k, "harm": h} for b, k, h in fam]
    print(f"\nproof state degrades {len(hurt)} of {len(out['models'])} interfaces: {', '.join(hurt)}")
    p = root / "results/b19_scale_extension_v1.json"
    p.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {p.relative_to(root)}")


if __name__ == "__main__":
    main()
