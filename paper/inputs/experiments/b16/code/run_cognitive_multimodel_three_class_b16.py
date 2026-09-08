#!/usr/bin/env python3
"""b16 stage 2: score the sealed three-class panel across all candidate models.

Models are streamed strictly one at a time -- download a pinned revision, record
the weight manifest, score every arm, persist receipts, mark the model complete,
then delete the weights. Peak disk is one model.

Resumable by completion marker. A model with a marker is skipped and never
re-run; a model interrupted without one leaves partial receipts that are
discarded and rewritten on the next pass. b11, b12 and b13 were each lost to
execution interrupts, so this is not a theoretical concern.

The answer authority is never read here. This script only records what each
model chose.

Prompts are scored one at a time rather than batched: a padding or mask error
would corrupt a one-shot sealed run silently, and the sweep is not compute-bound.
Candidate logits are cast to float32 and converted through a Python list, which
is the v10 fix for the MLX bfloat16 conversion fault that ended v8.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import time
import traceback
from pathlib import Path
from typing import Any, Mapping, Sequence

from cc_instruments import modelcache

VERSION = "multimodel-three-class-b16"
DATA = Path("data/cognitive_core/multimodel_three_class_b16")
RUN = Path("runs/cognitive_core/multimodel_three_class_b16")
ARMS = ("none", "irrelevant", "conclusion_only", "proof_prefix", "full")
CANDIDATES = ("Yes", "No", "Unknown")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_panel(project: Path) -> list[Mapping[str, Any]]:
    seal = json.loads((project / DATA / "public/seal.json").read_text(encoding="utf-8"))
    panel = project / seal["public_path"]
    if _sha256(panel) != seal["public_sha256"]:
        raise RuntimeError("sealed panel hash mismatch; refusing to score a modified panel")
    rows = [json.loads(l) for l in panel.read_text(encoding="utf-8").splitlines() if l.strip()]
    if len(rows) != seal["n"]:
        raise RuntimeError(f"panel has {len(rows)} rows, seal declares {seal['n']}")
    return rows


def _candidate_ids(tokenizer: Any) -> dict[str, int]:
    ids: dict[str, int] = {}
    for c in CANDIDATES:
        enc = tokenizer.encode(c, add_special_tokens=False)
        if len(enc) != 1:
            raise RuntimeError(f"{c!r} is not a single token for this tokenizer")
        ids[c] = int(enc[0])
    if len(set(ids.values())) != len(ids):
        raise RuntimeError("candidate tokens are not distinct")
    return ids


def _score_arm(model: Any, tokenizer: Any, rows: Sequence[Mapping[str, Any]], arm: str,
               ids: Mapping[str, int], model_key: str, mx: Any) -> list[Mapping[str, Any]]:
    out: list[Mapping[str, Any]] = []
    for row in rows:
        tokens = tokenizer.encode(row["prompts"][arm])
        logits = model(mx.array([tokens]))[0, -1]
        scores = mx.array(logits).astype(mx.float32).tolist()
        picked = {c: float(scores[i]) for c, i in ids.items()}
        ordered = sorted(picked.values(), reverse=True)
        body = {
            "version": VERSION, "stage": "prospective", "model_key": model_key,
            "arm": arm, "task_id": row["task_id"],
            "candidate": max(picked, key=lambda k: picked[k]),
            "candidate_token_scores": picked,
            "top_two_margin": ordered[0] - ordered[1],
            "raw_generation_used": False,
        }
        out.append({**body, "receipt_id": _digest(body)})
    return out


def _run_model(entry: Mapping[str, Any], rows: Sequence[Mapping[str, Any]], run_dir: Path) -> Mapping[str, Any]:
    from mlx_lm import load
    import mlx.core as mx

    key, repo, rev = entry["key"], entry["repo"], entry["revision"]
    t0 = time.time()
    snapshot = modelcache.download(repo, rev)
    weights = modelcache.weight_manifest(snapshot)              # manifest BEFORE any delete
    modelcache.write_json(run_dir / "control/model-manifest.json", {
        "version": VERSION, "key": key, "repo": repo, "revision": rev,
        "family": entry["family"], "params_b": entry["params_b"], "weights": weights})

    model, tokenizer = load(str(snapshot), tokenizer_config={"trust_remote_code": False})
    ids = _candidate_ids(tokenizer)
    modelcache.write_json(run_dir / "control/candidate-tokens.json",
                          {"version": VERSION, "key": key, "candidate_token_ids": ids})

    timings: dict[str, float] = {}
    for arm in ARMS:
        t1 = time.time()
        receipts = _score_arm(model, tokenizer, rows, arm, ids, key, mx)
        path = run_dir / f"receipts/prospective-{arm}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in receipts),
                        encoding="utf-8")
        timings[arm] = round(time.time() - t1, 1)
        print(f"    {key:16s} {arm:16s} {len(receipts):3d} receipts  {timings[arm]:6.1f}s", flush=True)

    del model, tokenizer
    gc.collect()
    try:
        mx.clear_cache()
    except AttributeError:
        pass
    return {"weights_sha256": weights["aggregate_sha256"],
            "weights_bytes": weights["total_bytes"],
            "arm_seconds": timings, "total_seconds": round(time.time() - t0, 1),
            "candidate_token_ids": ids}


def main() -> None:
    ap = argparse.ArgumentParser(description="Run the b16 three-class sweep across all models.")
    ap.add_argument("--project", type=Path, default=Path("."))
    ap.add_argument("--registry", type=Path, default=None)
    ap.add_argument("--only", type=str, default=None, help="comma-separated model keys")
    ap.add_argument("--keep-weights", action="store_true")
    args = ap.parse_args()

    project = args.project.resolve()
    registry = modelcache.load_registry(args.registry or project / "models.toml")
    rows = _load_panel(project)
    wanted = set(args.only.split(",")) if args.only else None
    print(f"b16 sweep: {len(rows)} items x {len(ARMS)} arms", flush=True)

    for entry in registry["model"]:
        key = entry["key"]
        if wanted and key not in wanted:
            continue
        run_dir = project / RUN / key
        marker = run_dir / "control/complete.json"
        if marker.exists():
            print(f"  {key:16s} complete, skipping", flush=True)
            continue
        if not entry.get("revision"):
            print(f"  {key:16s} SKIP - revision not pinned", flush=True)
            continue
        print(f"  {key:16s} starting ({entry['params_b']}B)", flush=True)
        try:
            summary = _run_model(entry, rows, run_dir)
        except Exception as exc:
            modelcache.write_json(run_dir / "control/failed.json", {
                "version": VERSION, "key": key, "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc()[-3000:]})
            print(f"  {key:16s} FAILED {type(exc).__name__}: {exc}", flush=True)
        else:
            body = {"version": VERSION, "key": key, "repo": entry["repo"],
                    "revision": entry["revision"], "arms": list(ARMS), "n": len(rows),
                    **summary}
            modelcache.write_json(marker, {**body, "completion_id": _digest(body)})
            print(f"  {key:16s} COMPLETE in {summary['total_seconds']:.0f}s", flush=True)
        finally:
            if not args.keep_weights:
                freed = modelcache.delete(entry["repo"], entry["revision"])
                print(f"  {key:16s} freed {freed.get('freed_bytes', 0) / 1e9:.1f} GB", flush=True)
    print("sweep finished", flush=True)


if __name__ == "__main__":
    main()
