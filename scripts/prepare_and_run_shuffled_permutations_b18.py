#!/usr/bin/env python3
"""b18 — eight permutations of the certificate, and a direct test of adjacency.

Two things this fixes, one of them a claim the paper makes on no evidence.

1. Round-2 minor 7 / our own §6.3: `shuffled` used ONE seeded permutation per
   item, so the +46.9pp order effect is a single draw from a distribution we
   never sampled. Eight permutations give it a range, on every checkpoint --
   which matters now that the effect is known to be checkpoint-dependent
   (gemma-3-4b scores 86/96 shuffled against qwen's 14/96).

2. §6.1 asserts the model "completes a final inference when both premises are
   present *and adjacent*". `shuffled` destroys order globally and never varies
   adjacency on its own, so adjacency has never been measured. Each permutation
   here records the signed gap between the final rule and its premise, which
   turns "order matters" into a testable statement about adjacency: if accuracy
   tracks the gap rather than global disorder, that is a mechanism.

Arm `perm_identity` re-scores truncate_1's exact bytes. It must reproduce the
b15 truncate_1 receipts, and is a free check that this runner is byte-faithful
to the frozen one.
"""
from __future__ import annotations

import argparse, gc, hashlib, json, random, re, time
from pathlib import Path
from cc_instruments import modelcache

VERSION = "shuffled-permutations-b18"
B15 = Path("data/cognitive_core/binary_certificate_factorial_b15")
DATA = Path("data/cognitive_core/shuffled_permutations_b18")
RUN = Path("runs/cognitive_core/shuffled_permutations_b18")
CANDIDATES = ("Yes", "No")
N_PERMS = 8
SEED_BASE = 2026090701           # distinct from b15's shuffled seed
PREFIX = "Solver record: "


def _rows(p: Path):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _canon(v): return json.dumps(v, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
def _digest(v): return hashlib.sha256(_canon(v)).hexdigest()


def _split_record(prompt: str) -> tuple[list[str], list[str]]:
    """Return (the four prompt lines, the record's sentences)."""
    lines = prompt.split("\n")
    assert len(lines) == 4, f"expected 4 prompt lines, got {len(lines)}"
    assert lines[2].startswith(PREFIX), "solver record line has moved"
    body = lines[2][len(PREFIX):].strip()
    sentences = [s + "." for s in body.split(". ") if s]
    sentences[-1] = sentences[-1].rstrip(".") + "."
    assert " ".join(sentences) == body, "record did not round-trip through the split"
    return lines, sentences


def _key_indices(sentences: list[str], query: str) -> tuple[int, int]:
    """Locate the final rule and the premise it fires on, by structure."""
    m = re.fullmatch(r"Query: (\w+) is (\w+)\. Answer:", query.strip())
    assert m, f"unexpected query shape: {query!r}"
    entity, predicate = m.group(1), m.group(2)
    # entailed items end on a positive final rule, contradicted ones on a negated
    # rule ("All X people are not <pred>."); both fire on the same premise shape.
    rule = [i for i, s in enumerate(sentences)
            if re.fullmatch(rf"All (\w+) people are (?:not )?{predicate}\.", s)]
    assert len(rule) == 1, f"expected one final rule for {predicate}, found {len(rule)}"
    antecedent = re.fullmatch(r"All (\w+) people are (?:not )?\w+\.",
                              sentences[rule[0]]).group(1)
    premise = [i for i, s in enumerate(sentences) if s == f"{entity} is {antecedent}."]
    assert len(premise) == 1, f"expected one premise {entity} is {antecedent}."
    return rule[0], premise[0]


def main() -> None:
    ap = argparse.ArgumentParser(description="Eight certificate permutations, scored.")
    ap.add_argument("--project", type=Path, default=Path("."))
    ap.add_argument("--key", default="qwen2p5_3b_4bit")
    a = ap.parse_args(); root = a.project.resolve()
    data, run = root / DATA, root / RUN / a.key

    pub = _rows(root / B15 / "public/panel.jsonl")
    auth = {r["task_id"]: r for r in _rows(root / B15 / "sealed/authority.jsonl")}
    arms = ["perm_identity"] + [f"perm_{i}" for i in range(1, N_PERMS + 1)]

    items, geometry = [], []
    for r in pub:
        lines, sentences = _split_record(r["prompts"]["truncate_1"])
        rule_i, prem_i = _key_indices(sentences, lines[3])
        assert rule_i == len(sentences) - 1 and prem_i == len(sentences) - 2, (
            "truncate_1 is expected to end premise-then-rule; got "
            f"rule at {rule_i}, premise at {prem_i} of {len(sentences)}")

        prompts, geo = {"perm_identity": r["prompts"]["truncate_1"]}, {}
        geo["perm_identity"] = {"gap": rule_i - prem_i, "rule_after_premise": True}
        for i in range(1, N_PERMS + 1):
            order = list(range(len(sentences)))
            random.Random(f"{SEED_BASE}-{r['task_id']}-{i}").shuffle(order)
            permuted = [sentences[j] for j in order]
            prompts[f"perm_{i}"] = "\n".join(
                [lines[0], lines[1], PREFIX + " ".join(permuted), lines[3]])
            nr, np_ = order.index(rule_i), order.index(prem_i)
            geo[f"perm_{i}"] = {"gap": nr - np_, "rule_after_premise": nr > np_}
        items.append({"task_id": r["task_id"].replace("b15-", "b18-", 1),
                      "version": VERSION, "query": r["query"], "prompts": prompts})
        geometry.append({"task_id": r["task_id"].replace("b15-", "b18-", 1),
                         "n_lines": len(sentences), "geometry": geo})

    authority = [{"task_id": r["task_id"].replace("b15-", "b18-", 1),
                  "answer": auth[r["task_id"]]["answer"]} for r in pub]
    for path, rowset in ((data / "public/panel.jsonl", items),
                         (data / "public/geometry.jsonl", geometry),
                         (data / "sealed/authority.jsonl", authority)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in rowset),
                        encoding="utf-8")
    seal = {"version": VERSION, "n": len(items), "arms": arms, "candidates": list(CANDIDATES),
            "n_permutations": N_PERMS, "seed_base": SEED_BASE,
            "derived_from": "binary_certificate_factorial_b15 truncate_1",
            "only_change": "order of the solver-record sentences; every other byte identical",
            "public_sha256": hashlib.sha256((data / "public/panel.jsonl").read_bytes()).hexdigest()}
    (data / "public/seal.json").write_text(json.dumps(seal, indent=2, sort_keys=True) + "\n")
    print(f"sealed {len(items)} items x {len(arms)} arms ({N_PERMS} permutations + identity)")

    from mlx_lm import load
    import mlx.core as mx
    entry = next(e for e in modelcache.load_registry(root / "models.toml")["b15_model"]
                 if e["key"] == a.key)
    snap = modelcache.download(entry["repo"], entry["revision"])
    modelcache.write_json(run / "control/model-manifest.json",
                          {"version": VERSION, **{k: entry[k] for k in ("key", "repo", "revision")},
                           "weights": modelcache.weight_manifest(snap)})
    model, tok = load(str(snap), tokenizer_config={"trust_remote_code": False})
    ids = {}
    for c in CANDIDATES:
        e = tok.encode(c, add_special_tokens=False)
        assert len(e) == 1, f"{c} is not a single token"
        ids[c] = int(e[0])
    print(f"candidates {ids}")

    t0 = time.time()
    for arm in arms:
        out = []
        for row in items:
            lg = model(mx.array([tok.encode(row["prompts"][arm])]))[0, -1]
            sc = mx.array(lg).astype(mx.float32).tolist()
            pick = {c: float(sc[i]) for c, i in ids.items()}
            body = {"version": VERSION, "stage": "prospective", "arm": arm,
                    "task_id": row["task_id"],
                    "candidate": max(pick, key=lambda k: pick[k]),
                    "candidate_token_scores": pick, "raw_generation_used": False}
            out.append({**body, "receipt_id": _digest(body)})
        p = run / f"receipts/prospective-{arm}.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in out), encoding="utf-8")
        print(f"  {arm:14s} {len(out)} receipts")
    del model, tok; gc.collect()
    try: mx.clear_cache()
    except AttributeError: pass
    modelcache.delete(entry["repo"], entry["revision"])
    modelcache.write_json(run / "control/complete.json",
                          {"version": VERSION, "arms": arms, "n": len(items),
                           "seconds": round(time.time() - t0, 1)})
    print(f"complete in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
