#!/usr/bin/env python3
"""b20 — score the scale extension from receipts. Standard library only.

v2 supersedes v1 for one reason: v1 computed d' through a hand-rolled Winitzki
`erfinv` polynomial while every other analysis in this repo uses
`statistics.NormalDist.inv_cdf`, and its docstring claimed otherwise. On the
censored cells that matter (hits = 0, fa = 96, n = 96) the two disagree in the
second decimal --- -5.124 against the exact -5.1306 --- so the manuscript
printed -5.12 for a statistic it prints as -5.13 everywhere else. Only d'
changes; every count, rate and margin in v2 is byte-identical to v1, which is
retained unedited as the record of what was published.

Writes results/b20_analysis_v2.json. Every value is derived here from the
receipts and the sealed authority; nothing is read from another analysis file.

The viability floor is applied before anything is interpreted: a checkpoint that
fails minimum per-class recall >= 0.50 under `full` has its corruption number
recorded and flagged `interpreted: false`, on the grounds Experiment 3 gives —
a responder that answers one label to almost everything is not measuring the arm.
"""
from __future__ import annotations
import json
from pathlib import Path
from statistics import NormalDist

DATA = Path("data/cognitive_core/binary_certificate_factorial_b15")
RUNS = {"qwen3_32b":     Path("runs/cognitive_core/binary_certificate_factorial_b20_cuda/qwen3_32b"),
        "llama3p3_70b":  Path("runs/cognitive_core/binary_certificate_factorial_b20_cuda/llama3p3_70b")}
OUT = Path("results/b20_analysis_v2.json")
SUPERSEDES = Path("results/b20_analysis_v1.json")
FLOOR = 0.50


def _rows(p: Path):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def dprime(hits: int, fa: int, n: int) -> float:
    """d' with the loglinear correction.

    The same primitive the b15, b14 and v7/v8 analyses use --- the exact inverse
    normal CDF from the standard library, not an approximation to it. The
    docstring in v1 asserted this and the code did not do it.
    """
    z = NormalDist().inv_cdf
    return z((hits + 0.5) / (n + 1)) - z((fa + 0.5) / (n + 1))


def main(project: Path = Path(".")) -> None:
    auth = {r["task_id"]: r["answer"]
            for r in _rows(project / DATA / "sealed/authority.jsonl")}
    ent = [t for t, a in auth.items() if a == "Yes"]
    con = [t for t, a in auth.items() if a == "No"]
    out = {"version": "b20-analysis-v2", "n": len(auth),
           "supersedes": "b20-analysis-v1",
           "supersedes_note": "v1 computed d' with a Winitzki erfinv approximation; "
                              "v2 uses statistics.NormalDist.inv_cdf. Only d' differs.",
           "n_entailed": len(ent), "n_contradicted": len(con),
           "viability_floor_min_per_class_recall": FLOOR, "checkpoints": {}}

    for key, run in RUNS.items():
        run = project / run
        manifest = json.loads((run / "control/model-manifest.json").read_text())
        arms: dict[str, dict] = {}
        for f in sorted((run / "receipts").glob("prospective-*.jsonl")):
            arm = f.stem.replace("prospective-", "")
            r = {x["task_id"]: x for x in _rows(f)}
            if set(r) != set(auth):
                raise SystemExit(f"{key}/{arm}: receipts do not cover the panel exactly")
            hits = sum(r[t]["candidate"] == "Yes" for t in ent)
            fa = sum(r[t]["candidate"] == "Yes" for t in con)
            rec_y, rec_n = hits / len(ent), (len(con) - fa) / len(con)
            margins = sorted(x["top_two_margin"] for x in r.values())
            arms[arm] = {
                "correct": sum(r[t]["candidate"] == auth[t] for t in auth),
                "incorrect": sum(r[t]["candidate"] != auth[t] for t in auth),
                "entailed_correct": hits, "false_alarms": fa,
                "recall_entailed": round(rec_y, 4), "recall_contradicted": round(rec_n, 4),
                "min_per_class_recall": round(min(rec_y, rec_n), 4),
                "yes_rate": round(sum(v["candidate"] == "Yes" for v in r.values()) / len(r), 4),
                "d_prime": round(dprime(hits, fa, len(ent)), 3),
                "median_top_two_margin": round(margins[len(margins) // 2], 3),
                "frac_margin_below_0p5": round(sum(m < 0.5 for m in margins) / len(margins), 4)}

        viable = ("full" in arms) and arms["full"]["min_per_class_recall"] >= FLOOR
        out["checkpoints"][key] = {
            "repo": manifest["repo"], "revision": manifest["revision"],
            "backend": manifest["backend"],
            "params_b": manifest.get("params_b") or manifest.get("params_b_total"),
            "params_b_active": manifest.get("params_b_active"),
            "weights_sha256": manifest["weights"]["aggregate_sha256"],
            "viable_under_full": viable,
            "corruption_interpreted": bool(viable),
            "arms": arms}

    # Everything except d' must be unchanged from v1: this is a numerical-
    # primitive correction, not a re-analysis. Assert it rather than claim it.
    if (project / SUPERSEDES).exists():
        old = json.loads((project / SUPERSEDES).read_text())
        for ck, c in out["checkpoints"].items():
            for arm, a in c["arms"].items():
                o = old["checkpoints"][ck]["arms"][arm]
                diff = {k for k in a if k != "d_prime" and a[k] != o[k]}
                if diff:
                    raise SystemExit(f"v2 changed more than d' in {ck}/{arm}: {sorted(diff)}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    for key, c in out["checkpoints"].items():
        m = c["arms"].get("misleading", {})
        tag = "" if c["corruption_interpreted"] else "   [not interpreted: fails the floor]"
        print(f"  {key:16s} misleading {m.get('incorrect','?'):3d}/192 wrong  "
              f"d'={m.get('d_prime','?'):>6}{tag}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", type=Path, default=Path("."))
    main(ap.parse_args().project)
