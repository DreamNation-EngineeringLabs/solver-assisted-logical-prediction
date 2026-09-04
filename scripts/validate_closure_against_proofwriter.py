#!/usr/bin/env python3
"""Validate cc_instruments.closure against ProofWriter OWA ground truth.

The merged three-class panel depends on being able to certify that an item is
genuinely underdetermined. That certification is only as good as the saturation
check, so before generating any panel we test the checker against an independent
labelled corpus: ProofWriter's OWA splits, which ship True/False/Unknown answers
produced by a different implementation.

Agreement below 100% on any depth means the checker is not fit to seal a panel.
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

from cc_instruments import closure as cl

ANSWER_TO_VERDICT = {"True": cl.ENTAILED, "False": cl.CONTRADICTED, "Unknown": cl.UNDETERMINED}
SPLITS = ["depth-0", "depth-1", "depth-2", "depth-3", "depth-5"]


def _theory(row: dict) -> tuple[list, list]:
    facts = [cl.parse_atom(v["representation"])
             for v in row["triples"].values() if v]
    rules = [cl.parse_rule(v["representation"])
             for v in row["rules"].values() if v]
    return facts, rules


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-per-split", type=int, default=400)
    ap.add_argument("--out", type=Path, default=Path("results/closure_validation_v1.json"))
    args = ap.parse_args()

    from huggingface_hub import hf_hub_download
    import pyarrow.parquet as pq

    overall = collections.Counter()
    per_split, disagreements = {}, []
    confusion: collections.Counter = collections.Counter()

    for split in SPLITS:
        path = hf_hub_download("hitachi-nlp/proofwriter_processed_OWA",
                               f"{split}/test-00000-of-00001.parquet", repo_type="dataset")
        rows = pq.read_table(path).to_pylist()[: args.limit_per_split]
        agree = total = unusable = 0
        for row in rows:
            try:
                facts, rules = _theory(row)
                c = cl.saturate(facts, rules)
            except Exception as exc:
                unusable += 1
                disagreements.append({"split": split, "id": row["id"], "error": str(exc)[:200]})
                continue
            if not c.usable:
                unusable += 1
                continue
            for qid, q in (row["questions"] or {}).items():
                if not q or q.get("answer") not in ANSWER_TO_VERDICT:
                    continue
                expected = ANSWER_TO_VERDICT[q["answer"]]
                got = cl.classify(cl.parse_atom(q["representation"]), c)
                total += 1
                confusion[(expected, got)] += 1
                if got == expected:
                    agree += 1
                elif len(disagreements) < 25:
                    disagreements.append({"split": split, "id": row["id"], "q": qid,
                                          "question": q.get("question"),
                                          "expected": expected, "got": got})
        per_split[split] = {"theories": len(rows), "unusable_theories": unusable,
                            "questions": total, "agree": agree,
                            "agreement": agree / total if total else None}
        overall["agree"] += agree; overall["total"] += total
        print(f"  {split:9s} {agree:5d}/{total:5d} = "
              f"{(agree/total*100 if total else 0):6.2f}%   unusable theories: {unusable}")

    print(f"\nOVERALL {overall['agree']}/{overall['total']} = "
          f"{overall['agree']/overall['total']*100:.4f}%")
    print("\nconfusion (expected -> got):")
    for (e, g), n in sorted(confusion.items(), key=lambda kv: -kv[1]):
        mark = "" if e == g else "   <-- DISAGREEMENT"
        print(f"  {e:14s} -> {g:14s} {n:6d}{mark}")
    if disagreements:
        print(f"\nfirst disagreements/errors ({len(disagreements)}):")
        for d in disagreements[:8]:
            print("   ", d)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({
        "version": "closure-validation-v1",
        "corpus": "hitachi-nlp/proofwriter_processed_OWA (test splits)",
        "per_split": per_split,
        "overall_agreement": overall["agree"] / overall["total"],
        "questions_checked": overall["total"],
        "confusion": {f"{e}->{g}": n for (e, g), n in confusion.items()},
        "disagreements": disagreements,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"\nwritten -> {args.out}")


if __name__ == "__main__":
    main()
