#!/usr/bin/env python3
"""b18 — the order effect as a distribution, and adjacency as a measured thing.

Two questions, one run.

1. The manuscript reports the order effect from ONE seeded permutation per item
   (`truncate_1 - shuffled = +46.9`pp on the 4-bit checkpoint). Eight
   permutations give it a range on every checkpoint, which matters because the
   effect is known to be checkpoint-dependent.

2. Section 6.1 asserts the model "completes a final inference when both premises
   are present *and adjacent*". `shuffled` destroys order globally and never
   varied adjacency on its own, so that claim rested on nothing. Each
   permutation here records the signed gap between the final rule and the
   premise it fires on, so accuracy can be read against the gap directly. If it
   tracks the gap, "order matters" becomes a statement about adjacency.

`perm_identity` re-scores truncate_1's exact bytes and must reproduce the b15
receipts; a mismatch means this runner is not byte-faithful and nothing below
should be believed.
"""
from __future__ import annotations

import argparse, json
from collections import defaultdict
from pathlib import Path

B15D = Path("data/cognitive_core/binary_certificate_factorial_b15")
B15R = Path("runs/cognitive_core/binary_certificate_factorial_b15")
B18D = Path("data/cognitive_core/shuffled_permutations_b18")
B18R = Path("runs/cognitive_core/shuffled_permutations_b18")
N_PERMS = 8


def _rows(p: Path):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> None:
    ap = argparse.ArgumentParser(description="Order effect distribution and adjacency.")
    ap.add_argument("--project", type=Path, default=Path("."))
    root = ap.parse_args().project.resolve()

    auth = {r["task_id"].replace("b15-", "b18-", 1): r["answer"]
            for r in _rows(root / B15D / "sealed/authority.jsonl")}
    entailed = {t for t, a in auth.items() if a == "Yes"}
    geo = {r["task_id"]: r["geometry"] for r in _rows(root / B18D / "public/geometry.jsonl")}

    out = {"version": "shuffled-permutations-b18-v1", "n_permutations": N_PERMS,
           "n_entailed": len(entailed), "checkpoints": {}}

    for run_dir in sorted((root / B18R).iterdir()):
        if not (run_dir / "control/complete.json").exists():
            continue
        key = run_dir.name
        got = {f.stem.replace("prospective-", ""):
               {r["task_id"]: r["candidate"] for r in _rows(f)}
               for f in sorted((run_dir / "receipts").glob("prospective-*.jsonl"))}

        # byte-faithfulness: perm_identity must reproduce b15's truncate_1
        b15 = {r["task_id"].replace("b15-", "b18-", 1): r["candidate"]
               for r in _rows(root / B15R / key / "receipts/prospective-truncate_1.jsonl")}
        agree = sum(got["perm_identity"][t] == b15[t] for t in b15)
        identity_ok = agree == len(b15)

        base = sum(got["perm_identity"][t] == auth[t] for t in entailed)
        perms = {}
        for i in range(1, N_PERMS + 1):
            a = f"perm_{i}"
            perms[a] = sum(got[a][t] == auth[t] for t in entailed)
        effects = sorted((base - v) / len(entailed) * 100 for v in perms.values())

        # accuracy by |gap| and by whether the rule follows its premise
        by_gap, by_dir = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])
        for i in range(1, N_PERMS + 1):
            a = f"perm_{i}"
            for t in entailed:
                g = geo[t][a]
                ok = got[a][t] == auth[t]
                by_gap[abs(g["gap"])][0] += ok; by_gap[abs(g["gap"])][1] += 1
                by_dir[g["rule_after_premise"]][0] += ok; by_dir[g["rule_after_premise"]][1] += 1

        out["checkpoints"][key] = {
            "identity_reproduces_b15_truncate_1": identity_ok,
            "identity_agreement": f"{agree}/{len(b15)}",
            "identity_correct_entailed": base,
            "per_permutation_correct_entailed": perms,
            "order_effect_pp": {"min": effects[0], "median": effects[len(effects) // 2],
                                "max": effects[-1], "all": effects},
            "accuracy_by_abs_gap": {str(k): {"correct": v[0], "n": v[1], "acc": v[0] / v[1]}
                                    for k, v in sorted(by_gap.items())},
            "accuracy_by_rule_after_premise": {
                str(k): {"correct": v[0], "n": v[1], "acc": v[0] / v[1]}
                for k, v in sorted(by_dir.items())},
        }

    for key, c in out["checkpoints"].items():
        print(f"\n{key}")
        print(f"  perm_identity reproduces b15 truncate_1: {c['identity_agreement']}"
              f" {'OK' if c['identity_reproduces_b15_truncate_1'] else '** MISMATCH **'}")
        e = c["order_effect_pp"]
        print(f"  order effect over {N_PERMS} permutations: "
              f"min {e['min']:+.1f}  median {e['median']:+.1f}  max {e['max']:+.1f} pp")
        print("  accuracy by |gap| between the final rule and its premise:")
        for g, v in c["accuracy_by_abs_gap"].items():
            print(f"     gap {g}: {v['acc']*100:5.1f}%  (n={v['n']})")
        d = c["accuracy_by_rule_after_premise"]
        print(f"  rule after premise {d.get('True',{}).get('acc',0)*100:.1f}%"
              f"  vs before {d.get('False',{}).get('acc',0)*100:.1f}%")

    path = root / "results/b18_permutations_v1.json"
    path.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"\nwrote {path.relative_to(root)}")


if __name__ == "__main__":
    main()
