#!/usr/bin/env python3
"""Produce publication-grade paired tables and intervals for the sealed v7 pilot."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from statistics import NormalDist
from typing import Any, Mapping, Sequence

import numpy as np


VERSION = "solver-assisted-v7-publication-analysis-v1"
DATA = Path("data/cognitive_core/repairability_proofwriter_grounded_state_v7")
RUN = Path("runs/cognitive_core/repairability_proofwriter_grounded_state_v7")
OUTPUT = Path("artifacts/solver_assisted_v7_publication_analysis/v7_paired_analysis.json")
BOOTSTRAP_SEED = 2026090121
NORMAL = NormalDist()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise RuntimeError(f"expected object at {path}")
    return value


def _rows(path: Path) -> list[Mapping[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _write_new(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _exact_mcnemar(left_only: int, right_only: int) -> float:
    discordant = left_only + right_only
    if discordant == 0:
        return 1.0
    return min(1.0, 2.0 * sum(math.comb(discordant, value) for value in range(min(left_only, right_only) + 1)) / (2**discordant))


def _bca(values: Sequence[int], *, seed: int, replicates: int = 100_000) -> tuple[float, float]:
    observed = np.asarray(values, dtype=np.float64)
    estimate = float(observed.mean())
    rng = np.random.default_rng(seed)
    distribution = np.empty(replicates, dtype=np.float64)
    for start in range(0, replicates, 1000):
        amount = min(1000, replicates - start)
        indexes = rng.integers(0, len(observed), size=(amount, len(observed)), endpoint=False)
        distribution[start : start + amount] = observed[indexes].mean(axis=1)
    proportion_less = (float(np.count_nonzero(distribution < estimate)) + 0.5 * float(np.count_nonzero(distribution == estimate))) / replicates
    proportion_less = min(max(proportion_less, 1.0 / (2 * replicates)), 1.0 - 1.0 / (2 * replicates))
    bias = NORMAL.inv_cdf(proportion_less)
    jackknife = (float(observed.sum()) - observed) / (len(observed) - 1)
    centered = jackknife.mean() - jackknife
    denominator = 6.0 * float(np.sum(centered * centered) ** 1.5)
    acceleration = 0.0 if denominator == 0.0 else float(np.sum(centered**3) / denominator)

    def adjusted(alpha: float) -> float:
        score = NORMAL.inv_cdf(alpha)
        numerator = bias + score
        return min(max(NORMAL.cdf(bias + numerator / (1.0 - acceleration * numerator)), 0.0), 1.0)

    return float(np.quantile(distribution, adjusted(0.025))), float(np.quantile(distribution, adjusted(0.975)))


def _comparison(left: Sequence[Mapping[str, Any]], right: Sequence[Mapping[str, Any]], authority: Mapping[str, str], comparison_name: str) -> Mapping[str, Any]:
    left_by_id = {str(row["task_id"]): row for row in left}
    right_by_id = {str(row["task_id"]): row for row in right}
    if set(left_by_id) != set(authority) or set(right_by_id) != set(authority):
        raise RuntimeError("receipts do not cover the authority exactly")
    both = left_only = right_only = neither = 0
    differences: list[int] = []
    for task_id in sorted(authority):
        left_correct = left_by_id[task_id]["candidate"] == authority[task_id]
        right_correct = right_by_id[task_id]["candidate"] == authority[task_id]
        differences.append(int(left_correct) - int(right_correct))
        if left_correct and right_correct:
            both += 1
        elif left_correct:
            left_only += 1
        elif right_correct:
            right_only += 1
        else:
            neither += 1
    seed = int.from_bytes(hashlib.sha256(f"{BOOTSTRAP_SEED}:{comparison_name}".encode("utf-8")).digest()[:8], "big")
    return {
        "comparison": comparison_name,
        "n": len(differences),
        "left_correct": both + left_only,
        "right_correct": both + right_only,
        "paired_risk_difference": sum(differences) / len(differences),
        "paired_table": {"both_correct": both, "left_only_correct": left_only, "right_only_correct": right_only, "neither_correct": neither},
        "exact_two_sided_mcnemar_p": _exact_mcnemar(left_only, right_only),
        "paired_BCa_bootstrap_95": list(_bca(differences, seed=seed)),
        "interval_method": "95% nonparametric paired BCa bootstrap; 100,000 deterministic resamples",
        "bootstrap_seed": seed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyse sealed v7 receipts with standard paired reporting.")
    parser.add_argument("--project", type=Path, default=Path("."))
    args = parser.parse_args()
    project = args.project.resolve()
    output = project / OUTPUT
    if output.exists():
        raise RuntimeError("publication analysis record already exists")
    data, run = project / DATA, project / RUN
    seal = _read(data / "public/seal.json")
    authority_path = project / str(seal["panels"]["prospective"]["authority_path"])
    authority = {str(row["task_id"]): str(row["answer"]) for row in _rows(authority_path)}
    receipts = {arm: _rows(run / f"receipts/prospective-{arm}.jsonl") for arm in ("verified_state", "irrelevant_state", "no_state")}
    comparisons = {
        "query_relevant_certificate_minus_irrelevant_certificate": _comparison(receipts["verified_state"], receipts["irrelevant_state"], authority, "relevant_minus_irrelevant"),
        "query_relevant_certificate_minus_no_certificate": _comparison(receipts["verified_state"], receipts["no_state"], authority, "relevant_minus_none"),
    }
    body = {
        "version": VERSION,
        "source_result_id": _read(run / "results/terminal-score.json")["result_id"],
        "authority_sha256": _sha256(authority_path),
        "receipt_sha256": {arm: _sha256(run / f"receipts/prospective-{arm}.jsonl") for arm in receipts},
        "comparisons": comparisons,
        "interpretation": "These intervals quantify the observed v7 system-level paired accuracy differences. They do not identify internal proof use because the query-relevant certificate is answer-diagnostic.",
        "power_note": "No effect-size sample-size calculation was recorded for the sealed v7 pilot. Do not report retrospective power as a confirmatory design justification.",
        "replacement_of_prior_interval": "This report supersedes the nonstandard Wilson sensitivity envelope in publication-facing text; the original terminal record remains immutable.",
    }
    _write_new(output, {**body, "analysis_id": _digest(body)})
    print(json.dumps({"output": str(output), "analysis_id": _digest(body), "comparisons": comparisons}, sort_keys=True))


if __name__ == "__main__":
    main()
