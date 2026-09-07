#!/usr/bin/env python3
"""b17b — the `none` arm under three candidates, as an abstention floor.

Peer review, round 2, minor 11: b17 used `irrelevant` as its abstention
baseline, which is defensible but conflates two causes of the 75.0% Unknown
rate. A record is present in that arm, so the rate could reflect either

  (a) the three-candidate instruction alone -- the model is simply willing to
      say Unknown when offered the option; or
  (b) the presence of a query-irrelevant record, which actively invites it.

`none` supplies no solver record at all under the same instruction and candidate
set, separating the two. If `none` and `irrelevant` agree, the instruction is
doing the work and `irrelevant` is a clean baseline; if they differ, the b17
delta is measured against a moving reference and must be read accordingly.

Same panel, same three candidates, byte-identical theories and queries; the b15
`none` prompt with the instruction line swapped, exactly as b17 did for its
three arms. Written as a new script rather than an edit to the frozen b17 runner
so the lineage stays inspectable.
"""
from __future__ import annotations
import argparse, gc, hashlib, json, time
from pathlib import Path
from cc_instruments import modelcache

VERSION = "three-class-none-baseline-b17b"
B15 = Path("data/cognitive_core/binary_certificate_factorial_b15")
DATA = Path("data/cognitive_core/three_class_none_baseline_b17b")
RUN = Path("runs/cognitive_core/three_class_none_baseline_b17b")
ARMS = ("none",)
CANDIDATES = ("Yes", "No", "Unknown")
OLD_SYS = "Use only the supplied logical facts, rules, and solver record. Answer exactly Yes or No."
NEW_SYS = ("Use only the supplied logical facts, rules, and solver record. "
           "Answer exactly Yes, No, or Unknown.")


def _rows(p): return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
def _canon(v): return json.dumps(v, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
def _digest(v): return hashlib.sha256(_canon(v)).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", type=Path, default=Path("."))
    ap.add_argument("--key", default="qwen2p5_3b_4bit")
    a = ap.parse_args(); root = a.project.resolve()
    data, run = root / DATA, root / RUN / a.key

    # ---- seal: derive from b15 with the instruction line swapped -------------
    pub = _rows(root / B15 / "public/panel.jsonl")
    auth = {r["task_id"]: r for r in _rows(root / B15 / "sealed/authority.jsonl")}
    items = []
    for r in pub:
        prompts = {}
        for arm in ARMS:
            p = r["prompts"][arm]
            assert p.startswith(OLD_SYS), "b15 prompt shape changed"
            prompts[arm] = NEW_SYS + p[len(OLD_SYS):]
        items.append({"task_id": r["task_id"].replace("b15-", "b17b-", 1),
                      "version": VERSION, "query": r["query"], "prompts": prompts})
    # the ground truth is unchanged for truncate_1/irrelevant (the THEORY still
    # settles the query); for broken_chain the certified verdict of the DISPLAYED
    # LINES is undetermined, which is the prediction under test.
    # No certificate is displayed in this arm, so there is no displayed-lines
    # verdict to record; the theory answer is the only ground truth that applies.
    authority = [{"task_id": r["task_id"].replace("b15-", "b17b-", 1),
                  "theory_answer": auth[r["task_id"]]["answer"]}
                 for r in pub]
    for path, rows in ((data / "public/panel.jsonl", items),
                       (data / "sealed/authority.jsonl", authority)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in rows), encoding="utf-8")
    seal = {"version": VERSION, "n": len(items), "arms": list(ARMS), "candidates": list(CANDIDATES),
            "derived_from": "binary_certificate_factorial_b15",
            "only_change": "instruction line and candidate set; theories, certificates and queries byte-identical",
            "public_sha256": hashlib.sha256((data / "public/panel.jsonl").read_bytes()).hexdigest()}
    (data / "public/seal.json").write_text(json.dumps(seal, indent=2, sort_keys=True) + "\n")
    print(f"sealed {len(items)} items x {len(ARMS)} arms")

    # ---- score ---------------------------------------------------------------
    from mlx_lm import load
    import mlx.core as mx
    entry = next(e for e in modelcache.load_registry(root / "models.toml")["b15_model"] if e["key"] == a.key)
    snap = modelcache.download(entry["repo"], entry["revision"])
    w = modelcache.weight_manifest(snap)
    modelcache.write_json(run / "control/model-manifest.json", {"version": VERSION, **{k: entry[k] for k in ("key","repo","revision")}, "weights": w})
    model, tok = load(str(snap), tokenizer_config={"trust_remote_code": False})
    ids = {}
    for c in CANDIDATES:
        e = tok.encode(c, add_special_tokens=False)
        assert len(e) == 1, f"{c} is not a single token"
        ids[c] = int(e[0])
    print(f"candidates {ids}")
    t0 = time.time()
    for arm in ARMS:
        out = []
        for row in items:
            lg = model(mx.array([tok.encode(row["prompts"][arm])]))[0, -1]
            sc = mx.array(lg).astype(mx.float32).tolist()
            pick = {c: float(sc[i]) for c, i in ids.items()}
            body = {"version": VERSION, "stage": "prospective", "arm": arm, "task_id": row["task_id"],
                    "candidate": max(pick, key=lambda k: pick[k]), "candidate_token_scores": pick,
                    "raw_generation_used": False}
            out.append({**body, "receipt_id": _digest(body)})
        p = run / f"receipts/prospective-{arm}.jsonl"; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in out), encoding="utf-8")
        print(f"  {arm:14s} {len(out)} receipts")
    del model, tok; gc.collect()
    try: mx.clear_cache()
    except AttributeError: pass
    modelcache.delete(entry["repo"], entry["revision"])
    modelcache.write_json(run / "control/complete.json", {"version": VERSION, "arms": list(ARMS),
                                                          "n": len(items), "seconds": round(time.time()-t0,1)})
    print(f"complete in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
