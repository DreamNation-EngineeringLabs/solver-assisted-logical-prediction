#!/usr/bin/env python3
"""b19 — the b16 sweep on CUDA, so the table can grow past what MLX can hold.

Why a second backend at all. Experiment 3 ran on Apple Silicon via mlx-lm, which
caps the sweep at roughly 8B. Extending it upward needs a rented GPU, and that
means a different inference stack.

Why that is not free. Across b16's 9,600 responses, 298 (3.1%) have an argmax
margin under 0.1 logits and the 1st percentile is 0.000. bf16 kernels differ
between Metal and CUDA by more than that, so a table mixing MLX rows with CUDA
rows is not measuring one thing. This runner therefore exists to re-score the
EXISTING ten models first: `compare_b16_backends.py` reports receipt-level
agreement, and only once that is known does adding larger models mean anything.

Scoring semantics are copied from the frozen b16 runner deliberately -- same
prompt bytes, same single-token candidate check, same argmax, same receipt
fields -- so the only difference between the two runs is the backend.
"""
from __future__ import annotations

import argparse, gc, hashlib, json, time
from pathlib import Path
from typing import Any, Mapping, Sequence

from cc_instruments import modelcache

VERSION = "multimodel-three-class-b19-cuda"
DATA = Path("data/cognitive_core/multimodel_three_class_b16")   # the SAME sealed panel
RUN = Path("runs/cognitive_core/multimodel_three_class_b19_cuda")
ARMS = ("none", "irrelevant", "conclusion_only", "proof_prefix", "full")
CANDIDATES = ("Yes", "No", "Unknown")


def _canonical(v: Any) -> bytes:
    return json.dumps(v, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(v: Any) -> str:
    return hashlib.sha256(_canonical(v)).hexdigest()


def _rows(p: Path):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


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


def _score_arm(model, tokenizer, rows: Sequence[Mapping[str, Any]], arm: str,
               ids: Mapping[str, int], model_key: str, torch) -> list[Mapping[str, Any]]:
    out: list[Mapping[str, Any]] = []
    dev = model.device
    with torch.inference_mode():
        for row in rows:
            tokens = tokenizer.encode(row["prompts"][arm])
            logits = model(torch.tensor([tokens], device=dev)).logits[0, -1]
            scores = logits.float().tolist()
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


def _run_model(entry: Mapping[str, Any], rows, run_dir: Path) -> Mapping[str, Any]:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    key, repo, rev = entry["key"], entry["repo"], entry["revision"]
    t0 = time.time()
    snapshot = modelcache.download(repo, rev)
    weights = modelcache.weight_manifest(snapshot)              # manifest BEFORE any delete
    modelcache.write_json(run_dir / "control/model-manifest.json", {
        "version": VERSION, "key": key, "repo": repo, "revision": rev,
        "family": entry["family"], "params_b": entry["params_b"], "weights": weights,
        "backend": "transformers+cuda", "torch": torch.__version__,
        "gpu": torch.cuda.get_device_name(0),
        "gpu_memory_total_gib": round(
            torch.cuda.get_device_properties(0).total_memory / 2**30, 2)})

    tokenizer = AutoTokenizer.from_pretrained(str(snapshot), trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(
        str(snapshot), dtype=torch.bfloat16, device_map="cuda", trust_remote_code=False)
    model.eval()

    # Prove the weights are on the GPU rather than assuming it. A silent CPU
    # fallback would still produce receipts -- slowly, and in a different
    # numerical regime -- which is exactly the kind of thing that turns into an
    # unexplainable row in the results table.
    devices = {p.device.type for p in model.parameters()}
    if devices != {"cuda"}:
        raise RuntimeError(f"model parameters are not all on CUDA: {devices}")
    if next(model.parameters()).dtype is not torch.bfloat16:
        raise RuntimeError(f"expected bfloat16, got {next(model.parameters()).dtype}")
    resident = torch.cuda.memory_allocated() / 2**30
    print(f"    {key:16s} on {torch.cuda.get_device_name(0)}, "
          f"{resident:.2f} GiB resident, dtype bfloat16", flush=True)
    ids = _candidate_ids(tokenizer)
    modelcache.write_json(run_dir / "control/candidate-tokens.json",
                          {"version": VERSION, "key": key, "candidate_token_ids": ids})

    timings: dict[str, float] = {}
    for arm in ARMS:
        t1 = time.time()
        receipts = _score_arm(model, tokenizer, rows, arm, ids, key, torch)
        path = run_dir / f"receipts/prospective-{arm}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in receipts),
                        encoding="utf-8")
        timings[arm] = round(time.time() - t1, 1)
        print(f"    {key:16s} {arm:16s} {len(receipts):3d} receipts  {timings[arm]:6.1f}s", flush=True)

    del model, tokenizer
    gc.collect()
    torch.cuda.empty_cache()
    return {"weights_sha256": weights["aggregate_sha256"],
            "weights_bytes": weights["total_bytes"],
            "arm_seconds": timings, "total_seconds": round(time.time() - t0, 1),
            "candidate_token_ids": ids}


def main() -> None:
    ap = argparse.ArgumentParser(description="Score the sealed b16 panel on CUDA.")
    ap.add_argument("--project", type=Path, default=Path("."))
    ap.add_argument("--registry", type=Path, default=None)
    ap.add_argument("--table", default="model", help="registry table to read")
    ap.add_argument("--key", action="append", help="model key; repeatable, default all")
    ap.add_argument("--keep-weights", action="store_true",
                    help="do not delete the snapshot after scoring")
    a = ap.parse_args()
    project = a.project.resolve()

    rows = _rows(project / DATA / "public/panel.jsonl")
    seal = json.loads((project / DATA / "public/seal.json").read_text())
    print(f"panel {len(rows)} items, seal {seal.get('seal_id', seal.get('public_sha256'))[:16]}")

    registry = modelcache.load_registry(a.registry or project / "models.toml")[a.table]
    wanted = [e for e in registry if not a.key or e["key"] in a.key]
    if not wanted:
        raise SystemExit(f"no models matched {a.key} in table [[{a.table}]]")

    for entry in wanted:
        run_dir = project / RUN / entry["key"]
        if (run_dir / "control/complete.json").exists():
            print(f"  {entry['key']}: already complete, skipping")
            continue
        print(f"  {entry['key']} ({entry['params_b']}B) ...", flush=True)
        try:
            summary = _run_model(entry, rows, run_dir)
        except Exception as exc:
            # A model that will not load is a result about weight provenance, not
            # a reason to abandon the sweep: mlx-community mirrors are MLX
            # conversions and some do not round-trip into transformers. Record
            # it and carry on, so an unattended run finishes.
            modelcache.write_json(run_dir / "control/failed.json",
                                  {"version": VERSION, "key": entry["key"],
                                   "repo": entry["repo"], "revision": entry["revision"],
                                   "error_type": type(exc).__name__, "error": str(exc)[:2000]})
            print(f"    FAILED to load: {type(exc).__name__}: {str(exc)[:160]}", flush=True)
            if not a.keep_weights:
                try: modelcache.delete(entry["repo"], entry["revision"])
                except Exception: pass
            continue
        modelcache.write_json(run_dir / "control/complete.json",
                              {"version": VERSION, "key": entry["key"], "arms": list(ARMS),
                               "n": len(rows), **summary})
        if not a.keep_weights:
            modelcache.delete(entry["repo"], entry["revision"])
        print(f"    done in {summary['total_seconds']:.0f}s", flush=True)


if __name__ == "__main__":
    main()
