#!/usr/bin/env python3
"""Count every scored response actually present in the repository.

Peer review, round 2: the manuscript quoted three different totals (18,816 in
the abstract, 12,480 twice elsewhere) and none matched the receipts. In a paper
whose thesis is re-derivability that is the worst available error, so the number
is no longer typed by hand: this script counts what is on disk, and the paper's
composer substitutes the result.

b14 predates the runs/ layout and released its 960 responses as a single flat
file; it is counted here so the total covers every experiment in the paper.
"""
from __future__ import annotations

import argparse, json
from pathlib import Path

RUNS = Path("runs/cognitive_core")
B14 = Path("results/b14_raw_model_calls_960.jsonl")


def _lines(path: Path) -> int:
    with path.open(encoding="utf-8") as fh:
        return sum(1 for line in fh if line.strip())


def main() -> None:
    ap = argparse.ArgumentParser(description="Census the scored responses on disk.")
    ap.add_argument("--project", type=Path, default=Path("."))
    root = ap.parse_args().project.resolve()

    runs: dict[str, int] = {}
    for receipts in sorted((root / RUNS).rglob("receipts")):
        n = sum(_lines(f) for f in sorted(receipts.glob("*.jsonl")))
        if n:
            runs[str(receipts.parent.relative_to(root / RUNS))] = n
    flat = root / B14
    if flat.exists():
        runs["binary_certificate_factorial_b14/qwen2p5_3b"] = _lines(flat)

    by_experiment: dict[str, dict[str, int]] = {}
    for key, n in runs.items():
        exp = key.split("/")[0]
        rec = by_experiment.setdefault(exp, {"runs": 0, "responses": 0})
        rec["runs"] += 1
        rec["responses"] += n

    census = {
        "version": "receipt-census-v1",
        "total_scored_responses": sum(runs.values()),
        "model_runs": len(runs),
        "by_experiment": dict(sorted(by_experiment.items())),
        "by_run": dict(sorted(runs.items())),
        "note": ("b14 released its responses as results/b14_raw_model_calls_960.jsonl "
                 "rather than under runs/*/receipts/; it is counted as one model-run."),
    }
    out = root / "results/receipt_census_v1.json"
    out.write_text(json.dumps(census, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: census[k] for k in ("total_scored_responses", "model_runs", "by_experiment")}, indent=1))


if __name__ == "__main__":
    main()
