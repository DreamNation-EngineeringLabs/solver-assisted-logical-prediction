#!/usr/bin/env python3
"""Run one qualified frozen-model execution of the sealed v8 factorial."""
from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import sys
from pathlib import Path
from statistics import NormalDist
from typing import Any, Mapping, Sequence

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import numpy as np


VERSION = "solver-assisted-certificate-factorial-v8"
DATA = Path("data/cognitive_core/solver_assisted_certificate_factorial_v8")
RUN = Path("runs/cognitive_core/solver_assisted_certificate_factorial_v8")
SOURCE = "scripts/run_cognitive_solver_assisted_certificate_factorial_v8.py"
ARMS = ("none", "irrelevant", "conclusion_only", "proof_prefix", "full")
NORMAL = NormalDist()
BOOTSTRAP_SEED = 2026090113
MODELS: Mapping[str, Mapping[str, Any]] = {
    "qwen2p5_3b": {
        "parameter_class": "3B",
        "repository": "mlx-community/Qwen2.5-3B-Instruct-4bit",
        "revision": "4f83f8f146fdf28b512a06562b671d7af4fab457",
        "path": "/Users/krishnachaitanya/.cache/huggingface/hub/models--mlx-community--Qwen2.5-3B-Instruct-4bit/snapshots/4f83f8f146fdf28b512a06562b671d7af4fab457",
        "enable_thinking": None,
    },
    "qwen3_1p7b": {
        "parameter_class": "1.7B",
        "repository": "Qwen/Qwen3-1.7B-MLX-4bit",
        "revision": "21457c6f51ed54a7c16e988c0844db973815c137",
        "path": "/Users/krishnachaitanya/.cache/huggingface/hub/models--Qwen--Qwen3-1.7B-MLX-4bit/snapshots/21457c6f51ed54a7c16e988c0844db973815c137",
        "enable_thinking": False,
    },
}
SYSTEM = "Solve the stated logical query using only the supplied text. Return exactly one of A, B, or C."
mx: Any | None = None


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
        raise RuntimeError(f"expected JSON object at {path}")
    return value


def _rows(path: Path) -> list[Mapping[str, Any]]:
    values = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if not all(isinstance(value, Mapping) for value in values):
        raise RuntimeError(f"expected JSON objects in {path}")
    return values


def _write_new(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(payload)
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


def _model_manifest(model_key: str) -> Mapping[str, Any]:
    spec = MODELS[model_key]
    model_path = Path(str(spec["path"]))
    config = model_path / "config.json"
    weights = model_path / "model.safetensors"
    if not config.is_file() or not weights.is_file():
        raise RuntimeError(f"frozen local model is unavailable for {model_key}")
    return {
        "model_key": model_key,
        "parameter_class": spec["parameter_class"],
        "repository": spec["repository"],
        "revision": spec["revision"],
        "path": str(model_path),
        "config": {"name": "config.json", "bytes": config.stat().st_size, "sha256": _sha256(config)},
        "weights": {"name": "model.safetensors", "bytes": weights.stat().st_size, "sha256": _sha256(weights)},
        "network_loading": False,
    }


def _runtime_manifest() -> Mapping[str, Any]:
    packages = {}
    for name in ("mlx", "mlx-lm", "numpy", "transformers", "tokenizers"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = "not-installed"
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "packages": packages,
        "offline": {"HF_HUB_OFFLINE": os.environ["HF_HUB_OFFLINE"], "TRANSFORMERS_OFFLINE": os.environ["TRANSFORMERS_OFFLINE"]},
    }


def _chat_prompt(tokenizer: Any, prompt: str, model_key: str) -> tuple[int, ...]:
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]
    if MODELS[model_key]["enable_thinking"] is False:
        rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    else:
        rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    tokens = tokenizer.encode(rendered, add_special_tokens=tokenizer.bos_token is None or not rendered.startswith(tokenizer.bos_token))
    return tuple(int(token) for token in tokens)


def _candidate_token_ids(tokenizer: Any) -> Mapping[str, int]:
    result: dict[str, int] = {}
    for label in ("A", "B", "C"):
        encoded = tokenizer.encode(label, add_special_tokens=False)
        if len(encoded) != 1:
            raise RuntimeError(f"{label} is not a single candidate token")
        result[label] = int(encoded[0])
    if len(set(result.values())) != 3:
        raise RuntimeError("candidate token ids are not distinct")
    return result


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
    encoded = [_chat_prompt(tokenizer, str(row[prompt_key]), model_key) for row in rows]
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
        logits = model(mx.array(batch))
        selected = logits[mx.arange(len(sequences)), mx.array(lengths, dtype=mx.int32) - 1]
        mx.eval(selected)
        values = np.asarray(selected, dtype=np.float32)
        for row, vector in zip(current, values, strict=True):
            scores = {label: float(vector[token]) for label, token in candidate_ids.items()}
            order = sorted(scores, key=lambda label: (-scores[label], label))
            body = {"version": VERSION, "model_key": model_key, "stage": stage, "arm": arm, "task_id": str(row["task_id"]), "candidate": order[0], "candidate_token_scores": scores, "top_two_margin": scores[order[0]] - scores[order[1]], "raw_generation_used": False}
            receipts.append({**body, "receipt_id": _digest(body)})
        print(json.dumps({"model": model_key, "stage": stage, "arm": arm, "completed": min(start + len(current), len(rows)), "total": len(rows)}), flush=True)
        del logits, selected
        mx.clear_cache()
    return receipts


def _exact_mcnemar(left_only: int, right_only: int) -> float:
    discordant = left_only + right_only
    if discordant == 0:
        return 1.0
    return min(1.0, 2.0 * sum(math.comb(discordant, index) for index in range(min(left_only, right_only) + 1)) / (2**discordant))


def _bca_paired_difference(values: Sequence[int], *, seed: int, replicates: int = 100_000) -> tuple[float, float]:
    observed = np.asarray(values, dtype=np.float64)
    if observed.ndim != 1 or len(observed) < 2:
        raise RuntimeError("BCa interval requires at least two paired values")
    estimate = float(observed.mean())
    rng = np.random.default_rng(seed)
    distribution = np.empty(replicates, dtype=np.float64)
    batch_size = 1000
    for start in range(0, replicates, batch_size):
        count = min(batch_size, replicates - start)
        indexes = rng.integers(0, len(observed), size=(count, len(observed)), endpoint=False)
        distribution[start : start + count] = observed[indexes].mean(axis=1)
    proportion_less = (float(np.count_nonzero(distribution < estimate)) + 0.5 * float(np.count_nonzero(distribution == estimate))) / replicates
    proportion_less = min(max(proportion_less, 1.0 / (2 * replicates)), 1.0 - 1.0 / (2 * replicates))
    bias = NORMAL.inv_cdf(proportion_less)
    total = float(observed.sum())
    jackknife = (total - observed) / (len(observed) - 1)
    centered = jackknife.mean() - jackknife
    denominator = 6.0 * float(np.sum(centered * centered) ** 1.5)
    acceleration = 0.0 if denominator == 0.0 else float(np.sum(centered**3) / denominator)

    def adjusted(alpha: float) -> float:
        z = NORMAL.inv_cdf(alpha)
        numerator = bias + z
        value = NORMAL.cdf(bias + numerator / (1.0 - acceleration * numerator))
        return min(max(value, 0.0), 1.0)

    lower, upper = adjusted(0.025), adjusted(0.975)
    return float(np.quantile(distribution, lower)), float(np.quantile(distribution, upper))


def _comparison(left: Sequence[Mapping[str, Any]], right: Sequence[Mapping[str, Any]], authority: Mapping[str, str], *, seed_suffix: str) -> Mapping[str, Any]:
    left_by_id = {str(row["task_id"]): row for row in left}
    right_by_id = {str(row["task_id"]): row for row in right}
    if set(left_by_id) != set(authority) or set(right_by_id) != set(authority):
        raise RuntimeError("paired receipt identities do not match the sealed authority")
    values: list[int] = []
    both_correct = left_only = right_only = neither = 0
    for task_id in sorted(authority):
        left_correct = left_by_id[task_id]["candidate"] == authority[task_id]
        right_correct = right_by_id[task_id]["candidate"] == authority[task_id]
        values.append(int(left_correct) - int(right_correct))
        if left_correct and right_correct:
            both_correct += 1
        elif left_correct:
            left_only += 1
        elif right_correct:
            right_only += 1
        else:
            neither += 1
    interval = _bca_paired_difference(values, seed=int.from_bytes(hashlib.sha256(f"{BOOTSTRAP_SEED}:{seed_suffix}".encode("utf-8")).digest()[:8], "big"))
    n = len(values)
    return {
        "n": n,
        "left_correct": both_correct + left_only,
        "right_correct": both_correct + right_only,
        "paired_risk_difference": sum(values) / n,
        "paired_table": {"both_correct": both_correct, "left_only_correct": left_only, "right_only_correct": right_only, "neither_correct": neither},
        "exact_two_sided_mcnemar_p": _exact_mcnemar(left_only, right_only),
        "paired_BCa_bootstrap_95": list(interval),
        "bootstrap": {"method": "nonparametric_paired_BCa", "replicates": 100_000, "seed_derivation": seed_suffix},
    }


def _holm(comparisons: Mapping[str, Mapping[str, Any]]) -> Mapping[str, float]:
    ordered = sorted(((name, float(result["exact_two_sided_mcnemar_p"])) for name, result in comparisons.items()), key=lambda item: item[1])
    adjusted: dict[str, float] = {}
    running = 0.0
    total = len(ordered)
    for rank, (name, p_value) in enumerate(ordered):
        running = max(running, min(1.0, (total - rank) * p_value))
        adjusted[name] = running
    return adjusted


def _release_preflight(project: Path, model_key: str) -> Mapping[str, Any]:
    data = project / DATA
    seal, protocol = _read(data / "public/seal.json"), _read(data / "public/protocol.json")
    if protocol.get("version") != VERSION or seal.get("protocol_id") != protocol.get("protocol_id"):
        raise RuntimeError("sealed v8 protocol binding is invalid")
    if protocol.get("execution_policy", {}).get("automatic_restarts_authorized") != 0:
        raise RuntimeError("automatic restarts are prohibited")
    output = project / RUN / model_key / "control/preflight.json"
    if output.exists():
        return _read(output)
    public = _rows(project / str(seal["panels"]["development"]["public_path"]))
    required = set(ARMS)
    if len(public) != 72 or any(set(row["prompts"]) != required for row in public):
        raise RuntimeError("development factorial construction is invalid")
    maximum_chars = max(len(str(prompt)) for row in public for prompt in row["prompts"].values())
    body = {"version": VERSION, "model_key": model_key, "status": "nonmodel_preflight_passed", "development_items": len(public), "arms": list(ARMS), "maximum_prompt_characters": maximum_chars, "authority_opened": False, "model_calls": 0}
    _write_new(output, {**body, "preflight_id": _digest(body)})
    return _read(output)


def _load_frozen(model_key: str) -> tuple[Any, Any, Mapping[str, Any], Mapping[str, int]]:
    global mx
    import mlx.core as mlx_core
    from mlx_lm import load as mlx_load

    mx = mlx_core
    manifest = _model_manifest(model_key)
    model, tokenizer = mlx_load(str(manifest["path"]), tokenizer_config={"trust_remote_code": False})
    candidate_ids = _candidate_token_ids(tokenizer)
    return model, tokenizer, manifest, candidate_ids


def qualify(project: Path, model_key: str) -> None:
    run = project / RUN / model_key
    terminal = run / "control/interface-terminal.json"
    result_path = run / "results/interface-qualification.json"
    if terminal.exists() or result_path.exists():
        raise RuntimeError("interface qualification attempt already consumed")
    _release_preflight(project, model_key)
    data = project / DATA
    seal = _read(data / "public/seal.json")
    rows = _rows(project / str(seal["panels"]["interface"]["public_path"]))
    authority_path = project / str(seal["panels"]["interface"]["authority_path"])
    try:
        model, tokenizer, model_manifest, candidate_ids = _load_frozen(model_key)
        freeze = {"version": VERSION, "model": model_manifest, "runtime": _runtime_manifest(), "candidate_token_ids": candidate_ids, "system_instruction": SYSTEM, "interface_public_sha256": seal["panels"]["interface"]["public_sha256"], "interface_authority_sha256": seal["panels"]["interface"]["authority_sha256"], "authority_opened_before_receipts": False}
        _write_new(run / "control/interface-code-freeze.json", {**freeze, "freeze_id": _digest(freeze)})
        normal = _score_prompts(model=model, tokenizer=tokenizer, model_key=model_key, rows=rows, prompt_key="normal_prompt", candidate_ids=candidate_ids, stage="interface", arm="normal")
        alternate = _score_prompts(model=model, tokenizer=tokenizer, model_key=model_key, rows=rows, prompt_key="alternate_prompt", candidate_ids=candidate_ids, stage="interface", arm="alternate_mapping")
        _write_rows_new(run / "receipts/interface-normal.jsonl", normal)
        _write_rows_new(run / "receipts/interface-alternate_mapping.jsonl", alternate)
        authority = {str(row["task_id"]): row for row in _rows(authority_path)}
        normal_by_id = {str(row["task_id"]): row for row in normal}
        alternate_by_id = {str(row["task_id"]): row for row in alternate}
        if set(normal_by_id) != set(authority) or set(alternate_by_id) != set(authority):
            raise RuntimeError("interface receipt identities are incomplete")
        normal_correct = sum(normal_by_id[key]["candidate"] == authority[key]["normal_answer"] for key in authority)
        alternate_correct = sum(alternate_by_id[key]["candidate"] == authority[key]["alternate_answer"] for key in authority)
        agreement = sum((next(semantic for semantic, label in {"entailed": "A", "contradicted": "B", "unknown": "C"}.items() if normal_by_id[key]["candidate"] == label) == next(semantic for semantic, label in {"entailed": "C", "contradicted": "A", "unknown": "B"}.items() if alternate_by_id[key]["candidate"] == label)) for key in authority)
        per_class: dict[str, Mapping[str, int]] = {}
        for semantic in ("entailed", "contradicted", "unknown"):
            ids = [key for key, row in authority.items() if row["semantic_class"] == semantic]
            per_class[semantic] = {"n": len(ids), "normal_correct": sum(normal_by_id[key]["candidate"] == authority[key]["normal_answer"] for key in ids), "alternate_correct": sum(alternate_by_id[key]["candidate"] == authority[key]["alternate_answer"] for key in ids)}
        qualified = normal_correct >= 27 and alternate_correct >= 27 and agreement >= 32 and all(values["normal_correct"] >= 8 and values["alternate_correct"] >= 8 for values in per_class.values())
        body = {"version": VERSION, "model_key": model_key, "status": "semantic_delivery_qualified" if qualified else "semantic_delivery_not_qualified", "n": len(authority), "normal_correct": normal_correct, "alternate_correct": alternate_correct, "semantic_agreement": agreement, "per_class": per_class, "candidate_token_ids": candidate_ids, "authority_opened_after_all_interface_receipts": True, "prospective_authorized": qualified, "failure_interpretation": "delivery failure, not a certificate-treatment null" if not qualified else None}
        _write_new(result_path, {**body, "qualification_id": _digest(body)})
        _write_new(terminal, {"version": VERSION, "model_key": model_key, "status": "interface_qualification_terminal", "qualified": qualified, "automatic_restarts_authorized": 0})
        del model, tokenizer
        gc.collect()
        mx.clear_cache()
        print(json.dumps(body, sort_keys=True))
    except Exception as error:
        if not terminal.exists():
            _write_new(terminal, {"version": VERSION, "model_key": model_key, "status": "interface_qualification_engineering_failure_no_retry", "error_type": type(error).__name__, "error": str(error)[:500], "automatic_restarts_authorized": 0})
        raise


def prospective(project: Path, model_key: str) -> None:
    run = project / RUN / model_key
    terminal = run / "control/prospective-terminal.json"
    result_path = run / "results/prospective-factorial.json"
    if terminal.exists() or result_path.exists():
        raise RuntimeError("prospective attempt already consumed")
    preflight = _release_preflight(project, model_key)
    qualification = _read(run / "results/interface-qualification.json")
    if qualification.get("status") != "semantic_delivery_qualified" or qualification.get("prospective_authorized") is not True:
        raise RuntimeError("prospective execution requires semantic delivery qualification")
    data = project / DATA
    seal = _read(data / "public/seal.json")
    rows = _rows(project / str(seal["panels"]["prospective"]["public_path"]))
    if len(rows) != 192 or any(set(row["prompts"]) != set(ARMS) for row in rows):
        raise RuntimeError("prospective panel is invalid")
    try:
        model, tokenizer, model_manifest, candidate_ids = _load_frozen(model_key)
        if dict(candidate_ids) != dict(qualification["candidate_token_ids"]):
            raise RuntimeError("candidate token identity changed after interface qualification")
        freeze = {"version": VERSION, "model": model_manifest, "runtime": _runtime_manifest(), "candidate_token_ids": candidate_ids, "system_instruction": SYSTEM, "preflight_id": preflight["preflight_id"], "interface_qualification_id": qualification["qualification_id"], "prospective_public_sha256": seal["panels"]["prospective"]["public_sha256"], "prospective_authority_sha256": seal["panels"]["prospective"]["authority_sha256"], "arms": list(ARMS), "n": len(rows), "authority_opened_before_receipts": False}
        _write_new(run / "control/prospective-code-freeze.json", {**freeze, "freeze_id": _digest(freeze)})
        receipts = {arm: _score_prompts(model=model, tokenizer=tokenizer, model_key=model_key, rows=rows, prompt_key="prompts", candidate_ids=candidate_ids, stage="prospective", arm=arm) for arm in ()}
        receipts = {}
        for arm in ARMS:
            arm_rows = [{**row, "prompts": row["prompts"][arm]} for row in rows]
            receipts[arm] = _score_prompts(model=model, tokenizer=tokenizer, model_key=model_key, rows=arm_rows, prompt_key="prompts", candidate_ids=candidate_ids, stage="prospective", arm=arm)
            _write_rows_new(run / f"receipts/prospective-{arm}.jsonl", receipts[arm])
        authority = {str(row["task_id"]): str(row["answer"]) for row in _rows(project / str(seal["panels"]["prospective"]["authority_path"]))}
        if len(authority) != 192:
            raise RuntimeError("sealed prospective authority has unexpected size")
        comparisons = {"proof_prefix_minus_conclusion_only": _comparison(receipts["proof_prefix"], receipts["conclusion_only"], authority, seed_suffix=f"{model_key}:prefix-conclusion"), "proof_prefix_minus_irrelevant": _comparison(receipts["proof_prefix"], receipts["irrelevant"], authority, seed_suffix=f"{model_key}:prefix-irrelevant"), "full_minus_conclusion_only": _comparison(receipts["full"], receipts["conclusion_only"], authority, seed_suffix=f"{model_key}:full-conclusion")}
        secondary = {name: comparisons[name] for name in ("proof_prefix_minus_irrelevant", "full_minus_conclusion_only")}
        adjusted = _holm(secondary)
        correct = {arm: sum(row["candidate"] == authority[str(row["task_id"])] for row in values) for arm, values in receipts.items()}
        primary = comparisons["proof_prefix_minus_conclusion_only"]
        supports_prefix = primary["exact_two_sided_mcnemar_p"] < 0.05 and primary["paired_BCa_bootstrap_95"][0] > 0 and comparisons["proof_prefix_minus_irrelevant"]["paired_BCa_bootstrap_95"][0] > 0
        body = {"version": VERSION, "model_key": model_key, "status": "terminal_scored_no_audit_or_restart", "n": len(authority), "correct": correct, "accuracy": {arm: correct[arm] / len(authority) for arm in ARMS}, "primary_comparison": comparisons["proof_prefix_minus_conclusion_only"], "secondary_comparisons": {name: {**result, "holm_adjusted_p": adjusted[name]} for name, result in secondary.items()}, "interpretation": "limited_system_level_proof_prefix_support" if supports_prefix else "external_answer_provision_or_no_prefix_support_not_resolved", "claim_boundary": "This result is about a frozen solver-assisted system in one qualified model/task envelope. It does not identify the model's internal reasoning process or a universal repair mechanism.", "authority_opened_after_all_prospective_receipts": True, "automatic_restarts_authorized": 0}
        _write_new(result_path, {**body, "result_id": _digest(body)})
        _write_new(terminal, {"version": VERSION, "model_key": model_key, "status": "prospective_terminal", "automatic_restarts_authorized": 0})
        del model, tokenizer
        gc.collect()
        mx.clear_cache()
        print(json.dumps(body, sort_keys=True))
    except Exception as error:
        if not terminal.exists():
            _write_new(terminal, {"version": VERSION, "model_key": model_key, "status": "prospective_engineering_failure_no_retry", "error_type": type(error).__name__, "error": str(error)[:500], "automatic_restarts_authorized": 0})
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one sealed v8 model stage.")
    parser.add_argument("stage", choices=("preflight", "qualify", "prospective"))
    parser.add_argument("--model", choices=tuple(MODELS), required=True)
    parser.add_argument("--project", type=Path, default=Path("."))
    args = parser.parse_args()
    project = args.project.resolve()
    if args.stage == "preflight":
        print(json.dumps(_release_preflight(project, args.model), sort_keys=True))
    elif args.stage == "qualify":
        qualify(project, args.model)
    else:
        prospective(project, args.model)


if __name__ == "__main__":
    main()
