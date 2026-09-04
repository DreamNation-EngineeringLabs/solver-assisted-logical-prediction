#!/usr/bin/env python3
"""b17 — does the model DETECT a broken chain, or merely fail to complete one?

Peer review, Major 4: on a binary panel these two are indistinguishable, because
the correct answer under a broken certificate IS the model's default label. Every
non-completable b15 arm lands on the identical point (0/96 entailed, d' = 0.000,
c = 2.565), which "detected the break" and "found no pattern to complete" both
predict.

The discriminating test, as the reviewer set it out: b15's `broken_chain` items
are certified UNDETERMINED under the displayed lines. Score them with three
candidates instead of two.

  a validity tracker  -> Unknown   (the shown lines do not settle the query)
  a pattern completer -> No        (its default label, unchanged)

Controls scored in the same run: `truncate_1`, where a completable chain should
still yield Yes, and `irrelevant`, which fixes the default under three
candidates. Panel, theories, certificates and queries are byte-identical to b15;
only the instruction line and the candidate set change, and that change is
recorded in the seal.
"""
from __future__ import annotations
import argparse, gc, hashlib, json, time
from pathlib import Path
from cc_instruments import modelcache

VERSION = "three-class-broken-chain-b17"
B15 = Path("data/cognitive_core/binary_certificate_factorial_b15")
DATA = Path("data/cognitive_core/three_class_broken_chain_b17")
RUN = Path("runs/cognitive_core/three_class_broken_chain_b17")
ARMS = ("irrelevant", "broken_chain", "truncate_1")
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
        items.append({"task_id": r["task_id"].replace("b15-", "b17-", 1),
                      "version": VERSION, "query": r["query"], "prompts": prompts})
    # the ground truth is unchanged for truncate_1/irrelevant (the THEORY still
    # settles the query); for broken_chain the certified verdict of the DISPLAYED
    # LINES is undetermined, which is the prediction under test.
    authority = [{"task_id": r["task_id"].replace("b15-", "b17-", 1),
                  "theory_answer": auth[r["task_id"]]["answer"],
                  "displayed_lines_verdict_broken_chain":
                      auth[r["task_id"]]["broken_chain_certification"]["verdict"]}
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
