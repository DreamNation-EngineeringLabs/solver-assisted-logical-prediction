#!/usr/bin/env python3
"""Run the one-attempt Qwen3 v10 certificate factorial after qualification.

This is a fresh successor to v8, never a v8 retry.  Its only runtime change is
to convert MLX logits through a Python list after an explicit float32 cast;
direct NumPy conversion of Qwen3's bfloat16 buffer caused v8 to terminate
before scoring its first item.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

import run_cognitive_solver_assisted_certificate_factorial_v8 as base


VERSION = "solver-assisted-certificate-factorial-v10"
DATA = Path("data/cognitive_core/solver_assisted_certificate_factorial_v10")
RUN = Path("runs/cognitive_core/solver_assisted_certificate_factorial_v10")
SCRIPT = "scripts/run_cognitive_solver_assisted_certificate_factorial_v10.py"
BOOTSTRAP_SEED = 2026090125
MODEL = "qwen3_1p7b"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _score_prompts(
    *,
    model: Any,
    tokenizer: Any,
    model_key: str,
    rows: Sequence[Mapping[str, Any]],
    prompt_key: str,
    candidate_ids: Mapping[str, int],
    stage: str,
    arm: str,
) -> list[Mapping[str, Any]]:
    encoded = [base._chat_prompt(tokenizer, str(row[prompt_key]), model_key) for row in rows]
    if not encoded or max(len(item) for item in encoded) > 1536:
        raise RuntimeError(f"{stage}/{arm} prompt length gate failed")
    pad_id = getattr(tokenizer, "pad_token_id", None) or getattr(tokenizer, "eos_token_id", 0)
    model.eval()
    receipts: list[Mapping[str, Any]] = []
    for start in range(0, len(rows), 4):
        current, sequences = rows[start : start + 4], encoded[start : start + 4]
        lengths = [len(sequence) for sequence in sequences]
        batch = np.full((len(sequences), max(lengths)), int(pad_id), dtype=np.int32)
        for index, sequence in enumerate(sequences):
            batch[index, : len(sequence)] = sequence
        logits = model(base.mx.array(batch))
        selected = logits[base.mx.arange(len(sequences)), base.mx.array(lengths, dtype=base.mx.int32) - 1]
        base.mx.eval(selected)
        values = np.asarray(selected.astype(base.mx.float32).tolist(), dtype=np.float32)
        for row, vector in zip(current, values, strict=True):
            scores = {label: float(vector[token]) for label, token in candidate_ids.items()}
            order = sorted(scores, key=lambda label: (-scores[label], label))
            body = {
                "version": VERSION,
                "model_key": model_key,
                "stage": stage,
                "arm": arm,
                "task_id": str(row["task_id"]),
                "candidate": order[0],
                "candidate_token_scores": scores,
                "top_two_margin": scores[order[0]] - scores[order[1]],
                "raw_generation_used": False,
            }
            receipts.append({**body, "receipt_id": base._digest(body)})
        print(json.dumps({"model": model_key, "stage": stage, "arm": arm, "completed": min(start + len(current), len(rows)), "total": len(rows)}), flush=True)
        del logits, selected
        base.mx.clear_cache()
    return receipts


def _configure_base() -> None:
    base.VERSION = VERSION
    base.DATA = DATA
    base.RUN = RUN
    base.BOOTSTRAP_SEED = BOOTSTRAP_SEED
    base._score_prompts = _score_prompts


def _implementation_manifest(project: Path) -> Mapping[str, Any]:
    return {
        "version": VERSION,
        "runner": {"script": SCRIPT, "sha256": _sha256(Path(__file__).resolve())},
        "base_runner": {
            "script": "scripts/run_cognitive_solver_assisted_certificate_factorial_v8.py",
            "sha256": _sha256(Path(base.__file__).resolve()),
        },
        "permitted_model": MODEL,
        "successor_reason": "v8_qwen3_qualification_engineering_failure_before_any_score_or_authority_opening",
        "sole_runtime_change": "explicit_mlx_float32_cast_followed_by_tolist_before_numpy_conversion",
        "no_prompt_or_analysis_change": True,
        "automatic_restarts_authorized": 0,
        "automatic_successors_authorized": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run exactly one v10 Qwen3 stage.")
    parser.add_argument("stage", choices=("preflight", "qualify", "prospective"))
    parser.add_argument("--model", choices=(MODEL,), required=True)
    parser.add_argument("--project", type=Path, default=Path("."))
    args = parser.parse_args()
    project = args.project.resolve()
    _configure_base()
    run = project / RUN / MODEL
    implementation = run / "control/implementation.json"
    if not implementation.exists():
        base._write_new(implementation, {**_implementation_manifest(project), "implementation_id": base._digest(_implementation_manifest(project))})
    if args.stage == "preflight":
        print(json.dumps(base._release_preflight(project, MODEL), sort_keys=True))
    elif args.stage == "qualify":
        base.qualify(project, MODEL)
    else:
        base.prospective(project, MODEL)


if __name__ == "__main__":
    main()
