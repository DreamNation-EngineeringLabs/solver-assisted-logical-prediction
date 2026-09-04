#!/usr/bin/env python3
"""Verify the sealed b14 binary factorial without loading a language model."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence


VERSION = "binary-certificate-factorial-b14-audit-v1"
DATA = Path("data/cognitive_core/binary_certificate_factorial_b14")
RUN = Path("runs/cognitive_core/binary_certificate_factorial_b14/qwen2p5_3b")
ARMS = ("none", "irrelevant", "conclusion_only", "proof_prefix", "full")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def _read(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _rows(path: Path) -> list[Mapping[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _exact_two_sided_mcnemar(left_only: int, right_only: int) -> float:
    discordant = left_only + right_only
    if discordant == 0:
        return 1.0
    tail = sum(math.comb(discordant, value) for value in range(min(left_only, right_only) + 1))
    return min(1.0, 2.0 * tail / (2**discordant))


def _comparison(
    left: Sequence[Mapping[str, Any]],
    right: Sequence[Mapping[str, Any]],
    authority: Mapping[str, str],
) -> Mapping[str, Any]:
    left_by_id = {str(row["task_id"]): row for row in left}
    right_by_id = {str(row["task_id"]): row for row in right}
    if set(left_by_id) != set(authority) or set(right_by_id) != set(authority):
        raise RuntimeError("paired receipts do not cover the sealed authority exactly")
    both = left_only = right_only = neither = 0
    for task_id, answer in authority.items():
        left_ok = left_by_id[task_id]["candidate"] == answer
        right_ok = right_by_id[task_id]["candidate"] == answer
        if left_ok and right_ok:
            both += 1
        elif left_ok:
            left_only += 1
        elif right_ok:
            right_only += 1
        else:
            neither += 1
    return {
        "left_correct": both + left_only,
        "right_correct": both + right_only,
        "paired_risk_difference": (left_only - right_only) / len(authority),
        "paired_table": {
            "both_correct": both,
            "left_only_correct": left_only,
            "right_only_correct": right_only,
            "neither_correct": neither,
        },
        "exact_two_sided_mcnemar_p": _exact_two_sided_mcnemar(left_only, right_only),
    }


def _assert_equal(name: str, observed: Any, expected: Any) -> None:
    if observed != expected:
        raise RuntimeError(f"{name} mismatch: observed={observed!r}, expected={expected!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit b14 data, receipts, and aggregate results without model calls.")
    parser.add_argument("--project", type=Path, default=Path("."))
    args = parser.parse_args()
    project = args.project.resolve()
    data, run = project / DATA, project / RUN
    seal, result = _read(data / "public/seal.json"), _read(run / "results/prospective-factorial.json")

    for panel, record in seal["panels"].items():
        public = project / str(record["public_path"])
        authority = project / str(record["authority_path"])
        _assert_equal(f"{panel} public SHA-256", _sha256(public), record["public_sha256"])
        _assert_equal(f"{panel} authority SHA-256", _sha256(authority), record["authority_sha256"])
        _assert_equal(f"{panel} public row count", len(_rows(public)), record["n"])
        _assert_equal(f"{panel} authority row count", len(_rows(authority)), record["n"])

    authority_rows = _rows(data / "sealed/prospective-authority.jsonl")
    authority = {str(row["task_id"]): str(row["answer"]) for row in authority_rows}
    if len(authority) != 192 or set(authority.values()) != {"Yes", "No"}:
        raise RuntimeError("sealed b14 prospective authority is malformed")

    receipts: dict[str, list[Mapping[str, Any]]] = {}
    for arm in ARMS:
        rows = _rows(run / f"receipts/prospective-{arm}.jsonl")
        if len(rows) != len(authority):
            raise RuntimeError(f"{arm} has {len(rows)} receipts, not {len(authority)}")
        identifiers = set()
        for row in rows:
            body = {key: value for key, value in row.items() if key != "receipt_id"}
            _assert_equal(f"{arm} receipt digest", _digest(body), row.get("receipt_id"))
            if row.get("stage") != "prospective" or row.get("arm") != arm or row.get("candidate") not in {"Yes", "No"}:
                raise RuntimeError(f"{arm} receipt metadata is malformed")
            identifiers.add(str(row["task_id"]))
        if identifiers != set(authority):
            raise RuntimeError(f"{arm} receipt task identifiers do not match authority")
        receipts[arm] = rows

    comparisons = {
        "primary_comparison": _comparison(receipts["proof_prefix"], receipts["conclusion_only"], authority),
        "proof_prefix_minus_irrelevant": _comparison(receipts["proof_prefix"], receipts["irrelevant"], authority),
        "full_minus_conclusion_only": _comparison(receipts["full"], receipts["conclusion_only"], authority),
    }
    correct = {arm: sum(row["candidate"] == authority[str(row["task_id"])] for row in rows) for arm, rows in receipts.items()}
    _assert_equal("result status", result.get("status"), "terminal_scored_no_audit_or_restart")
    _assert_equal("result n", result.get("n"), len(authority))
    _assert_equal("per-arm correct", result.get("correct"), correct)
    for key, comparison in comparisons.items():
        reported = result["primary_comparison"] if key == "primary_comparison" else result["secondary_comparisons"][key]
        for field, value in comparison.items():
            _assert_equal(f"{key} {field}", reported.get(field), value)

    print(json.dumps({
        "version": VERSION,
        "status": "b14_audit_passed_without_model_calls",
        "n": len(authority),
        "receipt_count": sum(len(rows) for rows in receipts.values()),
        "correct": correct,
        "primary_comparison": comparisons["primary_comparison"],
        "seal_id": seal["seal_id"],
        "result_id": result["result_id"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
