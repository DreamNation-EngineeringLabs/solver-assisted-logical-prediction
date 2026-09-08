#!/usr/bin/env python3
"""Run b15: qualification smoke check, then the ten-arm prospective factorial.

Single model, 4-bit, pinned to `4f83f8f1...` -- the exact snapshot the frozen b14
runner used -- so b15 scores on byte-identical weights and b14's 50.0% / 87.0%
anchors carry over without a weights caveat.

The qualification is a RECORDED SMOKE CHECK, not a blocking gate. b14 ran this
exact screen on these exact weights and passed (36/36, 33/36), and b16 showed a
direct-fact screen says nothing about task competence -- it passed 36/36 while
the model was degenerate on the real panel. Its value here is verifying the
runtime path end to end and preserving comparability with b14. Use
`--require-qualification` to restore blocking behaviour.

The authority is never read. Candidate logits are cast to float32 and converted
through a Python list (the v10 fix for the MLX bfloat16 fault that ended v8).
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from cc_instruments import modelcache

VERSION = "binary-certificate-factorial-b15"
DATA = Path("data/cognitive_core/binary_certificate_factorial_b15")
RUN = Path("runs/cognitive_core/binary_certificate_factorial_b15")
ARMS = ("none", "irrelevant", "same_entity_irrelevant", "truncate_3", "truncate_2",
        "truncate_1", "broken_chain", "misleading", "shuffled", "full")
TEMPLATES = ("direct", "reordered")
CANDIDATES = ("Yes", "No")
THRESHOLDS = {"per_template_correct": 27, "per_class_correct": 12, "agreement": 32, "n": 36}


def _canonical(v: Any) -> bytes:
    return json.dumps(v, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(v: Any) -> str:
    return hashlib.sha256(_canonical(v)).hexdigest()


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _rows(p: Path) -> list[Mapping[str, Any]]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _candidate_ids(tok: Any) -> dict[str, int]:
    ids = {}
    for c in CANDIDATES:
        e = tok.encode(c, add_special_tokens=False)
        if len(e) != 1:
            raise RuntimeError(f"{c!r} is not a single token")
        ids[c] = int(e[0])
    if len(set(ids.values())) != len(ids):
        raise RuntimeError("candidate tokens are not distinct")
    return ids


def _score(model: Any, tok: Any, rows: Sequence[Mapping[str, Any]], key: str,
           ids: Mapping[str, int], stage: str, mx: Any) -> list[Mapping[str, Any]]:
    out = []
    for row in rows:
        logits = model(mx.array([tok.encode(row["prompts"][key])]))[0, -1]
        scores = mx.array(logits).astype(mx.float32).tolist()
        picked = {c: float(scores[i]) for c, i in ids.items()}
        body = {"version": VERSION, "stage": stage, "arm" if stage == "prospective" else "template": key,
                "task_id": row["task_id"], "candidate": max(picked, key=lambda k: picked[k]),
                "candidate_token_scores": picked,
                "top_two_margin": abs(picked["Yes"] - picked["No"]),
                "raw_generation_used": False}
        out.append({**body, "receipt_id": _digest(body)})
    return out


def _write(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Run the b15 ten-arm factorial.")
    ap.add_argument("stage", choices=("qualify", "prospective", "all"))
    ap.add_argument("--project", type=Path, default=Path("."))
    ap.add_argument("--require-qualification", action="store_true",
                    help="treat the smoke check as a blocking gate (default: recorded only)")
    ap.add_argument("--keep-weights", action="store_true")
    args = ap.parse_args()
    project = args.project.resolve()
    entry = modelcache.load_registry(project / "models.toml")["b15_model"][0]
    run_dir = project / RUN / entry["key"]

    seal = json.loads((project / DATA / "public/seal.json").read_text(encoding="utf-8"))
    panel = project / seal["public_path"]
    if _sha256(panel) != seal["public_sha256"]:
        raise RuntimeError("sealed panel hash mismatch; refusing to score a modified panel")
    qual_path = project / seal["qualification_public_path"]
    if _sha256(qual_path) != seal["qualification_public_sha256"]:
        raise RuntimeError("qualification panel hash mismatch")

    from mlx_lm import load
    import mlx.core as mx

    t0 = time.time()
    snapshot = modelcache.download(entry["repo"], entry["revision"])
    weights = modelcache.weight_manifest(snapshot)
    modelcache.write_json(run_dir / "control/model-manifest.json", {
        "version": VERSION, **{k: entry[k] for k in ("key", "repo", "revision", "family", "params_b")},
        "weights": weights, "matches_b14_snapshot": True})
    model, tok = load(str(snapshot), tokenizer_config={"trust_remote_code": False})
    ids = _candidate_ids(tok)
    print(f"loaded {entry['key']} ({weights['total_bytes']/1e9:.2f} GB)  candidates={ids}", flush=True)

    try:
        qualified = None
        if args.stage in ("qualify", "all"):
            qrows = _rows(qual_path)
            qauth = {r["task_id"]: r["answer"] for r in
                     _rows(project / DATA / "sealed/qualification-authority.jsonl")}
            per, chosen = {}, {}
            for tmpl in TEMPLATES:
                receipts = _score(model, tok, qrows, tmpl, ids, "qualification", mx)
                _write(run_dir / f"receipts/qualification-{tmpl}.jsonl", receipts)
                chosen[tmpl] = {r["task_id"]: r["candidate"] for r in receipts}
                correct = sum(1 for r in receipts if r["candidate"] == qauth[r["task_id"]])
                by_class = {}
                for r in receipts:
                    a = qauth[r["task_id"]]
                    by_class[a] = by_class.get(a, 0) + int(r["candidate"] == a)
                per[tmpl] = {"correct": correct, "by_class": by_class}
                print(f"  qualification[{tmpl}] {correct}/{len(qrows)}  {by_class}", flush=True)
            agree = sum(1 for t in chosen[TEMPLATES[0]]
                        if chosen[TEMPLATES[0]][t] == chosen[TEMPLATES[1]][t])
            qualified = (all(v["correct"] >= THRESHOLDS["per_template_correct"] for v in per.values())
                         and all(c >= THRESHOLDS["per_class_correct"]
                                 for v in per.values() for c in v["by_class"].values())
                         and agree >= THRESHOLDS["agreement"])
            modelcache.write_json(run_dir / "results/qualification.json", {
                "version": VERSION, "per_template": per, "agreement": agree,
                "thresholds": THRESHOLDS, "passed": qualified,
                "role": "recorded smoke check; blocking only with --require-qualification"})
            print(f"  agreement {agree}/{len(qrows)}  passed={qualified}", flush=True)

        if args.stage in ("prospective", "all"):
            if args.require_qualification and qualified is False:
                print(json.dumps({"status": "prospective_not_authorized"}), flush=True)
                return
            rows = _rows(panel)
            timings = {}
            for arm in ARMS:
                t1 = time.time()
                receipts = _score(model, tok, rows, arm, ids, "prospective", mx)
                _write(run_dir / f"receipts/prospective-{arm}.jsonl", receipts)
                timings[arm] = round(time.time() - t1, 1)
                print(f"  {arm:24s} {len(receipts)} receipts  {timings[arm]:6.1f}s", flush=True)
            body = {"version": VERSION, "key": entry["key"], "revision": entry["revision"],
                    "arms": list(ARMS), "n": len(rows), "arm_seconds": timings,
                    "qualification_passed": qualified,
                    "weights_sha256": weights["aggregate_sha256"],
                    "total_seconds": round(time.time() - t0, 1)}
            modelcache.write_json(run_dir / "control/complete.json",
                                  {**body, "completion_id": _digest(body)})
            print(f"COMPLETE in {body['total_seconds']:.0f}s", flush=True)
    finally:
        del model, tok
        gc.collect()
        try:
            mx.clear_cache()
        except AttributeError:
            pass
        if not args.keep_weights:
            freed = modelcache.delete(entry["repo"], entry["revision"])
            print(f"freed {freed.get('freed_bytes', 0)/1e9:.1f} GB", flush=True)


if __name__ == "__main__":
    main()
