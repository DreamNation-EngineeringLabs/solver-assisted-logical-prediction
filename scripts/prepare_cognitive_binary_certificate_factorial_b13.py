#!/usr/bin/env python3
"""Seal b13: a fresh panel for one-forward-batch execution."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import prepare_cognitive_binary_certificate_factorial_b12 as transport


VERSION = "binary-certificate-factorial-b13"
DATA = Path("data/cognitive_core/binary_certificate_factorial_b13")
TASK_SEED = 2026090131
SCRIPT = "scripts/prepare_cognitive_binary_certificate_factorial_b13.py"
root = transport.base


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _factorial_item(index: int, split: str, semantic: str) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    public, authority = transport._factorial_item(index, split, semantic)
    task_id = str(public["task_id"]).replace("bcf12-", "bcf13-", 1)
    return ({**public, "version": VERSION, "task_id": task_id}, {**authority, "task_id": task_id})


def _qualification_item(index: int, semantic: str) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    public, authority = transport._qualification_item(index, semantic)
    task_id = str(public["task_id"]).replace("bcf12-", "bcf13-", 1)
    return ({**public, "version": VERSION, "task_id": task_id}, {**authority, "task_id": task_id})


def _configure() -> None:
    transport._configure_base()
    root.VERSION = VERSION
    root.DATA = DATA
    root.TASK_SEED = TASK_SEED
    root._factorial_item = _factorial_item
    root._qualification_item = _qualification_item


def _protocol() -> Mapping[str, Any]:
    body = dict(root._protocol())
    body.pop("protocol_id", None)
    body["version"] = VERSION
    body["successor_reason"] = "b12_qualification_external_interruption_before_any_receipt_or_authority_opening"
    body["execution_transport"] = {
        "prospective_shards": 8,
        "items_per_shard": 24,
        "model_forward_batches_per_prospective_shard": 1,
        "model_forward_batches_per_qualification_template": 1,
        "atomic_receipt_policy": "one exclusive receipt file and completion record per arm-shard",
        "recovery_policy": "no started shard is rerun",
    }
    return {**body, "protocol_id": root._digest(body)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Seal fresh b13 data without model calls.")
    parser.add_argument("--project", type=Path, default=Path("."))
    args = parser.parse_args()
    project, data = args.project.resolve(), args.project.resolve() / DATA
    if data.exists():
        raise RuntimeError("b13 data construction is consumed")
    _configure()
    interface_public: list[Mapping[str, Any]] = []
    interface_authority: list[Mapping[str, Any]] = []
    for semantic in root.CLASSES:
        for _ in range(root.QUALIFICATION_PER_CLASS):
            task, answer = _qualification_item(len(interface_public), semantic)
            interface_public.append(task)
            interface_authority.append(answer)
    development_public, development_authority = root._panel("development", root.DEVELOPMENT_PER_CLASS)
    prospective_public, prospective_authority = root._panel("prospective", root.PROSPECTIVE_PER_CLASS)
    public = {"interface": interface_public, "development": development_public, "prospective": prospective_public}
    authority = {"interface": interface_authority, "development": development_authority, "prospective": prospective_authority}
    protocol = _protocol()
    for name in public:
        root._write_rows_new(data / f"public/{name}.jsonl", public[name])
        root._write_rows_new(data / f"sealed/{name}-authority.jsonl", authority[name])
    root._write_new(data / "public/protocol.json", protocol)
    all_ids = [str(row["task_id"]) for rows in public.values() for row in rows]
    if len(set(all_ids)) != len(all_ids):
        raise RuntimeError("b13 task identifiers are not unique")
    generator = {"script": SCRIPT, "script_sha256": _sha256(Path(__file__).resolve()), "base_generator": "scripts/prepare_cognitive_binary_certificate_factorial_b12.py", "base_generator_sha256": _sha256(Path(transport.__file__).resolve()), "task_seed": TASK_SEED, "successor_reason": "b12_qualification_external_interruption_before_any_receipt_or_authority_opening"}
    seal_body = {"version": VERSION, "protocol_id": protocol["protocol_id"], "protocol_sha256": _sha256(data / "public/protocol.json"), "generator": generator, "panels": {name: {"public_path": str((DATA / f"public/{name}.jsonl").as_posix()), "public_sha256": _sha256(data / f"public/{name}.jsonl"), "authority_path": str((DATA / f"sealed/{name}-authority.jsonl").as_posix()), "authority_sha256": _sha256(data / f"sealed/{name}-authority.jsonl"), "n": len(public[name])} for name in public}}
    root._write_new(data / "public/seal.json", {**seal_body, "seal_id": root._digest(seal_body)})
    print(json.dumps({"status": "b13_data_sealed_without_model_calls", "panels": {name: len(rows) for name, rows in public.items()}, "protocol_id": protocol["protocol_id"], "model_calls": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
