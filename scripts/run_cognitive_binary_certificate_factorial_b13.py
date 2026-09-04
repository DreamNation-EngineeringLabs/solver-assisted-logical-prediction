#!/usr/bin/env python3
"""Execute b13 with exactly one forward batch per model-call unit."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

import run_cognitive_binary_certificate_factorial_b12 as transport


VERSION = "binary-certificate-factorial-b13"
DATA = Path("data/cognitive_core/binary_certificate_factorial_b13")
RUN = Path("runs/cognitive_core/binary_certificate_factorial_b13")
BOOTSTRAP_SEED = 2026090132
SCRIPT = "scripts/run_cognitive_binary_certificate_factorial_b13.py"
root = transport.base


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _one_batch_score(*, model: Any, tokenizer: Any, rows: Sequence[Mapping[str, Any]], prompt_key: str, candidate_ids: Mapping[str, int], stage: str, arm: str) -> list[Mapping[str, Any]]:
    encoded = [root.common._chat_prompt(tokenizer, str(row[prompt_key]), transport.MODEL) for row in rows]
    if not encoded or max(len(value) for value in encoded) > 1536:
        raise RuntimeError("one-batch prompt-length gate failed")
    pad = getattr(tokenizer, "pad_token_id", None) or getattr(tokenizer, "eos_token_id", 0)
    batch = np.full((len(encoded), max(len(value) for value in encoded)), int(pad), dtype=np.int32)
    for index, sequence in enumerate(encoded):
        batch[index, : len(sequence)] = sequence
    model.eval()
    logits = model(root.common.mx.array(batch))
    lengths = [len(value) for value in encoded]
    selected = logits[root.common.mx.arange(len(encoded)), root.common.mx.array(lengths, dtype=root.common.mx.int32) - 1]
    root.common.mx.eval(selected)
    values = np.asarray(selected.astype(root.common.mx.float32).tolist(), dtype=np.float32)
    receipts: list[Mapping[str, Any]] = []
    for row, vector in zip(rows, values, strict=True):
        scores = {candidate: float(vector[token]) for candidate, token in candidate_ids.items()}
        order = sorted(scores, key=lambda candidate: (-scores[candidate], candidate))
        body = {"version": VERSION, "model_key": transport.MODEL, "stage": stage, "arm": arm, "task_id": str(row["task_id"]), "candidate": order[0], "candidate_token_scores": scores, "top_two_margin": scores[order[0]] - scores[order[1]], "raw_generation_used": False}
        receipts.append({**body, "receipt_id": root.common._digest(body)})
    del logits, selected
    root.common.mx.clear_cache()
    return receipts


def _qualification_score(*, model: Any, tokenizer: Any, rows: Sequence[Mapping[str, Any]], prompt_key: str, candidate_ids: Mapping[str, int], stage: str, arm: str) -> list[Mapping[str, Any]]:
    return _one_batch_score(model=model, tokenizer=tokenizer, rows=rows, prompt_key=prompt_key, candidate_ids=candidate_ids, stage=stage, arm=arm)


def _prospective_score(model: Any, tokenizer: Any, rows: Sequence[Mapping[str, Any]], candidate_ids: Mapping[str, int], arm: str, shard: int) -> list[Mapping[str, Any]]:
    receipts = _one_batch_score(model=model, tokenizer=tokenizer, rows=rows, prompt_key="arm_prompt", candidate_ids=candidate_ids, stage="prospective", arm=arm)
    return [{**row, "shard": shard, "receipt_id": root.common._digest({key: value for key, value in {**row, "shard": shard}.items() if key != "receipt_id"})} for row in receipts]


def _configure() -> None:
    transport.VERSION = VERSION
    transport.DATA = DATA
    transport.RUN = RUN
    transport.BOOTSTRAP_SEED = BOOTSTRAP_SEED
    transport.SCRIPT = SCRIPT
    transport._configure_base()
    root._score = _qualification_score
    transport._score_shard = _prospective_score
    root.common.BOOTSTRAP_SEED = BOOTSTRAP_SEED


def _implementation(project: Path) -> None:
    path = project / RUN / transport.MODEL / "control/implementation.json"
    if not path.exists():
        body = {"version": VERSION, "runner": {"script": SCRIPT, "sha256": _sha256(Path(__file__).resolve())}, "base_runner": {"script": "scripts/run_cognitive_binary_certificate_factorial_b12.py", "sha256": _sha256(Path(transport.__file__).resolve())}, "execution_change": "one forward batch per qualification template and 24-item arm-shard", "automatic_restarts_authorized": 0, "automatic_successors_authorized": 0}
        root.common._write_new(path, {**body, "implementation_id": root.common._digest(body)})


def main() -> None:
    parser = argparse.ArgumentParser(description="Run b13 with bounded one-forward-batch units.")
    parser.add_argument("stage", choices=("preflight", "qualify", "arm", "finalize"))
    parser.add_argument("--arm", choices=transport.ARMS)
    parser.add_argument("--shard", type=int)
    parser.add_argument("--project", type=Path, default=Path("."))
    args = parser.parse_args()
    _configure()
    project = args.project.resolve()
    _implementation(project)
    if args.stage == "preflight":
        print(json.dumps(transport._preflight(project), sort_keys=True))
    elif args.stage == "qualify":
        transport._qualify(project)
    elif args.stage == "arm":
        if args.arm is None or args.shard is None:
            raise RuntimeError("arm stage requires --arm and --shard")
        transport._run_shard(project, args.arm, args.shard)
    else:
        transport._finalize(project)


if __name__ == "__main__":
    main()
