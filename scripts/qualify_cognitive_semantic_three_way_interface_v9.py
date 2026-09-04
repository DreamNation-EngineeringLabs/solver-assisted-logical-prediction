#!/usr/bin/env python3
"""One fresh semantic-token delivery qualification for the local 3B model."""
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


VERSION = "semantic-three-way-interface-qualification-v9"
SOURCE_DATA = Path("data/cognitive_core/solver_assisted_certificate_factorial_v8")
RUN = Path("runs/cognitive_core/semantic_three_way_interface_v9/qwen2p5_3b")
MODEL_PATH = Path("/Users/krishnachaitanya/.cache/huggingface/hub/models--mlx-community--Qwen2.5-3B-Instruct-4bit/snapshots/4f83f8f146fdf28b512a06562b671d7af4fab457")
SYSTEM = "Use only the stated logical facts and rules. Answer exactly Yes, No, or Unknown."
CANDIDATES = ("Yes", "No", "Unknown")
SEMANTIC_WORD = {"entailed": "Yes", "contradicted": "No", "unknown": "Unknown"}


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _sha256(path: Path) -> str:
    block = hashlib.sha256()
    with path.open("rb") as handle:
        for payload in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            block.update(payload)
    return block.hexdigest()


def _read(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise RuntimeError(f"expected object at {path}")
    return value


def _rows(path: Path) -> list[Mapping[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _write_new(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(body)
        handle.flush()
        os.fsync(handle.fileno())


def _write_rows_new(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _semantic_prompt(v8_prompt: str, template: str) -> str:
    marker = "\n\nA = entailed.\nB = contradicted.\nC = unknown.\nAnswer:"
    if marker not in v8_prompt:
        raise RuntimeError("source interface prompt lacks the expected v8 response suffix")
    question = v8_prompt.removesuffix(marker)
    if template == "direct":
        suffix = "\n\nReply with exactly one semantic word: Yes if the query follows, No if its inverse follows, or Unknown if neither follows.\nAnswer:"
    elif template == "reordered":
        suffix = "\n\nChoose one word only. Unknown means neither polarity follows; No means the inverse follows; Yes means the query follows.\nAnswer:"
    else:
        raise ValueError("unknown semantic template")
    return question + suffix


def _chat(tokenizer: Any, prompt: str) -> tuple[int, ...]:
    rendered = tokenizer.apply_chat_template([{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True)
    return tuple(int(token) for token in tokenizer.encode(rendered, add_special_tokens=tokenizer.bos_token is None or not rendered.startswith(tokenizer.bos_token)))


def _candidate_ids(tokenizer: Any) -> Mapping[str, int]:
    values: dict[str, int] = {}
    for candidate in CANDIDATES:
        ids = tokenizer.encode(candidate, add_special_tokens=False)
        if len(ids) != 1:
            raise RuntimeError(f"semantic candidate is not one token: {candidate}")
        values[candidate] = int(ids[0])
    if len(set(values.values())) != len(values):
        raise RuntimeError("semantic candidates do not have distinct token identities")
    return values


def _score(model: Any, tokenizer: Any, rows: Sequence[Mapping[str, Any]], source_key: str, template: str, candidate_ids: Mapping[str, int]) -> list[Mapping[str, Any]]:
    prompts = [_chat(tokenizer, _semantic_prompt(str(row[f"{source_key}_prompt"]), template),) for row in rows]
    if max(len(value) for value in prompts) > 1024:
        raise RuntimeError("semantic interface prompt length exceeds qualified context")
    pad = getattr(tokenizer, "pad_token_id", None) or getattr(tokenizer, "eos_token_id", 0)
    receipts: list[Mapping[str, Any]] = []
    model.eval()
    for start in range(0, len(rows), 4):
        current, sequences = rows[start : start + 4], prompts[start : start + 4]
        lengths = [len(sequence) for sequence in sequences]
        batch = np.full((len(sequences), max(lengths)), int(pad), dtype=np.int32)
        for index, sequence in enumerate(sequences):
            batch[index, : len(sequence)] = sequence
        logits = model(mx.array(batch))
        selected = logits[mx.arange(len(sequences)), mx.array(lengths, dtype=mx.int32) - 1]
        mx.eval(selected)
        for row, vector in zip(current, np.asarray(selected, dtype=np.float32), strict=True):
            scores = {word: float(vector[token]) for word, token in candidate_ids.items()}
            ordered = sorted(scores, key=lambda word: (-scores[word], word))
            body = {"version": VERSION, "task_id": str(row["task_id"]), "template": template, "candidate": ordered[0], "candidate_token_scores": scores, "top_two_margin": scores[ordered[0]] - scores[ordered[1]], "raw_generation_used": False}
            receipts.append({**body, "receipt_id": _digest(body)})
        print(json.dumps({"template": template, "completed": min(start + len(current), len(rows)), "total": len(rows)}), flush=True)
        del logits, selected
        mx.clear_cache()
    return receipts


def main() -> None:
    parser = argparse.ArgumentParser(description="Qualify semantic Yes/No/Unknown token delivery once.")
    parser.add_argument("--project", type=Path, default=Path("."))
    args = parser.parse_args()
    project, run = args.project.resolve(), args.project.resolve() / RUN
    terminal, result_path = run / "control/terminal.json", run / "results/qualification.json"
    if terminal.exists() or result_path.exists():
        raise RuntimeError("semantic-token qualification attempt already consumed")
    source = project / SOURCE_DATA
    seal = _read(source / "public/seal.json")
    rows = _rows(project / str(seal["panels"]["interface"]["public_path"]))
    if len(rows) != 36:
        raise RuntimeError("source screen length is invalid")
    authority_path = project / str(seal["panels"]["interface"]["authority_path"])
    try:
        model, tokenizer = load(str(MODEL_PATH), tokenizer_config={"trust_remote_code": False})
        candidate_ids = _candidate_ids(tokenizer)
        model_freeze = {"version": VERSION, "model": {"repository": "mlx-community/Qwen2.5-3B-Instruct-4bit", "revision": "4f83f8f146fdf28b512a06562b671d7af4fab457", "path": str(MODEL_PATH), "config_sha256": _sha256(MODEL_PATH / "config.json"), "weights_sha256": _sha256(MODEL_PATH / "model.safetensors")}, "candidate_token_ids": candidate_ids, "templates": ["direct", "reordered"], "source_interface_sha256": seal["panels"]["interface"]["public_sha256"], "authority_opened_before_receipts": False}
        _write_new(run / "control/code-freeze.json", {**model_freeze, "freeze_id": _digest(model_freeze)})
        direct = _score(model, tokenizer, rows, "normal", "direct", candidate_ids)
        reordered = _score(model, tokenizer, rows, "normal", "reordered", candidate_ids)
        _write_rows_new(run / "receipts/direct.jsonl", direct)
        _write_rows_new(run / "receipts/reordered.jsonl", reordered)
        authority = {str(row["task_id"]): row for row in _rows(authority_path)}
        direct_by_id = {str(row["task_id"]): row for row in direct}
        reordered_by_id = {str(row["task_id"]): row for row in reordered}
        expected = {task_id: SEMANTIC_WORD[str(row["semantic_class"])] for task_id, row in authority.items()}
        direct_correct = sum(direct_by_id[key]["candidate"] == expected[key] for key in expected)
        reordered_correct = sum(reordered_by_id[key]["candidate"] == expected[key] for key in expected)
        agreement = sum(direct_by_id[key]["candidate"] == reordered_by_id[key]["candidate"] for key in expected)
        per_class = {semantic: {"n": 12, "direct_correct": sum(direct_by_id[key]["candidate"] == expected[key] for key, row in authority.items() if row["semantic_class"] == semantic), "reordered_correct": sum(reordered_by_id[key]["candidate"] == expected[key] for key, row in authority.items() if row["semantic_class"] == semantic)} for semantic in SEMANTIC_WORD}
        qualified = direct_correct >= 27 and reordered_correct >= 27 and agreement >= 32 and all(value["direct_correct"] >= 8 and value["reordered_correct"] >= 8 for value in per_class.values())
        body = {"version": VERSION, "status": "semantic_token_delivery_qualified" if qualified else "semantic_token_delivery_not_qualified", "n": len(expected), "direct_correct": direct_correct, "reordered_correct": reordered_correct, "candidate_agreement": agreement, "per_class": per_class, "candidate_token_ids": candidate_ids, "authority_opened_after_all_receipts": True, "factorial_authorized": qualified, "failure_interpretation": None if qualified else "semantic-token delivery is not sufficiently discriminative; no factorial is authorized"}
        _write_new(result_path, {**body, "qualification_id": _digest(body)})
        _write_new(terminal, {"version": VERSION, "status": "terminal", "qualified": qualified, "automatic_restarts_authorized": 0})
        print(json.dumps(body, sort_keys=True))
        del model, tokenizer
        gc.collect()
        mx.clear_cache()
    except Exception as error:
        if not terminal.exists():
            _write_new(terminal, {"version": VERSION, "status": "engineering_failure_no_retry", "error_type": type(error).__name__, "error": str(error)[:500], "automatic_restarts_authorized": 0})
        raise


if __name__ == "__main__":
    main()
