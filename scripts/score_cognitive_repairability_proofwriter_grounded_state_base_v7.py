#!/usr/bin/env python3
"""One sealed frozen-base qualification for the v7 grounded-certificate study."""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import mlx.core as mx
import numpy as np
from mlx_lm import load


VERSION = "cognitive-repairability-proofwriter-grounded-state-v7"
DATA = Path("data/cognitive_core/repairability_proofwriter_grounded_state_v7")
RUN = Path("runs/cognitive_core/repairability_proofwriter_grounded_state_v7")
V4_RUN = Path("runs/cognitive_core/repairability_proofwriter_hidden_state_v4")
PRIOR = Path("data/cognitive_core/repairability_relational_binding_forced_choice_parameter_v1/public/seal.json")
FILE = "scripts/score_cognitive_repairability_proofwriter_grounded_state_base_v7.py"
SOURCES = (FILE, "scripts/prepare_cognitive_repairability_proofwriter_grounded_state_v7.py", "scripts/audit_cognitive_repairability_proofwriter_grounded_state_v7.py", "src/scientist/domains/cognitive_core/proofwriter_verified_trace_v4.py")
SYSTEM = "Solve the stated logical query using only the supplied theory and any solver-verified derivation certificate. Return only A or B."


def _canonical(value: Any) -> bytes: return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
def _digest(value: Any) -> str: return hashlib.sha256(_canonical(value)).hexdigest()
def _sha256(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def _read(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping): raise RuntimeError(f"expected JSON object: {path}")
    return value
def _rows(path: Path) -> list[Mapping[str, Any]]: return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
def _write_new(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); encoded = json.dumps(value, sort_keys=True, indent=2).encode("utf-8") + b"\n"; descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle: handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
def _write_rows_new(path: Path, values: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        for value in values: handle.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush(); os.fsync(handle.fileno())
def _terminal(project: Path, status: str, error: Exception | None = None) -> None:
    path = project / RUN / "control/terminal.json"
    if path.exists(): return
    body: dict[str, Any] = {"version": VERSION, "stage": "base-qualification", "status": status, "automatic_restarts_authorized": 0, "automatic_successors_authorized": 0}
    if error is not None: body.update(error_type=type(error).__name__, error=str(error)[:500])
    _write_new(path, {**body, "terminal_id": _digest(body)})


def _authorize(project: Path) -> tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, int]]:
    data, run = project / DATA, project / RUN
    if (run / "control/terminal.json").exists() or (run / "control/base-qualification.json").exists() or (run / "control/base-qualification-claim.json").exists(): raise RuntimeError("base attempt already consumed")
    seal, protocol = _read(data / "public/seal.json"), _read(data / "public/protocol.json")
    certificate, authorization = _read(run / "preflight/nonmodel-certificate.json"), _read(run / "control/authorization.json")
    if certificate.get("status") != "grounded_certificate_source_and_delivery_preflight_qualified_nonmodel" or certificate.get("seal_id") != seal.get("seal_id") or authorization.get("status") != "one_base_qualification_authorized" or authorization.get("certificate_id") != certificate.get("certificate_id") or authorization.get("base_qualification_attempts") != 1: raise RuntimeError("base authority is invalid")
    panel = seal.get("panels", {}).get("base_qualification", {}); public_path, authority_path = project / str(panel.get("public_path", "")), project / str(panel.get("authority_path", ""))
    if _sha256(public_path) != panel.get("public_sha256") or _sha256(authority_path) != panel.get("authority_sha256"): raise RuntimeError("base panel changed after sealing")
    prior = _read(project / PRIOR).get("model")
    if not isinstance(prior, Mapping) or prior.get("model_key") != "qwen2p5_3b" or prior.get("parameter_class") != "3B": raise RuntimeError("primary 3B model identity is invalid")
    runtime = _read(project / V4_RUN / "control/runtime-installation.json"); token_ids = runtime.get("candidate_token_ids")
    if runtime.get("status") != "runtime_installation_qualified" or not isinstance(token_ids, Mapping) or set(token_ids) != {"A", "B"}: raise RuntimeError("certified A/B token interface is invalid")
    if protocol.get("gates", {}).get("base_qualification") != {"n": 32, "correct_inclusive": [8, 24], "arm": "no_state"}: raise RuntimeError("sealed base gate is invalid")
    return seal, prior, {str(key): int(value) for key, value in token_ids.items()}


def _prompt(tokenizer: Any, task: Mapping[str, Any]) -> tuple[int, ...]:
    rendered = tokenizer.apply_chat_template([{"role": "system", "content": SYSTEM}, {"role": "user", "content": str(task["prompt_no_state"])}], tokenize=False, add_generation_prompt=True)
    return tuple(int(value) for value in tokenizer.encode(rendered, add_special_tokens=tokenizer.bos_token is None or not rendered.startswith(tokenizer.bos_token)))


def _score(model: Any, tokenizer: Any, tasks: Sequence[Mapping[str, Any]], token_ids: Mapping[str, int]) -> list[Mapping[str, Any]]:
    encoded = [_prompt(tokenizer, task) for task in tasks]
    if len(encoded) != 32 or max(map(len, encoded)) > 1024: raise RuntimeError("base prompt length gate failed")
    pad_id = getattr(tokenizer, "pad_token_id", None) or getattr(tokenizer, "eos_token_id", 0); receipts: list[Mapping[str, Any]] = []; model.eval()
    for start in range(0, len(tasks), 8):
        current, seqs = tasks[start:start + 8], encoded[start:start + 8]; lengths = [len(seq) for seq in seqs]; batch = np.full((len(seqs), max(lengths)), int(pad_id), dtype=np.int32)
        for index, seq in enumerate(seqs): batch[index, :len(seq)] = seq
        logits = model(mx.array(batch)); selected = logits[mx.arange(len(seqs)), mx.array(lengths, dtype=mx.int32) - 1]; mx.eval(selected); values = np.asarray(selected, dtype=np.float32)
        for task, vector in zip(current, values, strict=True):
            scores = {label: float(vector[token]) for label, token in token_ids.items()}; order = sorted(scores, key=lambda label: (-scores[label], label)); body = {"version": VERSION, "stage": "base-qualification", "arm": "no_state", "task_id": task["task_id"], "candidate": order[0], "top_two_margin": scores[order[0]] - scores[order[1]], "candidate_token_scores": scores, "raw_generation_used": False, "state_in_prompt": False}; receipts.append({**body, "receipt_id": _digest(body)})
        print(json.dumps({"stage": "base-qualification", "completed": min(start + len(current), len(tasks)), "total": len(tasks)}), flush=True); del logits, selected; mx.clear_cache()
    return receipts


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the one v7 frozen base qualification."); parser.add_argument("--project", type=Path, default=Path(".")); args = parser.parse_args(); project, run = args.project.resolve(), args.project.resolve() / RUN
    try:
        seal, prior, token_ids = _authorize(project)
        freeze = {"version": VERSION, "stage": "base-qualification", "source_sha256": {source: _sha256(project / source) for source in SOURCES}, "seal_id": seal["seal_id"], "panel_public_sha256": seal["panels"]["base_qualification"]["public_sha256"], "panel_authority_sha256": seal["panels"]["base_qualification"]["authority_sha256"], "model_path": str(prior["path"]), "candidate_token_ids": token_ids, "system_instruction": SYSTEM, "n": 32, "batch_size": 8, "free_text_generation": False, "positive_control_authority_opened": False, "prospective_authority_opened": False}
        _write_new(run / "control/base-qualification-code-freeze.json", {**freeze, "freeze_id": _digest(freeze)}); _write_new(run / "control/base-qualification-claim.json", {"version": VERSION, "stage": "base-qualification", "status": "claimed", "retry": False})
        panel = seal["panels"]["base_qualification"]; tasks = _rows(project / str(panel["public_path"])); authority = {str(row["task_id"]): str(row["answer"]) for row in _rows(project / str(panel["authority_path"]))}
        model, tokenizer = load(str(prior["path"])); receipts = _score(model, tokenizer, tasks, token_ids); _write_rows_new(run / "receipts/base-qualification-no-state.jsonl", receipts)
        if len(receipts) != 32 or {str(row["task_id"]) for row in receipts} != set(authority): raise RuntimeError("base receipt identity mismatch")
        correct = sum(row["candidate"] == authority[str(row["task_id"])] for row in receipts); qualified = 8 <= correct <= 24
        body = {"version": VERSION, "status": "base_qualification_qualified" if qualified else "base_qualification_not_qualified_terminal_abstention", "n": 32, "correct": correct, "accuracy": correct / 32, "correct_inclusive": [8, 24], "measurement": "direct next-token A/B likelihood; no free-text generation", "state_in_prompt": False, "positive_control_authorized": 1 if qualified else 0, "positive_control_authority_opened": False, "prospective_authority_opened": False, "automatic_restarts_authorized": 0}
        _write_new(run / "control/base-qualification.json", {**body, "screen_id": _digest(body)})
        if qualified:
            auth = {"version": VERSION, "status": "one_grounded_certificate_positive_control_authorized", "base_screen_id": _digest(body), "positive_control_attempts": 1, "prospective_attempts": 0, "automatic_restarts_authorized": 0, "automatic_successors_authorized": 0}; _write_new(run / "control/positive-control-authorization.json", {**auth, "authorization_id": _digest(auth)})
        else: _terminal(project, "base_qualification_not_qualified_terminal_abstention")
        print(json.dumps(body, sort_keys=True)); del model, tokenizer; gc.collect(); mx.clear_cache()
    except Exception as error:
        _terminal(project, "base_qualification_engineering_failure_terminal", error); raise


if __name__ == "__main__": main()
