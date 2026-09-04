#!/usr/bin/env python3
"""Execute b12 as forty bounded, atomic arm-shards and one finalizer."""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

import run_cognitive_binary_certificate_factorial_b11 as base


VERSION = "binary-certificate-factorial-b12"
DATA = Path("data/cognitive_core/binary_certificate_factorial_b12")
RUN = Path("runs/cognitive_core/binary_certificate_factorial_b12")
MODEL = "qwen2p5_3b"
ARMS = ("none", "irrelevant", "conclusion_only", "proof_prefix", "full")
SHARD_SIZE = 24
SHARD_COUNT = 8
BOOTSTRAP_SEED = 2026090130
SCRIPT = "scripts/run_cognitive_binary_certificate_factorial_b12.py"


def _sha256(path: Path) -> str:
    block = hashlib.sha256()
    with path.open("rb") as handle:
        for value in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            block.update(value)
    return block.hexdigest()


def _read(path: Path) -> Mapping[str, Any]:
    return base.common._read(path)


def _rows(path: Path) -> list[Mapping[str, Any]]:
    return base.common._rows(path)


def _configure_base() -> None:
    base.VERSION = VERSION
    base.DATA = DATA
    base.RUN = RUN
    base.BOOTSTRAP_SEED = BOOTSTRAP_SEED
    base.common.SYSTEM = base.SYSTEM
    base.common.BOOTSTRAP_SEED = BOOTSTRAP_SEED


def _implementation() -> Mapping[str, Any]:
    return {
        "version": VERSION,
        "runner": {"script": SCRIPT, "sha256": _sha256(Path(__file__).resolve())},
        "base_runner": {"script": "scripts/run_cognitive_binary_certificate_factorial_b11.py", "sha256": _sha256(Path(base.__file__).resolve())},
        "transport": {"shard_size": SHARD_SIZE, "shard_count": SHARD_COUNT, "arms": list(ARMS), "per_shard_batch_size": 12},
        "successor_reason": "b11_prospective_external_interruption_before_any_receipt_or_authority_opening",
        "no_prompt_or_analysis_change": True,
        "automatic_restarts_authorized": 0,
        "automatic_successors_authorized": 0,
    }


def _score_shard(model: Any, tokenizer: Any, rows: Sequence[Mapping[str, Any]], candidate_ids: Mapping[str, int], arm: str, shard: int) -> list[Mapping[str, Any]]:
    encoded = [base.common._chat_prompt(tokenizer, str(row["arm_prompt"]), MODEL) for row in rows]
    if len(rows) != SHARD_SIZE or max(len(value) for value in encoded) > 1536:
        raise RuntimeError("invalid prospective shard construction")
    pad = getattr(tokenizer, "pad_token_id", None) or getattr(tokenizer, "eos_token_id", 0)
    model.eval()
    receipts: list[Mapping[str, Any]] = []
    for start in range(0, len(rows), 12):
        current, sequences = rows[start : start + 12], encoded[start : start + 12]
        lengths = [len(sequence) for sequence in sequences]
        batch = np.full((len(sequences), max(lengths)), int(pad), dtype=np.int32)
        for index, sequence in enumerate(sequences):
            batch[index, : len(sequence)] = sequence
        logits = model(base.common.mx.array(batch))
        selected = logits[base.common.mx.arange(len(sequences)), base.common.mx.array(lengths, dtype=base.common.mx.int32) - 1]
        base.common.mx.eval(selected)
        values = np.asarray(selected.astype(base.common.mx.float32).tolist(), dtype=np.float32)
        for row, vector in zip(current, values, strict=True):
            scores = {candidate: float(vector[token]) for candidate, token in candidate_ids.items()}
            order = sorted(scores, key=lambda candidate: (-scores[candidate], candidate))
            body = {
                "version": VERSION,
                "model_key": MODEL,
                "stage": "prospective",
                "arm": arm,
                "shard": shard,
                "task_id": str(row["task_id"]),
                "candidate": order[0],
                "candidate_token_scores": scores,
                "top_two_margin": scores[order[0]] - scores[order[1]],
                "raw_generation_used": False,
            }
            receipts.append({**body, "receipt_id": base.common._digest(body)})
        del logits, selected
        base.common.mx.clear_cache()
    return receipts


def _preflight(project: Path) -> Mapping[str, Any]:
    return base._preflight(project)


def _ensure_implementation(project: Path) -> None:
    path = project / RUN / MODEL / "control/implementation.json"
    if not path.exists():
        value = _implementation()
        base.common._write_new(path, {**value, "implementation_id": base.common._digest(value)})


def _qualify(project: Path) -> None:
    base._qualification(project)


def _prospective_freeze(project: Path, model_manifest: Mapping[str, Any], candidate_ids: Mapping[str, int]) -> None:
    run = project / RUN / MODEL
    freeze_path = run / "control/prospective-code-freeze.json"
    if freeze_path.exists():
        frozen = _read(freeze_path)
        if dict(frozen.get("candidate_token_ids", {})) != dict(candidate_ids):
            raise RuntimeError("candidate token identities differ from prospective freeze")
        return
    seal = _read(project / DATA / "public/seal.json")
    qualification = _read(run / "results/qualification.json")
    preflight = _preflight(project)
    freeze = {
        "version": VERSION,
        "model": model_manifest,
        "runtime": base.common._runtime_manifest(),
        "candidate_token_ids": candidate_ids,
        "system_instruction": base.SYSTEM,
        "preflight_id": preflight["preflight_id"],
        "qualification_id": qualification["qualification_id"],
        "prospective_public_sha256": seal["panels"]["prospective"]["public_sha256"],
        "prospective_authority_sha256": seal["panels"]["prospective"]["authority_sha256"],
        "arms": list(ARMS),
        "n": 192,
        "shard_size": SHARD_SIZE,
        "shard_count": SHARD_COUNT,
        "authority_opened_before_receipts": False,
    }
    base.common._write_new(freeze_path, {**freeze, "freeze_id": base.common._digest(freeze)})


def _run_shard(project: Path, arm: str, shard: int) -> None:
    if arm not in ARMS or not 0 <= shard < SHARD_COUNT:
        raise ValueError("unsupported arm or shard")
    run = project / RUN / MODEL
    terminal = run / "control/prospective-terminal.json"
    if terminal.exists():
        raise RuntimeError("prospective study is terminal")
    _preflight(project)
    qualification = _read(run / "results/qualification.json")
    if qualification.get("status") != "binary_semantic_delivery_qualified" or qualification.get("prospective_authorized") is not True:
        raise RuntimeError("prospective shards require qualified binary delivery")
    start, end = shard * SHARD_SIZE, (shard + 1) * SHARD_SIZE
    seal = _read(project / DATA / "public/seal.json")
    public = _rows(project / str(seal["panels"]["prospective"]["public_path"]))
    selected = [{**row, "arm_prompt": row["prompts"][arm]} for row in public[start:end]]
    receipt_path = run / f"receipts/prospective-{arm}-shard-{shard:02d}.jsonl"
    start_path = run / f"control/shards/{arm}-shard-{shard:02d}-start.json"
    complete_path = run / f"control/shards/{arm}-shard-{shard:02d}-complete.json"
    if receipt_path.exists() and complete_path.exists():
        print(json.dumps({"status": "existing_complete_shard", "arm": arm, "shard": shard, "model_calls": 0}, sort_keys=True))
        return
    if start_path.exists() or receipt_path.exists() or complete_path.exists():
        raise RuntimeError("incomplete or inconsistent shard record; b12 prohibits reissuing a started shard")
    try:
        model, tokenizer, model_manifest, candidate_ids = base._load_frozen()
        if dict(candidate_ids) != dict(qualification["candidate_token_ids"]):
            raise RuntimeError("candidate token identities changed after qualification")
        _prospective_freeze(project, model_manifest, candidate_ids)
        started = {"version": VERSION, "arm": arm, "shard": shard, "start_index": start, "end_index_exclusive": end, "task_ids": [str(row["task_id"]) for row in selected], "authority_opened": False}
        base.common._write_new(start_path, {**started, "start_id": base.common._digest(started)})
        receipts = _score_shard(model, tokenizer, selected, candidate_ids, arm, shard)
        base.common._write_rows_new(receipt_path, receipts)
        complete = {"version": VERSION, "arm": arm, "shard": shard, "n": len(receipts), "receipt_sha256": _sha256(receipt_path), "task_ids": [str(row["task_id"]) for row in receipts], "authority_opened": False}
        base.common._write_new(complete_path, {**complete, "complete_id": base.common._digest(complete)})
        print(json.dumps({"status": "completed_shard", "arm": arm, "shard": shard, "n": len(receipts), "model_calls": len(receipts)}, sort_keys=True))
        del model, tokenizer
        gc.collect()
        base.common.mx.clear_cache()
    except Exception as error:
        failure = run / "control/prospective-terminal.json"
        if not failure.exists():
            base.common._write_new(failure, {"version": VERSION, "status": "prospective_shard_engineering_failure_no_retry", "arm": arm, "shard": shard, "error_type": type(error).__name__, "error": str(error)[:500], "automatic_restarts_authorized": 0})
        raise


def _finalize(project: Path) -> None:
    run = project / RUN / MODEL
    terminal, result_path = run / "control/prospective-terminal.json", run / "results/prospective-factorial.json"
    if terminal.exists() or result_path.exists():
        raise RuntimeError("prospective study is already terminal")
    qualification = _read(run / "results/qualification.json")
    if qualification.get("prospective_authorized") is not True:
        raise RuntimeError("unqualified model cannot be finalized")
    seal = _read(project / DATA / "public/seal.json")
    public = _rows(project / str(seal["panels"]["prospective"]["public_path"]))
    receipts: dict[str, list[Mapping[str, Any]]] = {}
    for arm in ARMS:
        arm_receipts: list[Mapping[str, Any]] = []
        for shard in range(SHARD_COUNT):
            receipt_path = run / f"receipts/prospective-{arm}-shard-{shard:02d}.jsonl"
            complete_path = run / f"control/shards/{arm}-shard-{shard:02d}-complete.json"
            if not receipt_path.exists() or not complete_path.exists():
                raise RuntimeError(f"cannot finalize: missing complete {arm} shard {shard}")
            rows = _rows(receipt_path)
            expected_ids = [str(row["task_id"]) for row in public[shard * SHARD_SIZE : (shard + 1) * SHARD_SIZE]]
            if len(rows) != SHARD_SIZE or [str(row["task_id"]) for row in rows] != expected_ids:
                raise RuntimeError(f"receipt identity failure in {arm} shard {shard}")
            arm_receipts.extend(rows)
        receipts[arm] = arm_receipts
    authority = {str(row["task_id"]): str(row["answer"]) for row in _rows(project / str(seal["panels"]["prospective"]["authority_path"]))}
    if len(authority) != 192:
        raise RuntimeError("sealed authority has unexpected size")
    comparisons = {
        "proof_prefix_minus_conclusion_only": base.common._comparison(receipts["proof_prefix"], receipts["conclusion_only"], authority, seed_suffix="b12:prefix-conclusion"),
        "proof_prefix_minus_irrelevant": base.common._comparison(receipts["proof_prefix"], receipts["irrelevant"], authority, seed_suffix="b12:prefix-irrelevant"),
        "full_minus_conclusion_only": base.common._comparison(receipts["full"], receipts["conclusion_only"], authority, seed_suffix="b12:full-conclusion"),
    }
    secondary = {name: comparisons[name] for name in ("proof_prefix_minus_irrelevant", "full_minus_conclusion_only")}
    adjusted = base.common._holm(secondary)
    primary = comparisons["proof_prefix_minus_conclusion_only"]
    supports_prefix = primary["exact_two_sided_mcnemar_p"] < 0.05 and primary["paired_BCa_bootstrap_95"][0] > 0 and comparisons["proof_prefix_minus_irrelevant"]["paired_BCa_bootstrap_95"][0] > 0
    correct = {arm: sum(row["candidate"] == authority[str(row["task_id"])] for row in values) for arm, values in receipts.items()}
    body = {"version": VERSION, "model_key": MODEL, "status": "terminal_scored_no_audit_or_restart", "n": len(authority), "correct": correct, "accuracy": {arm: correct[arm] / len(authority) for arm in ARMS}, "primary_comparison": primary, "secondary_comparisons": {name: {**result, "holm_adjusted_p": adjusted[name]} for name, result in secondary.items()}, "interpretation": "limited_binary_system_level_proof_prefix_support" if supports_prefix else "external_answer_provision_or_no_binary_prefix_support_not_resolved", "claim_boundary": "This is a frozen Qwen2.5-3B binary system result. It does not test open-world unknown cases, internal cognition, or a universal repair mechanism.", "authority_opened_after_all_prospective_receipts": True, "automatic_restarts_authorized": 0}
    base.common._write_new(result_path, {**body, "result_id": base.common._digest(body)})
    base.common._write_new(terminal, {"version": VERSION, "status": "prospective_terminal", "automatic_restarts_authorized": 0})
    print(json.dumps(body, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run b12 one stage or one predeclared arm-shard.")
    parser.add_argument("stage", choices=("preflight", "qualify", "arm", "finalize"))
    parser.add_argument("--arm", choices=ARMS)
    parser.add_argument("--shard", type=int)
    parser.add_argument("--project", type=Path, default=Path("."))
    args = parser.parse_args()
    _configure_base()
    project = args.project.resolve()
    _ensure_implementation(project)
    if args.stage == "preflight":
        print(json.dumps(_preflight(project), sort_keys=True))
    elif args.stage == "qualify":
        _qualify(project)
    elif args.stage == "arm":
        if args.arm is None or args.shard is None:
            raise RuntimeError("arm stage requires --arm and --shard")
        _run_shard(project, args.arm, args.shard)
    else:
        _finalize(project)


if __name__ == "__main__":
    main()
