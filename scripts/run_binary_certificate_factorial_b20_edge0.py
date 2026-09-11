#!/usr/bin/env python3
"""b20 - the b15 ten-arm decomposition on an Edge0 streaming-MoE checkpoint.

Why this checkpoint. Every model in the paper is dense, so its parameter ladder
conflates two things that a mixture-of-experts separates: how much capacity a
model has, and how much of it runs on any one token. Edge0-35B-A3B is 35B total
with 4 of 256 experts active, so roughly 3B active -- which lands exactly where
the sweep already found viability (Qwen2.5-3B clears the floor). It is therefore
the one checkpoint available that can ask whether viability tracks ACTIVE or
TOTAL parameters. Nothing in the existing twelve can answer that.

Why the edge0 runtime rather than mlx-lm. The checkpoint ships as int4 with
unmerged LoRA and prerouter adapters and only its own runtime assembles them.
That is a third backend, and the paper already shows a backend can flip a
verdict, so this run is reported as its own thing rather than merged into a
table of mlx-lm rows.

Scoring semantics match the frozen b15 runner: same prompt bytes, same
single-token candidate check, same argmax over candidate logits, same receipt
fields. The engine exposes raw logits through prefill() -> next_logits(), so no
text is generated and nothing is parsed. The answer authority is never read.
"""
from __future__ import annotations

import argparse, hashlib, json, time
from pathlib import Path
from typing import Any, Mapping, Sequence

from cc_instruments import modelcache

VERSION = "binary-certificate-factorial-b20-edge0"
DATA = Path("data/cognitive_core/binary_certificate_factorial_b15")   # the SAME sealed panel
RUN = Path("runs/cognitive_core/binary_certificate_factorial_b20_edge0")
ARMS = ("none", "irrelevant", "same_entity_irrelevant", "truncate_3", "truncate_2",
        "truncate_1", "broken_chain", "misleading", "shuffled", "full")
CANDIDATES = ("Yes", "No")


def _canonical(v: Any) -> bytes:
    return json.dumps(v, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(v: Any) -> str:
    return hashlib.sha256(_canonical(v)).hexdigest()


def _rows(p: Path):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _candidate_ids(tok: Any) -> dict[str, int]:
    ids: dict[str, int] = {}
    for c in CANDIDATES:
        enc = tok.encode(c)
        enc = [t for t in enc]
        if len(enc) != 1:
            raise RuntimeError(f"{c!r} is not a single token for this tokenizer: {enc}")
        ids[c] = int(enc[0])
    if len(set(ids.values())) != len(ids):
        raise RuntimeError("candidate tokens are not distinct")
    return ids


def _score_arm(engine, tok, rows: Sequence[Mapping[str, Any]], arm: str,
               ids: Mapping[str, int], model_key: str, mx) -> list[Mapping[str, Any]]:
    out: list[Mapping[str, Any]] = []
    for row in rows:
        # The engine carries KV state and a prerouter cache across calls; without
        # a reset each item would be scored in the context of the previous one.
        engine.reset()
        tokens = tok.encode(row["prompts"][arm])
        engine.prefill(tokens)
        logits = engine.next_logits()          # 1-D over the vocabulary
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


def main() -> None:
    ap = argparse.ArgumentParser(description="Score the sealed b15 panel on an Edge0 engine.")
    ap.add_argument("--project", type=Path, default=Path("."))
    ap.add_argument("--model-dir", type=Path, required=True)
    ap.add_argument("--key", default="edge0_35b_a3b")
    ap.add_argument("--repo", default="Edge0/Edge0-35B-A3B-preview")
    ap.add_argument("--revision", required=True, help="pinned commit sha of the checkpoint")
    ap.add_argument("--limit", type=int, default=None, help="smoke test: first N items only")
    ap.add_argument("--arm", action="append", help="arm; repeatable, default all ten")
    a = ap.parse_args()
    project = a.project.resolve()

    import mlx.core as mx
    from edge0 import AutoEngine

    rows = _rows(project / DATA / "public/panel.jsonl")
    seal = json.loads((project / DATA / "public/seal.json").read_text())
    if a.limit:
        rows = rows[:a.limit]
    arms = tuple(a.arm) if a.arm else ARMS
    print(f"panel {len(rows)} items, seal {seal['seal_id'][:16]}, arms {len(arms)}")

    run_dir = project / RUN / a.key
    t0 = time.time()
    weights = modelcache.weight_manifest(a.model_dir)      # manifest BEFORE anything else
    engine = AutoEngine.from_pretrained(str(a.model_dir))
    tok = engine._tok
    if tok is None:
        raise RuntimeError("engine loaded without a tokenizer; cannot score candidates")
    ids = _candidate_ids(tok)
    print(f"loaded {a.key} ({weights['total_bytes']/1e9:.2f} GB)  candidates={ids}", flush=True)

    modelcache.write_json(run_dir / "control/model-manifest.json", {
        "version": VERSION, "key": a.key, "repo": a.repo, "revision": a.revision,
        "family": "edge0", "params_b_total": 35.0, "params_b_active": 3.0,
        "weights": weights, "backend": "edge0+mlx", "mlx": mx.__version__,
        "quantisation": "int4 base with unmerged LoRA and prerouter adapters"})
    modelcache.write_json(run_dir / "control/candidate-tokens.json",
                          {"version": VERSION, "key": a.key, "candidate_token_ids": ids})

    timings: dict[str, float] = {}
    for arm in arms:
        t1 = time.time()
        receipts = _score_arm(engine, tok, rows, arm, ids, a.key, mx)
        path = run_dir / f"receipts/prospective-{arm}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in receipts),
                        encoding="utf-8")
        timings[arm] = round(time.time() - t1, 1)
        print(f"    {a.key:16s} {arm:18s} {len(receipts):3d} receipts  {timings[arm]:7.1f}s", flush=True)

    engine.close()
    if not a.limit and tuple(arms) == ARMS:
        modelcache.write_json(run_dir / "control/complete.json", {
            "version": VERSION, "key": a.key, "arms": list(ARMS), "n": len(rows),
            "weights_sha256": weights["aggregate_sha256"],
            "weights_bytes": weights["total_bytes"],
            "arm_seconds": timings, "total_seconds": round(time.time() - t0, 1),
            "candidate_token_ids": ids})
    print(f"    done in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
