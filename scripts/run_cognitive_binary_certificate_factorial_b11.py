#!/usr/bin/env python3
"""Run the one-attempt Qwen2.5-3B binary certificate factorial b11."""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

import run_cognitive_solver_assisted_certificate_factorial_v8 as common


VERSION = "binary-certificate-factorial-b11"
DATA = Path("data/cognitive_core/binary_certificate_factorial_b11")
RUN = Path("runs/cognitive_core/binary_certificate_factorial_b11")
MODEL = "qwen2p5_3b"
ARMS = ("none", "irrelevant", "conclusion_only", "proof_prefix", "full")
BOOTSTRAP_SEED = 2026090128
SYSTEM = "Use only the supplied logical facts, rules, and solver record. Answer exactly Yes or No."
CANDIDATES = ("Yes", "No")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(path: Path) -> Mapping[str, Any]:
    return common._read(path)


def _rows(path: Path) -> list[Mapping[str, Any]]:
    return common._rows(path)


def _candidate_ids(tokenizer: Any) -> Mapping[str, int]:
    result: dict[str, int] = {}
    for candidate in CANDIDATES:
        encoded = tokenizer.encode(candidate, add_special_tokens=False)
        if len(encoded) != 1:
            raise RuntimeError(f"{candidate} is not a single candidate token")
        result[candidate] = int(encoded[0])
    if len(set(result.values())) != len(result):
        raise RuntimeError("Yes and No do not have distinct token identities")
    return result


def _load_frozen() -> tuple[Any, Any, Mapping[str, Any], Mapping[str, int]]:
    import mlx.core as mx
    from mlx_lm import load

    common.mx = mx
    manifest = common._model_manifest(MODEL)
    model, tokenizer = load(str(manifest["path"]), tokenizer_config={"trust_remote_code": False})
    return model, tokenizer, manifest, _candidate_ids(tokenizer)


def _score(
    *,
    model: Any,
    tokenizer: Any,
    rows: Sequence[Mapping[str, Any]],
    prompt_key: str,
    candidate_ids: Mapping[str, int],
    stage: str,
    arm: str,
) -> list[Mapping[str, Any]]:
    encoded = [common._chat_prompt(tokenizer, str(row[prompt_key]), MODEL) for row in rows]
    if not encoded or max(len(item) for item in encoded) > 1536:
        raise RuntimeError(f"{stage}/{arm} prompt-length gate failed")
    pad = getattr(tokenizer, "pad_token_id", None) or getattr(tokenizer, "eos_token_id", 0)
    model.eval()
    receipts: list[Mapping[str, Any]] = []
    for start in range(0, len(rows), 4):
        current, sequences = rows[start : start + 4], encoded[start : start + 4]
        lengths = [len(sequence) for sequence in sequences]
        batch = np.full((len(sequences), max(lengths)), int(pad), dtype=np.int32)
        for index, sequence in enumerate(sequences):
            batch[index, : len(sequence)] = sequence
        logits = model(common.mx.array(batch))
        selected = logits[common.mx.arange(len(sequences)), common.mx.array(lengths, dtype=common.mx.int32) - 1]
        common.mx.eval(selected)
        values = np.asarray(selected.astype(common.mx.float32).tolist(), dtype=np.float32)
        for row, vector in zip(current, values, strict=True):
            scores = {candidate: float(vector[token]) for candidate, token in candidate_ids.items()}
            order = sorted(scores, key=lambda candidate: (-scores[candidate], candidate))
            body = {
                "version": VERSION,
                "model_key": MODEL,
                "stage": stage,
                "arm": arm,
                "task_id": str(row["task_id"]),
                "candidate": order[0],
                "candidate_token_scores": scores,
                "top_two_margin": scores[order[0]] - scores[order[1]],
                "raw_generation_used": False,
            }
            receipts.append({**body, "receipt_id": common._digest(body)})
        print(json.dumps({"stage": stage, "arm": arm, "completed": min(start + len(current), len(rows)), "total": len(rows)}), flush=True)
        del logits, selected
        common.mx.clear_cache()
    return receipts


def _preflight(project: Path) -> Mapping[str, Any]:
    data = project / DATA
    seal, protocol = _read(data / "public/seal.json"), _read(data / "public/protocol.json")
    if protocol.get("version") != VERSION or seal.get("protocol_id") != protocol.get("protocol_id"):
        raise RuntimeError("b11 protocol binding is invalid")
    if protocol.get("execution_policy", {}).get("automatic_restarts_authorized") != 0:
        raise RuntimeError("automatic restarts are prohibited")
    output = project / RUN / MODEL / "control/preflight.json"
    if output.exists():
        return _read(output)
    public = _rows(project / str(seal["panels"]["development"]["public_path"]))
    if len(public) != 72 or any(set(row["prompts"]) != set(ARMS) for row in public):
        raise RuntimeError("development panel is invalid")
    maximum = max(len(str(prompt)) for row in public for prompt in row["prompts"].values())
    body = {"version": VERSION, "model_key": MODEL, "status": "nonmodel_preflight_passed", "development_items": len(public), "arms": list(ARMS), "maximum_prompt_characters": maximum, "authority_opened": False, "model_calls": 0}
    common._write_new(output, {**body, "preflight_id": common._digest(body)})
    return _read(output)


def _implementation() -> Mapping[str, Any]:
    return {
        "version": VERSION,
        "runner": {"script": "scripts/run_cognitive_binary_certificate_factorial_b11.py", "sha256": _sha256(Path(__file__).resolve())},
        "candidate_response": {"labels": list(CANDIDATES), "scoring": "next_token_logit_argmax", "free_text_generation": False},
        "sole_scope_change_from_v8": "fresh binary direct-Yes-No experiment; open-world unknown is excluded rather than treated as a failed arm",
        "automatic_restarts_authorized": 0,
        "automatic_successors_authorized": 0,
    }


def _qualification(project: Path) -> None:
    run = project / RUN / MODEL
    terminal, result_path = run / "control/qualification-terminal.json", run / "results/qualification.json"
    if terminal.exists() or result_path.exists():
        raise RuntimeError("qualification attempt already consumed")
    _preflight(project)
    seal = _read(project / DATA / "public/seal.json")
    rows = _rows(project / str(seal["panels"]["interface"]["public_path"]))
    authority_path = project / str(seal["panels"]["interface"]["authority_path"])
    try:
        model, tokenizer, model_manifest, candidate_ids = _load_frozen()
        freeze = {"version": VERSION, "model": model_manifest, "runtime": common._runtime_manifest(), "candidate_token_ids": candidate_ids, "system_instruction": SYSTEM, "interface_public_sha256": seal["panels"]["interface"]["public_sha256"], "interface_authority_sha256": seal["panels"]["interface"]["authority_sha256"], "authority_opened_before_receipts": False}
        common._write_new(run / "control/qualification-code-freeze.json", {**freeze, "freeze_id": common._digest(freeze)})
        direct = _score(model=model, tokenizer=tokenizer, rows=rows, prompt_key="direct_prompt", candidate_ids=candidate_ids, stage="qualification", arm="direct")
        reordered = _score(model=model, tokenizer=tokenizer, rows=rows, prompt_key="reordered_prompt", candidate_ids=candidate_ids, stage="qualification", arm="reordered")
        common._write_rows_new(run / "receipts/qualification-direct.jsonl", direct)
        common._write_rows_new(run / "receipts/qualification-reordered.jsonl", reordered)
        authority = {str(row["task_id"]): row for row in _rows(authority_path)}
        direct_by_id = {str(row["task_id"]): row for row in direct}
        reordered_by_id = {str(row["task_id"]): row for row in reordered}
        if set(authority) != set(direct_by_id) or set(authority) != set(reordered_by_id):
            raise RuntimeError("qualification receipts are incomplete")
        direct_correct = sum(direct_by_id[key]["candidate"] == authority[key]["answer"] for key in authority)
        reordered_correct = sum(reordered_by_id[key]["candidate"] == authority[key]["answer"] for key in authority)
        agreement = sum(direct_by_id[key]["candidate"] == reordered_by_id[key]["candidate"] for key in authority)
        per_class = {
            semantic: {
                "n": sum(row["semantic_class"] == semantic for row in authority.values()),
                "direct_correct": sum(direct_by_id[key]["candidate"] == authority[key]["answer"] for key, row in authority.items() if row["semantic_class"] == semantic),
                "reordered_correct": sum(reordered_by_id[key]["candidate"] == authority[key]["answer"] for key, row in authority.items() if row["semantic_class"] == semantic),
            }
            for semantic in ("entailed", "contradicted")
        }
        qualified = direct_correct >= 27 and reordered_correct >= 27 and agreement >= 32 and all(value["direct_correct"] >= 12 and value["reordered_correct"] >= 12 for value in per_class.values())
        body = {"version": VERSION, "model_key": MODEL, "status": "binary_semantic_delivery_qualified" if qualified else "binary_semantic_delivery_not_qualified", "n": len(authority), "direct_correct": direct_correct, "reordered_correct": reordered_correct, "candidate_agreement": agreement, "per_class": per_class, "candidate_token_ids": candidate_ids, "prospective_authorized": qualified, "authority_opened_after_all_receipts": True, "failure_interpretation": None if qualified else "binary semantic delivery failure, not a certificate-treatment null"}
        common._write_new(result_path, {**body, "qualification_id": common._digest(body)})
        common._write_new(terminal, {"version": VERSION, "status": "qualification_terminal", "qualified": qualified, "automatic_restarts_authorized": 0})
        print(json.dumps(body, sort_keys=True))
        del model, tokenizer
        gc.collect()
        common.mx.clear_cache()
    except Exception as error:
        if not terminal.exists():
            common._write_new(terminal, {"version": VERSION, "status": "qualification_engineering_failure_no_retry", "error_type": type(error).__name__, "error": str(error)[:500], "automatic_restarts_authorized": 0})
        raise


def _prospective(project: Path) -> None:
    run = project / RUN / MODEL
    terminal, result_path = run / "control/prospective-terminal.json", run / "results/prospective-factorial.json"
    if terminal.exists() or result_path.exists():
        raise RuntimeError("prospective attempt already consumed")
    preflight = _preflight(project)
    qualification = _read(run / "results/qualification.json")
    if qualification.get("status") != "binary_semantic_delivery_qualified" or qualification.get("prospective_authorized") is not True:
        raise RuntimeError("prospective run requires binary semantic delivery qualification")
    seal = _read(project / DATA / "public/seal.json")
    rows = _rows(project / str(seal["panels"]["prospective"]["public_path"]))
    if len(rows) != 192 or any(set(row["prompts"]) != set(ARMS) for row in rows):
        raise RuntimeError("prospective panel is invalid")
    try:
        model, tokenizer, model_manifest, candidate_ids = _load_frozen()
        if dict(candidate_ids) != dict(qualification["candidate_token_ids"]):
            raise RuntimeError("candidate token identity changed after qualification")
        freeze = {"version": VERSION, "model": model_manifest, "runtime": common._runtime_manifest(), "candidate_token_ids": candidate_ids, "system_instruction": SYSTEM, "preflight_id": preflight["preflight_id"], "qualification_id": qualification["qualification_id"], "prospective_public_sha256": seal["panels"]["prospective"]["public_sha256"], "prospective_authority_sha256": seal["panels"]["prospective"]["authority_sha256"], "arms": list(ARMS), "n": len(rows), "authority_opened_before_receipts": False}
        common._write_new(run / "control/prospective-code-freeze.json", {**freeze, "freeze_id": common._digest(freeze)})
        receipts: dict[str, list[Mapping[str, Any]]] = {}
        for arm in ARMS:
            arm_rows = [{**row, "arm_prompt": row["prompts"][arm]} for row in rows]
            receipts[arm] = _score(model=model, tokenizer=tokenizer, rows=arm_rows, prompt_key="arm_prompt", candidate_ids=candidate_ids, stage="prospective", arm=arm)
            common._write_rows_new(run / f"receipts/prospective-{arm}.jsonl", receipts[arm])
        authority = {str(row["task_id"]): str(row["answer"]) for row in _rows(project / str(seal["panels"]["prospective"]["authority_path"]))}
        if len(authority) != 192:
            raise RuntimeError("sealed authority has unexpected size")
        comparisons = {
            "proof_prefix_minus_conclusion_only": common._comparison(receipts["proof_prefix"], receipts["conclusion_only"], authority, seed_suffix="b11:prefix-conclusion"),
            "proof_prefix_minus_irrelevant": common._comparison(receipts["proof_prefix"], receipts["irrelevant"], authority, seed_suffix="b11:prefix-irrelevant"),
            "full_minus_conclusion_only": common._comparison(receipts["full"], receipts["conclusion_only"], authority, seed_suffix="b11:full-conclusion"),
        }
        secondary = {name: comparisons[name] for name in ("proof_prefix_minus_irrelevant", "full_minus_conclusion_only")}
        adjusted = common._holm(secondary)
        primary = comparisons["proof_prefix_minus_conclusion_only"]
        supports_prefix = primary["exact_two_sided_mcnemar_p"] < 0.05 and primary["paired_BCa_bootstrap_95"][0] > 0 and comparisons["proof_prefix_minus_irrelevant"]["paired_BCa_bootstrap_95"][0] > 0
        correct = {arm: sum(row["candidate"] == authority[str(row["task_id"])] for row in values) for arm, values in receipts.items()}
        body = {"version": VERSION, "model_key": MODEL, "status": "terminal_scored_no_audit_or_restart", "n": len(authority), "correct": correct, "accuracy": {arm: correct[arm] / len(authority) for arm in ARMS}, "primary_comparison": primary, "secondary_comparisons": {name: {**result, "holm_adjusted_p": adjusted[name]} for name, result in secondary.items()}, "interpretation": "limited_binary_system_level_proof_prefix_support" if supports_prefix else "external_answer_provision_or_no_binary_prefix_support_not_resolved", "claim_boundary": "This is a frozen Qwen2.5-3B binary system result. It does not test open-world unknown cases, internal cognition, or a universal repair mechanism.", "authority_opened_after_all_prospective_receipts": True, "automatic_restarts_authorized": 0}
        common._write_new(result_path, {**body, "result_id": common._digest(body)})
        common._write_new(terminal, {"version": VERSION, "status": "prospective_terminal", "automatic_restarts_authorized": 0})
        print(json.dumps(body, sort_keys=True))
        del model, tokenizer
        gc.collect()
        common.mx.clear_cache()
    except Exception as error:
        if not terminal.exists():
            common._write_new(terminal, {"version": VERSION, "status": "prospective_engineering_failure_no_retry", "error_type": type(error).__name__, "error": str(error)[:500], "automatic_restarts_authorized": 0})
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Run exactly one binary factorial b11 stage.")
    parser.add_argument("stage", choices=("preflight", "qualify", "prospective"))
    parser.add_argument("--project", type=Path, default=Path("."))
    args = parser.parse_args()
    common.SYSTEM = SYSTEM
    common.BOOTSTRAP_SEED = BOOTSTRAP_SEED
    run = args.project.resolve() / RUN / MODEL
    implementation = run / "control/implementation.json"
    if not implementation.exists():
        value = _implementation()
        common._write_new(implementation, {**value, "implementation_id": common._digest(value)})
    if args.stage == "preflight":
        print(json.dumps(_preflight(args.project.resolve()), sort_keys=True))
    elif args.stage == "qualify":
        _qualification(args.project.resolve())
    else:
        _prospective(args.project.resolve())


if __name__ == "__main__":
    main()
