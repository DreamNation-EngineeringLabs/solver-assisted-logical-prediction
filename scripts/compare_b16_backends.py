#!/usr/bin/env python3
"""Do MLX and CUDA agree, receipt by receipt, on the same sealed panel?

This has to be answered before any larger model joins Experiment 3. Across
b16's 9,600 MLX responses, 298 (3.1%) have an argmax margin below 0.1 logits
and the 1st percentile is 0.000 -- comfortably inside the range where bf16
kernel differences between Metal and CUDA can flip a decision. If they do flip,
a table mixing backends is not measuring one thing, and we would need to say so
rather than quietly append rows.

Reports, per model: how many of the 960 argmax decisions match, where the
mismatches sit in the margin distribution, and whether any per-arm verdict
(balanced accuracy, min per-class recall, viability) actually moves.
"""
from __future__ import annotations

import argparse, json
from pathlib import Path

MLX = Path("runs/cognitive_core/multimodel_three_class_b16")
CUDA = Path("runs/cognitive_core/multimodel_three_class_b19_cuda")
DATA = Path("data/cognitive_core/multimodel_three_class_b16")
ARMS = ("none", "irrelevant", "conclusion_only", "proof_prefix", "full")


def _rows(p: Path):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _balanced(recs, auth):
    per = {}
    for cls in ("Yes", "No", "Unknown"):
        items = [t for t, a in auth.items() if a == cls]
        if items:
            per[cls] = sum(recs[t] == cls for t in items) / len(items)
    return sum(per.values()) / len(per), min(per.values())


def main() -> None:
    ap = argparse.ArgumentParser(description="MLX vs CUDA receipt agreement.")
    ap.add_argument("--project", type=Path, default=Path("."))
    root = ap.parse_args().project.resolve()

    auth = {r["task_id"]: r["answer"] for r in _rows(root / DATA / "sealed/authority.jsonl")}
    out = {"version": "b16-backend-comparison-v1", "models": {}}

    for cuda_dir in sorted((root / CUDA).iterdir()):
        key = cuda_dir.name
        mlx_dir = root / MLX / key
        if not (cuda_dir / "control/complete.json").exists() or not mlx_dir.exists():
            continue
        total = agree = 0
        flips = []
        verdict = {}
        for arm in ARMS:
            m = {r["task_id"]: r for r in _rows(mlx_dir / f"receipts/prospective-{arm}.jsonl")}
            c = {r["task_id"]: r for r in _rows(cuda_dir / f"receipts/prospective-{arm}.jsonl")}
            for t in m:
                total += 1
                if m[t]["candidate"] == c[t]["candidate"]:
                    agree += 1
                else:
                    flips.append({"arm": arm, "task_id": t,
                                  "mlx": m[t]["candidate"], "cuda": c[t]["candidate"],
                                  "mlx_margin": round(m[t]["top_two_margin"], 4),
                                  "cuda_margin": round(c[t]["top_two_margin"], 4)})
            mb, mr = _balanced({t: r["candidate"] for t, r in m.items()}, auth)
            cb, cr = _balanced({t: r["candidate"] for t, r in c.items()}, auth)
            verdict[arm] = {
                "mlx_balanced_acc": round(mb * 100, 2), "cuda_balanced_acc": round(cb * 100, 2),
                "mlx_min_recall": round(mr, 3), "cuda_min_recall": round(cr, 3),
                "mlx_viable": mr >= 0.5, "cuda_viable": cr >= 0.5,
                "verdict_moved": (mr >= 0.5) != (cr >= 0.5),
            }
        out["models"][key] = {
            "responses": total, "agree": agree, "agreement": agree / total,
            "flips": flips[:50], "n_flips": len(flips),
            "max_mlx_margin_among_flips": max((f["mlx_margin"] for f in flips), default=0.0),
            "per_arm": verdict,
            "any_verdict_moved": any(v["verdict_moved"] for v in verdict.values()),
        }

    if not out["models"]:
        raise SystemExit("no model has receipts on both backends yet")

    moved = [k for k, v in out["models"].items() if v["any_verdict_moved"]]
    out["any_verdict_moved"] = bool(moved)
    out["models_with_moved_verdict"] = moved
    for k, v in out["models"].items():
        print(f"{k:16s} {v['agree']}/{v['responses']} agree ({v['agreement']*100:.2f}%)  "
              f"flips {v['n_flips']:3d}  largest MLX margin among them "
              f"{v['max_mlx_margin_among_flips']:.4f}  verdict moved: "
              f"{'YES' if v['any_verdict_moved'] else 'no'}")
    print("\n" + ("A per-arm viability verdict MOVED between backends: " + ", ".join(moved)
                  if moved else
                  "No per-arm verdict moved. Backends are interchangeable for this table."))
    p = root / "results/b16_backend_comparison_v1.json"
    p.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {p.relative_to(root)}")


if __name__ == "__main__":
    main()
