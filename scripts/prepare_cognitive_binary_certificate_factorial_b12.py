#!/usr/bin/env python3
"""Seal the one b12 recovery successor to b11 without loading a model."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import prepare_cognitive_binary_certificate_factorial_b11 as base


VERSION = "binary-certificate-factorial-b12"
DATA = Path("data/cognitive_core/binary_certificate_factorial_b12")
TASK_SEED = 2026090129
SCRIPT = "scripts/prepare_cognitive_binary_certificate_factorial_b12.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _id_b12(task_id: str) -> str:
    return task_id.replace("bcf11-", "bcf12-", 1)


_factorial_item_b11 = base._factorial_item
_qualification_item_b11 = base._qualification_item


def _factorial_item(index: int, split: str, semantic: str) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    public, authority = _factorial_item_b11(index, split, semantic)
    task_id = _id_b12(str(public["task_id"]))
    return ({**public, "version": VERSION, "task_id": task_id}, {**authority, "task_id": task_id})


def _qualification_item(index: int, semantic: str) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    public, authority = _qualification_item_b11(index, semantic)
    task_id = _id_b12(str(public["task_id"]))
    return ({**public, "version": VERSION, "task_id": task_id}, {**authority, "task_id": task_id})


def _configure_base() -> None:
    base.VERSION = VERSION
    base.DATA = DATA
    base.TASK_SEED = TASK_SEED
    base._factorial_item = _factorial_item
    base._qualification_item = _qualification_item


def _protocol() -> Mapping[str, Any]:
    body = dict(base._protocol())
    body.pop("protocol_id", None)
    body["version"] = VERSION
    body["successor_reason"] = "b11_prospective_external_interruption_before_any_receipt_or_authority_opening"
    body["execution_transport"] = {
        "prospective_shards": 8,
        "items_per_shard": 24,
        "arms": list(base.ARMS),
        "atomic_receipt_policy": "one exclusive receipt file and completion record per predeclared arm-shard",
        "recovery_policy": "no arm-shard is rerun; an interrupted shard without a receipt terminates the study",
    }
    return {**body, "protocol_id": base._digest(body)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Seal fresh b12 binary certificate-factorial data without model calls.")
    parser.add_argument("--project", type=Path, default=Path("."))
    args = parser.parse_args()
    project = args.project.resolve()
    data = project / DATA
    if data.exists():
        raise RuntimeError("b12 data path already exists; construction is consumed")
    _configure_base()
    interface_public: list[Mapping[str, Any]] = []
    interface_authority: list[Mapping[str, Any]] = []
    for semantic in base.CLASSES:
        for _ in range(base.QUALIFICATION_PER_CLASS):
            task, answer = _qualification_item(len(interface_public), semantic)
            interface_public.append(task)
            interface_authority.append(answer)
    development_public, development_authority = base._panel("development", base.DEVELOPMENT_PER_CLASS)
    prospective_public, prospective_authority = base._panel("prospective", base.PROSPECTIVE_PER_CLASS)
    public = {"interface": interface_public, "development": development_public, "prospective": prospective_public}
    authority = {"interface": interface_authority, "development": development_authority, "prospective": prospective_authority}
    all_tasks = [*interface_public, *development_public, *prospective_public]
    if len({str(row["task_id"]) for row in all_tasks}) != len(all_tasks):
        raise RuntimeError("b12 task identifiers are not unique")
    protocol = _protocol()
    for name in public:
        base._write_rows_new(data / f"public/{name}.jsonl", public[name])
        base._write_rows_new(data / f"sealed/{name}-authority.jsonl", authority[name])
    base._write_new(data / "public/protocol.json", protocol)
    generator = {
        "script": SCRIPT,
        "script_sha256": _sha256(Path(__file__).resolve()),
        "base_generator": "scripts/prepare_cognitive_binary_certificate_factorial_b11.py",
        "base_generator_sha256": _sha256(Path(base.__file__).resolve()),
        "task_seed": TASK_SEED,
        "successor_reason": "b11_prospective_external_interruption_before_any_receipt_or_authority_opening",
    }
    seal_body = {
        "version": VERSION,
        "protocol_id": protocol["protocol_id"],
        "protocol_sha256": _sha256(data / "public/protocol.json"),
        "generator": generator,
        "panels": {name: {"public_path": str((DATA / f"public/{name}.jsonl").as_posix()), "public_sha256": _sha256(data / f"public/{name}.jsonl"), "authority_path": str((DATA / f"sealed/{name}-authority.jsonl").as_posix()), "authority_sha256": _sha256(data / f"sealed/{name}-authority.jsonl"), "n": len(public[name])} for name in public},
    }
    base._write_new(data / "public/seal.json", {**seal_body, "seal_id": base._digest(seal_body)})
    print(json.dumps({"status": "b12_data_sealed_without_model_calls", "panels": {name: len(rows) for name, rows in public.items()}, "protocol_id": protocol["protocol_id"], "model_calls": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
