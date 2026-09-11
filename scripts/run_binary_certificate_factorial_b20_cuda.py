#!/usr/bin/env python3
"""b20 - the b15 ten-arm decomposition on CUDA, to take the corruption result past 4.3B.

Why this experiment exists. The paper's one invariant finding is that no
checkpoint resists a corrupted apparatus: given a certificate whose fabricated
final rule establishes the query's negation, all three answer incorrectly on
189, 186 and 192 of 192. Every checkpoint behind that number is <= 4.3B, so the
obvious objection is that it is a small-model artefact that scale removes.

What the existing data says about that objection. It points the other way.
Gemma-3-4B is the most capable of the three on every measure available -- 63.5%
against 41.1% balanced accuracy unaided, 22/96 against 0/96 on this panel -- and
it is the one that scored 192/192 wrong. Competence rose; verification did not
appear. Three checkpoints under 4.3B cannot settle what happens at 70B, which is
the whole point of running this.

Why the whole ten arms rather than just `misleading`. The corruption contrast is
an absolute count and needs no denominator, so it survives any competence level.
The validity share does not: it divides by (truncate_1 - irrelevant), and a model
with high unaided competence drives that denominator toward zero and the share
toward noise. Scoring every arm lets that be observed rather than assumed, and
whether the instrument still measures anything at this scale is itself a result.

Scoring semantics are copied from the frozen b15 and b19 runners deliberately --
same prompt bytes, same single-token candidate check, same argmax, same receipt
fields -- so the only differences from b15 are the backend and the checkpoint.
The answer authority is never read.
"""
from __future__ import annotations

import argparse, gc, hashlib, json, time
from pathlib import Path
from typing import Any, Mapping, Sequence

from cc_instruments import modelcache

VERSION = "binary-certificate-factorial-b20-cuda"
DATA = Path("data/cognitive_core/binary_certificate_factorial_b15")   # the SAME sealed panel
RUN = Path("runs/cognitive_core/binary_certificate_factorial_b20_cuda")
ARMS = ("none", "irrelevant", "same_entity_irrelevant", "truncate_3", "truncate_2",
        "truncate_1", "broken_chain", "misleading", "shuffled", "full")
CANDIDATES = ("Yes", "No")


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
    # A 70B is sharded across GPUs, so model.device does not exist. Inputs go to
    # wherever the embedding table lives and accelerate moves them onward.
    dev = model.get_input_embeddings().weight.device
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
    gpus = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
    modelcache.write_json(run_dir / "control/model-manifest.json", {
        "version": VERSION, "key": key, "repo": repo, "revision": rev,
        "family": entry["family"], "params_b": entry["params_b"], "weights": weights,
        "backend": "transformers+cuda", "torch": torch.__version__,
        "gpu": gpus[0] if gpus else None, "gpu_count": len(gpus), "gpus": gpus,
        "gpu_memory_total_gib": round(sum(
            torch.cuda.get_device_properties(i).total_memory
            for i in range(torch.cuda.device_count())) / 2**30, 2)})

    tokenizer = AutoTokenizer.from_pretrained(str(snapshot), trust_remote_code=False)
    # device_map="auto" rather than "cuda": 70B in bf16 does not fit one card.
    model = AutoModelForCausalLM.from_pretrained(
        str(snapshot), dtype=torch.bfloat16, device_map="auto", trust_remote_code=False)
    model.eval()

    # Prove the weights are on GPUs rather than assuming it. A silent CPU or
    # disk offload would still produce receipts -- slowly, and in a different
    # numerical regime -- which is exactly the kind of thing that turns into an
    # unexplainable row in the results table.
    devices = {p.device.type for p in model.parameters()}
    if devices != {"cuda"}:
        raise RuntimeError(f"model parameters are not all on CUDA: {sorted(devices)}")
    if next(model.parameters()).dtype is not torch.bfloat16:
        raise RuntimeError(f"expected bfloat16, got {next(model.parameters()).dtype}")
    resident = sum(torch.cuda.memory_allocated(i)
                   for i in range(torch.cuda.device_count())) / 2**30
    print(f"    {key:16s} on {len(gpus)}x {gpus[0] if gpus else '?'}, "
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
        print(f"    {key:16s} {arm:18s} {len(receipts):3d} receipts  {timings[arm]:6.1f}s", flush=True)

    del model, tokenizer
    gc.collect()
    torch.cuda.empty_cache()
    return {"weights_sha256": weights["aggregate_sha256"],
            "weights_bytes": weights["total_bytes"],
            "arm_seconds": timings, "total_seconds": round(time.time() - t0, 1),
            "candidate_token_ids": ids}


def main() -> None:
    ap = argparse.ArgumentParser(description="Score the sealed b15 panel on CUDA.")
    ap.add_argument("--project", type=Path, default=Path("."))
    ap.add_argument("--registry", type=Path, default=None)
    ap.add_argument("--table", default="b20_model", help="registry table to read")
    ap.add_argument("--key", action="append", help="model key; repeatable, default all")
    ap.add_argument("--keep-weights", action="store_true",
                    help="do not delete the snapshot after scoring")
    a = ap.parse_args()
    project = a.project.resolve()

    rows = _rows(project / DATA / "public/panel.jsonl")
    seal = json.loads((project / DATA / "public/seal.json").read_text())
    print(f"panel {len(rows)} items, seal {seal['seal_id'][:16]}")

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
            # a reason to abandon the sweep. Record it and carry on.
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
