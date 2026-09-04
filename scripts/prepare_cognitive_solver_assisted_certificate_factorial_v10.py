#!/usr/bin/env python3
"""Seal the one permitted v10 successor to the v8 certificate factorial.

V8 is not modified or reopened: its Qwen3 qualification stopped before it
produced a score because MLX bfloat16 logits could not be converted directly
to NumPy.  V10 uses a distinct, deterministic panel and records both this
wrapper and the frozen v8 generator from which its construction is derived.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import prepare_cognitive_solver_assisted_certificate_factorial_v8 as base


VERSION = "solver-assisted-certificate-factorial-v10"
DATA = Path("data/cognitive_core/solver_assisted_certificate_factorial_v10")
TASK_SEED = 2026090124
SCRIPT = "scripts/prepare_cognitive_solver_assisted_certificate_factorial_v10.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _id_v10(task_id: str) -> str:
    return task_id.replace("scf8-", "scf10-", 1)


_base_factorial_item = base._factorial_item
_base_qualification_item = base._qualification_item


def _factorial_item(index: int, split: str, semantic: str) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    public, authority = _base_factorial_item(index, split, semantic)
    task_id = _id_v10(str(public["task_id"]))
    return ({**public, "version": VERSION, "task_id": task_id}, {**authority, "task_id": task_id})


def _qualification_item(index: int, semantic: str) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    public, authority = _base_qualification_item(index, semantic)
    task_id = _id_v10(str(public["task_id"]))
    return ({**public, "version": VERSION, "task_id": task_id}, {**authority, "task_id": task_id})


def _configure_base() -> None:
    base.VERSION = VERSION
    base.DATA = DATA
    base.TASK_SEED = TASK_SEED
    base._factorial_item = _factorial_item
    base._qualification_item = _qualification_item


def main() -> None:
    parser = argparse.ArgumentParser(description="Seal the fresh v10 certificate-factorial data without model calls.")
    parser.add_argument("--project", type=Path, default=Path("."))
    args = parser.parse_args()
    project = args.project.resolve()
    data = project / DATA
    if data.exists():
        raise RuntimeError("v10 data path already exists; this construction attempt is consumed")
    _configure_base()

    interface_public: list[Mapping[str, Any]] = []
    interface_authority: list[Mapping[str, Any]] = []
    for semantic in base.NORMAL_MAP:
        for _ in range(base.QUALIFICATION_PER_CLASS):
            task, answer = _qualification_item(len(interface_public), semantic)
            interface_public.append(task)
            interface_authority.append(answer)
    development_public, development_authority = base._panel("development", base.DEVELOPMENT_PER_CLASS)
    prospective_public, prospective_authority = base._panel("prospective", base.PROSPECTIVE_PER_CLASS)
    all_public = [*interface_public, *development_public, *prospective_public]
    if len({str(task["task_id"]) for task in all_public}) != len(all_public):
        raise RuntimeError("v10 task identifiers are not unique")

    protocol = base._protocol()
    public = {"interface": interface_public, "development": development_public, "prospective": prospective_public}
    authorities = {"interface": interface_authority, "development": development_authority, "prospective": prospective_authority}
    for name in public:
        base._write_rows_new(data / f"public/{name}.jsonl", public[name])
        base._write_rows_new(data / f"sealed/{name}-authority.jsonl", authorities[name])
    base._write_new(data / "public/protocol.json", protocol)
    generator = {
        "script": SCRIPT,
        "script_sha256": _sha256(Path(__file__).resolve()),
        "base_generator": "scripts/prepare_cognitive_solver_assisted_certificate_factorial_v8.py",
        "base_generator_sha256": _sha256(Path(base.__file__).resolve()),
        "task_seed": TASK_SEED,
        "successor_reason": "v8_qwen3_qualification_engineering_failure_before_any_score_or_authority_opening",
    }
    seal_body = {
        "version": VERSION,
        "protocol_id": protocol["protocol_id"],
        "protocol_sha256": _sha256(data / "public/protocol.json"),
        "generator": generator,
        "panels": {
            name: {
                "public_path": str((DATA / f"public/{name}.jsonl").as_posix()),
                "public_sha256": _sha256(data / f"public/{name}.jsonl"),
                "authority_path": str((DATA / f"sealed/{name}-authority.jsonl").as_posix()),
                "authority_sha256": _sha256(data / f"sealed/{name}-authority.jsonl"),
                "n": len(public[name]),
            }
            for name in public
        },
    }
    base._write_new(data / "public/seal.json", {**seal_body, "seal_id": base._digest(seal_body)})
    print(json.dumps({"status": "v10_data_sealed_without_model_calls", "panels": {name: len(rows) for name, rows in public.items()}, "protocol_id": protocol["protocol_id"], "model_calls": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
