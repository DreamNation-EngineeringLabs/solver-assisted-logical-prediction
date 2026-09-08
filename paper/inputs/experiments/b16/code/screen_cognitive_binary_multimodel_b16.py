#!/usr/bin/env python3
"""b16 stage 1: eligibility screen across candidate models.

Streams one model at a time -- download, hash, verify candidate tokenisation,
one dummy prefill, delete -- so peak disk is a single model rather than the
whole candidate set. Resumable: a model with a completed screen record is
skipped, never re-downloaded.

This screen makes NO experimental claim. It answers only: can this model be
scored by direct next-token likelihood over our candidate labels at all? Two
outcome kinds are kept strictly apart:

  * `incompatible` / `load_failed` -- tooling limitations. Excluded, and NOT a
    finding about the model.
  * everything else -- the model is eligible, and any degeneracy it later shows
    on the sealed panel IS a reportable result about substrate viability.

Usage:
    python scripts/screen_cognitive_binary_multimodel_b16.py --resolve-revisions
    python scripts/screen_cognitive_binary_multimodel_b16.py --screen
"""
from __future__ import annotations

import argparse
import json
import re
import time
import traceback
from pathlib import Path
from typing import Any, Mapping

from cc_instruments import modelcache

VERSION = "binary-multimodel-survey-b16-screen-v1"
RUN = Path("runs/cognitive_core/binary_multimodel_b16")
PROBE = ("Use only the stated logical facts and rules. Answer exactly Yes or No.\n"
         "Fact: Pava is copper. Rule: All copper people are calm.\n"
         "Query: Pava is calm. Answer:")


def _record_path(project: Path, key: str) -> Path:
    return project / RUN / key / "control/screen.json"


def _resolve_revisions(project: Path, registry_path: Path) -> None:
    """Fill empty `revision` fields with the current head sha, in place."""
    reg = modelcache.load_registry(registry_path)
    text = registry_path.read_text(encoding="utf-8")
    for entry in reg["model"]:
        if entry.get("revision"):
            continue
        try:
            sha = modelcache.resolve_revision(entry["repo"])
        except Exception as exc:                       # repo missing / renamed / gated
            print(f"  {entry['key']:16s} UNRESOLVED  {type(exc).__name__}: {exc}")
            continue
        # match the revision line that FOLLOWS this repo line, tolerating trailing comments
        pattern = re.compile(r'(repo\s*=\s*"' + re.escape(entry["repo"]) + r'".*?\n\s*revision\s*=\s*)""',
                             re.DOTALL)
        text, count = pattern.subn(lambda m: m.group(1) + f'"{sha}"', text, count=1)
        if not count:
            print(f"  {entry['key']:16s} WARNING: could not write revision back")
            continue
        print(f"  {entry['key']:16s} {sha}")
    registry_path.write_text(text, encoding="utf-8")
    print("revisions written back to models.toml")


def _screen_one(entry: Mapping[str, Any], candidates: Mapping[str, list[str]]) -> Mapping[str, Any]:
    """Download, hash, verify tokens, one prefill, then delete. Manifest first."""
    from mlx_lm import load
    import mlx.core as mx

    repo, rev = entry["repo"], entry["revision"]
    t0 = time.time()
    snapshot = modelcache.download(repo, rev)
    weights = modelcache.weight_manifest(snapshot)          # hash BEFORE any delete
    download_s = time.time() - t0

    model, tokenizer = load(str(snapshot), tokenizer_config={"trust_remote_code": False})
    checks = {name: modelcache.verify_candidates(tokenizer, cands)
              for name, cands in candidates.items()}

    # One real prefill: catches MLX dtype/buffer faults of the kind that ended v8.
    t1 = time.time()
    ids = tokenizer.encode(PROBE)
    logits = model(mx.array([ids]))[0, -1]
    scores = [float(v) for v in mx.array(logits).astype(mx.float32).tolist()]
    prefill_s = time.time() - t1

    binary = checks["binary"]
    probe = None
    if binary["eligible"]:
        pick = {c: scores[binary["first_token_ids"][c]] for c in ("Yes", "No")}
        probe = {"candidate_scores": pick, "argmax": max(pick, key=lambda k: pick[k])}

    return {"status": "screened", "weights": weights, "candidate_checks": checks,
            "probe": probe, "vocab_size": len(scores),
            "timing_s": {"download": round(download_s, 1), "prefill": round(prefill_s, 3)}}


def _screen(project: Path, registry_path: Path, keep: bool) -> None:
    reg = modelcache.load_registry(registry_path)
    candidates = {"binary": list(reg["candidates"]),
                  "three_way": list(reg["candidates_three_way"])}
    for entry in reg["model"]:
        key = entry["key"]
        out = _record_path(project, key)
        if out.exists():
            print(f"{key:16s} already screened, skipping")
            continue
        if not entry.get("revision"):
            print(f"{key:16s} SKIP - revision not pinned (run --resolve-revisions)")
            continue
        print(f"{key:16s} screening {entry['repo']} ...", flush=True)
        try:
            body = _screen_one(entry, candidates)
        except Exception as exc:
            body = {"status": "load_failed", "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc()[-2000:]}
        body |= {"version": VERSION, "key": key, "repo": entry["repo"],
                 "revision": entry["revision"], "family": entry["family"],
                 "params_b": entry["params_b"]}
        modelcache.write_json(out, body)                    # persist BEFORE delete
        if not keep:
            freed = modelcache.delete(entry["repo"], entry["revision"])
            body_note = f"freed {freed.get('freed_bytes', 0) / 1e9:.1f} GB"
        else:
            body_note = "weights kept"
        if body["status"] == "screened":
            mode = body["candidate_checks"]["binary"]["scoring_mode"]
            three = body["candidate_checks"]["three_way"]["scoring_mode"]
            print(f"{key:16s} OK   binary={mode}  three_way={three}  {body_note}")
        else:
            print(f"{key:16s} FAIL {body['error']}  {body_note}")


def _summary(project: Path, registry_path: Path) -> None:
    reg = modelcache.load_registry(registry_path)
    rows = []
    for entry in reg["model"]:
        p = _record_path(project, entry["key"])
        if not p.exists():
            rows.append((entry["key"], entry["params_b"], "not screened", "-", "-"))
            continue
        b = json.loads(p.read_text(encoding="utf-8"))
        if b["status"] != "screened":
            rows.append((entry["key"], entry["params_b"], "LOAD FAILED", "-", "-"))
            continue
        rows.append((entry["key"], entry["params_b"], "ok",
                     b["candidate_checks"]["binary"]["scoring_mode"],
                     b["candidate_checks"]["three_way"]["scoring_mode"]))
    print(f"\n{'model':18s} {'B':>5s}  {'status':12s} {'binary':22s} three-way")
    for k, n, s, b2, b3 in rows:
        print(f"{k:18s} {n:5.1f}  {s:12s} {b2:22s} {b3}")
    elig = sum(1 for r in rows if r[3] in ("single_token", "first_token_fallback"))
    print(f"\neligible for binary scoring: {elig}/{len(rows)}")


def main() -> None:
    ap = argparse.ArgumentParser(description="b16 model eligibility screen.")
    ap.add_argument("--project", type=Path, default=Path("."))
    ap.add_argument("--registry", type=Path, default=None)
    ap.add_argument("--resolve-revisions", action="store_true")
    ap.add_argument("--screen", action="store_true")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--keep-weights", action="store_true",
                    help="do not delete after screening (uses far more disk)")
    args = ap.parse_args()
    project = args.project.resolve()
    registry = args.registry or project / "models.toml"
    if args.resolve_revisions:
        _resolve_revisions(project, registry)
    if args.screen:
        _screen(project, registry, args.keep_weights)
    if args.summary or not (args.resolve_revisions or args.screen):
        _summary(project, registry)


if __name__ == "__main__":
    main()
