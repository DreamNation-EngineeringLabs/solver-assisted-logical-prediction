#!/usr/bin/env python3
"""One terminal depth-4 prospective comparison for v7."""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
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
FILE = "scripts/score_cognitive_repairability_proofwriter_grounded_state_prospective_v7.py"
SOURCES = (FILE, "scripts/prepare_cognitive_repairability_proofwriter_grounded_state_v7.py", "scripts/audit_cognitive_repairability_proofwriter_grounded_state_v7.py", "scripts/score_cognitive_repairability_proofwriter_grounded_state_base_v7.py", "scripts/score_cognitive_repairability_proofwriter_grounded_state_positive_v7.py", "src/scientist/domains/cognitive_core/proofwriter_verified_trace_v4.py")
SYSTEM = "Solve the stated logical query using only the supplied theory and any solver-verified derivation certificate. Return only A or B."
ARMS = ("no_state", "verified_state", "irrelevant_state")
PROMPT_KEYS = {"no_state": "prompt_no_state", "verified_state": "prompt_verified_state", "irrelevant_state": "prompt_irrelevant_state"}


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
    body: dict[str, Any] = {"version": VERSION, "stage": "prospective", "status": status, "automatic_restarts_authorized": 0, "automatic_successors_authorized": 0}
    if error is not None: body.update(error_type=type(error).__name__, error=str(error)[:500])
    _write_new(path, {**body, "terminal_id": _digest(body)})


def _authorize(project: Path) -> tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, int]]:
    data, run = project / DATA, project / RUN
    if (run / "control/terminal.json").exists() or (run / "results/terminal-score.json").exists() or (run / "control/prospective-claim.json").exists(): raise RuntimeError("prospective attempt already consumed")
    seal, protocol = _read(data / "public/seal.json"), _read(data / "public/protocol.json")
    positive, authorization = _read(run / "control/positive-control.json"), _read(run / "control/prospective-authorization.json")
    if positive.get("status") != "grounded_certificate_positive_control_qualified" or authorization.get("status") != "one_grounded_certificate_prospective_comparison_authorized" or authorization.get("positive_control_gate_id") != positive.get("gate_id") or authorization.get("prospective_attempts") != 1: raise RuntimeError("prospective authority is invalid")
    panel = seal.get("panels", {}).get("prospective", {}); public_path, authority_path = project / str(panel.get("public_path", "")), project / str(panel.get("authority_path", ""))
    if _sha256(public_path) != panel.get("public_sha256") or _sha256(authority_path) != panel.get("authority_sha256"): raise RuntimeError("prospective panel changed after sealing")
    prior = _read(project / PRIOR).get("model")
    if not isinstance(prior, Mapping) or prior.get("model_key") != "qwen2p5_3b" or prior.get("parameter_class") != "3B": raise RuntimeError("primary 3B model identity is invalid")
    runtime = _read(project / V4_RUN / "control/runtime-installation.json"); token_ids = runtime.get("candidate_token_ids")
    if runtime.get("status") != "runtime_installation_qualified" or not isinstance(token_ids, Mapping) or set(token_ids) != {"A", "B"}: raise RuntimeError("certified A/B token interface is invalid")
    expected = {"n": 192, "primary_comparison": "verified_state_minus_irrelevant_state", "exact_two_sided_mcnemar_p": 0.05, "boundary_aware_paired_lower_bound_above_zero": True, "verified_must_not_score_below_no_state": True}
    if protocol.get("gates", {}).get("prospective") != expected: raise RuntimeError("sealed prospective rule is invalid")
    return seal, prior, {str(key): int(value) for key, value in token_ids.items()}


def _prompt(tokenizer: Any, task: Mapping[str, Any], arm: str) -> tuple[int, ...]:
    rendered = tokenizer.apply_chat_template([{"role": "system", "content": SYSTEM}, {"role": "user", "content": str(task[PROMPT_KEYS[arm]])}], tokenize=False, add_generation_prompt=True)
    return tuple(int(value) for value in tokenizer.encode(rendered, add_special_tokens=tokenizer.bos_token is None or not rendered.startswith(tokenizer.bos_token)))


def _score(model: Any, tokenizer: Any, tasks: Sequence[Mapping[str, Any]], token_ids: Mapping[str, int], arm: str) -> list[Mapping[str, Any]]:
    encoded = [_prompt(tokenizer, task, arm) for task in tasks]
    if len(encoded) != 192 or max(map(len, encoded)) > 1024: raise RuntimeError(f"{arm} prospective prompt length gate failed")
    pad_id = getattr(tokenizer, "pad_token_id", None) or getattr(tokenizer, "eos_token_id", 0); receipts: list[Mapping[str, Any]] = []; model.eval()
    for start in range(0, len(tasks), 8):
        current, seqs = tasks[start:start + 8], encoded[start:start + 8]; lengths = [len(seq) for seq in seqs]; batch = np.full((len(seqs), max(lengths)), int(pad_id), dtype=np.int32)
        for index, seq in enumerate(seqs): batch[index, :len(seq)] = seq
        logits = model(mx.array(batch)); selected = logits[mx.arange(len(seqs)), mx.array(lengths, dtype=mx.int32) - 1]; mx.eval(selected); values = np.asarray(selected, dtype=np.float32)
        for task, vector in zip(current, values, strict=True):
            scores = {label: float(vector[token]) for label, token in token_ids.items()}; order = sorted(scores, key=lambda label: (-scores[label], label)); body = {"version": VERSION, "stage": "prospective", "arm": arm, "task_id": task["task_id"], "candidate": order[0], "top_two_margin": scores[order[0]] - scores[order[1]], "candidate_token_scores": scores, "raw_generation_used": False, "state_in_prompt": arm != "no_state"}; receipts.append({**body, "receipt_id": _digest(body)})
        print(json.dumps({"stage": "prospective", "arm": arm, "completed": min(start + len(current), len(tasks)), "total": len(tasks)}), flush=True); del logits, selected; mx.clear_cache()
    return receipts


def _wilson(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    probability = k / n; denominator = 1 + z * z / n; center = (probability + z * z / (2 * n)) / denominator; radius = z * math.sqrt(probability * (1 - probability) / n + z * z / (4 * n * n)) / denominator
    return max(0.0, center - radius), min(1.0, center + radius)


def _comparison(verified: Sequence[Mapping[str, Any]], control: Sequence[Mapping[str, Any]], authority: Mapping[str, str]) -> Mapping[str, Any]:
    left, right = {str(row["task_id"]): row for row in verified}, {str(row["task_id"]): row for row in control}
    if set(left) != set(authority) or set(right) != set(authority): raise RuntimeError("paired prospective receipt identities are invalid")
    ids = sorted(authority); real = [left[item]["candidate"] == authority[item] for item in ids]; other = [right[item]["candidate"] == authority[item] for item in ids]; favorable = sum(a and not b for a, b in zip(real, other, strict=True)); adverse = sum(b and not a for a, b in zip(real, other, strict=True)); discordant = favorable + adverse; exact = 1.0 if discordant == 0 else min(1.0, 2 * sum(math.comb(discordant, index) for index in range(min(favorable, adverse) + 1)) / (2 ** discordant)); favorable_interval, adverse_interval = _wilson(favorable, len(ids)), _wilson(adverse, len(ids))
    return {"verified_correct": sum(real), "control_correct": sum(other), "correct_gain": sum(real) - sum(other), "effect": (sum(real) - sum(other)) / len(ids), "verified_only_correct": favorable, "control_only_correct": adverse, "discordant": discordant, "exact_two_sided_mcnemar_p": exact, "conservative_paired_category_wilson_envelope_95": [favorable_interval[0] - adverse_interval[1], favorable_interval[1] - adverse_interval[0]], "interval_note": "A boundary-aware conservative paired-category sensitivity envelope, computed from Wilson bounds for treatment-only and control-only correctness; it is not a degenerate normal interval."}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the one v7 terminal prospective comparison."); parser.add_argument("--project", type=Path, default=Path(".")); args = parser.parse_args(); project, run = args.project.resolve(), args.project.resolve() / RUN
    try:
        seal, prior, token_ids = _authorize(project)
        freeze = {"version": VERSION, "stage": "prospective", "source_sha256": {source: _sha256(project / source) for source in SOURCES}, "seal_id": seal["seal_id"], "panel_public_sha256": seal["panels"]["prospective"]["public_sha256"], "panel_authority_sha256": seal["panels"]["prospective"]["authority_sha256"], "model_path": str(prior["path"]), "candidate_token_ids": token_ids, "system_instruction": SYSTEM, "arms": ARMS, "n": 192, "batch_size": 8, "support_rule": "verified certificate exceeds irrelevant certificate by exact paired McNemar p < 0.05 and a positive conservative paired-category Wilson-envelope lower bound; verified certificate does not score below no certificate", "free_text_generation": False, "prospective_authority_opened_at_claim": True}
        _write_new(run / "control/prospective-code-freeze.json", {**freeze, "freeze_id": _digest(freeze)}); _write_new(run / "control/prospective-claim.json", {"version": VERSION, "stage": "prospective", "status": "claimed", "retry": False, "prospective_authority_opened": True})
        panel = seal["panels"]["prospective"]; tasks = _rows(project / str(panel["public_path"])); authority = {str(row["task_id"]): str(row["answer"]) for row in _rows(project / str(panel["authority_path"]))}
        model, tokenizer = load(str(prior["path"])); receipts = {arm: _score(model, tokenizer, tasks, token_ids, arm) for arm in ARMS}
        for arm in ARMS: _write_rows_new(run / f"receipts/prospective-{arm}.jsonl", receipts[arm])
        correct = {arm: sum(row["candidate"] == authority[str(row["task_id"])] for row in receipts[arm]) for arm in ARMS}; versus_irrelevant, versus_no_state = _comparison(receipts["verified_state"], receipts["irrelevant_state"], authority), _comparison(receipts["verified_state"], receipts["no_state"], authority)
        supported = versus_irrelevant["exact_two_sided_mcnemar_p"] < 0.05 and versus_irrelevant["conservative_paired_category_wilson_envelope_95"][0] > 0 and correct["verified_state"] >= correct["no_state"]
        body = {"version": VERSION, "status": "terminal_scored_no_audit_or_restart", "n": 192, "correct": correct, "accuracy": {arm: correct[arm] / 192 for arm in ARMS}, "verified_state_vs_irrelevant_state": versus_irrelevant, "verified_state_vs_no_state": versus_no_state, "support_rule": "verified certificate exceeds irrelevant certificate by exact paired McNemar p < 0.05 and a positive conservative paired-category Wilson-envelope lower bound; verified certificate does not score below no certificate", "interpretation": "grounded_explicit_state_repair_supported_in_3b_envelope" if supported else "grounded_explicit_state_repair_not_supported_in_3b_envelope", "transport_requirement": "one fresh Qwen3-1.7B replication before any transport claim", "prospective_authority_opened_at_terminal_scoring_only": True, "automatic_restarts_authorized": 0}
        _write_new(run / "results/terminal-score.json", {**body, "result_id": _digest(body)}); _terminal(project, "terminal_scored_no_audit_or_restart"); print(json.dumps(body, sort_keys=True)); del model, tokenizer; gc.collect(); mx.clear_cache()
    except Exception as error:
        _terminal(project, "terminal_scoring_engineering_failure_no_retry", error); raise


if __name__ == "__main__": main()
