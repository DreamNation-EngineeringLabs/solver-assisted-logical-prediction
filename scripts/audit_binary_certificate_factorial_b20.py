#!/usr/bin/env python3
"""b20 — re-verify the scale extension without a model. Standard library only.

Independent of analyse_*_b20.py by construction: it recomputes the headline
values from receipts by its own arithmetic and then asserts them against the
published analysis file, so a bug in either surfaces as a mismatch rather than
as agreement. Exits non-zero on any failure, and on any check it could not run.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
from statistics import NormalDist

DATA = Path("data/cognitive_core/binary_certificate_factorial_b15")
RUNS = {"qwen3_32b":     "runs/cognitive_core/binary_certificate_factorial_b20_cuda/qwen3_32b",
        "llama3p3_70b":  "runs/cognitive_core/binary_certificate_factorial_b20_cuda/llama3p3_70b"}
ANALYSIS = Path("results/b20_analysis_v2.json")


def canonical(v) -> bytes:
    return json.dumps(v, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def rows(p: Path):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def dprime(hits: int, fa: int, n: int) -> float:
    """Loglinear d', exact inverse normal CDF.

    v1 of the analysis used a polynomial approximation to erfinv and this audit
    did not check d' at all, so a 0.007 discrepancy reached the manuscript. It
    is checked here now, against the same primitive every other analysis uses.
    """
    z = NormalDist().inv_cdf
    return z((hits + 0.5) / (n + 1)) - z((fa + 0.5) / (n + 1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", type=Path, default=Path("."))
    project = ap.parse_args().project.resolve()
    fails: list[str] = []
    checks = 0

    def check(ok: bool, label: str) -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(label)
        print(f"  {'OK  ' if ok else 'FAIL'}  {label}")

    # --- the panel these receipts claim to be about --------------------------
    seal = json.loads((project / DATA / "public/seal.json").read_text())
    panel_bytes = (project / DATA / "public/panel.jsonl").read_bytes()
    check(hashlib.sha256(panel_bytes).hexdigest() == seal["public_sha256"],
          f"panel matches its seal ({seal['seal_id'][:16]})")

    auth = {r["task_id"]: r["answer"] for r in rows(project / DATA / "sealed/authority.jsonl")}
    ent = [t for t, a in auth.items() if a == "Yes"]
    con = [t for t, a in auth.items() if a == "No"]
    check(len(auth) == 192 and len(ent) == 96 and len(con) == 96,
          f"authority is 192 items, {len(ent)}/{len(con)} per class")

    published = json.loads((project / ANALYSIS).read_text())

    total_receipts = 0
    for key, rel in RUNS.items():
        run = project / rel
        if not run.exists():
            check(False, f"{key}: run directory missing")
            continue
        print(f"\n--- {key} ---")
        man = json.loads((run / "control/model-manifest.json").read_text())
        pub = published["checkpoints"][key]
        check(man["revision"] == pub["revision"], f"{key}: manifest revision matches the analysis")

        for f in sorted((run / "receipts").glob("prospective-*.jsonl")):
            arm = f.stem.replace("prospective-", "")
            recs = rows(f)
            total_receipts += len(recs)

            bad_digest = 0
            for r in recs:
                body = {k: v for k, v in r.items() if k != "receipt_id"}
                if hashlib.sha256(canonical(body)).hexdigest() != r["receipt_id"]:
                    bad_digest += 1
            ids = [r["task_id"] for r in recs]
            by = {r["task_id"]: r for r in recs}

            # recomputed here, deliberately not reusing the analysis code path
            wrong = sum(1 for t in auth if by[t]["candidate"] != auth[t])
            hits = sum(1 for t in ent if by[t]["candidate"] == "Yes")
            fa = sum(1 for t in con if by[t]["candidate"] == "Yes")
            rec_min = min(hits / 96, (96 - fa) / 96)
            dp = dprime(hits, fa, 96)
            a = pub["arms"][arm]

            ok = (bad_digest == 0 and len(ids) == len(set(ids)) == 192
                  and set(ids) == set(auth)
                  and wrong == a["incorrect"] and hits == a["entailed_correct"]
                  and fa == a["false_alarms"]
                  and abs(rec_min - a["min_per_class_recall"]) < 5e-4
                  and abs(dp - a["d_prime"]) < 5e-4
                  and all(r["raw_generation_used"] is False for r in recs))
            check(ok, f"{key}/{arm}: 192 unique receipts, digests, counts, "
                      f"min-recall, d' and no-free-text all re-derive")

        # the viability gate must agree with what the analysis published
        if "full" in pub["arms"]:
            expect = pub["arms"]["full"]["min_per_class_recall"] >= published[
                "viability_floor_min_per_class_recall"]
            check(expect == pub["viable_under_full"],
                  f"{key}: viability verdict follows from the floor, not from assertion")
            check(pub["corruption_interpreted"] == pub["viable_under_full"],
                  f"{key}: corruption is interpreted only where the checkpoint is viable")

    # --- the claim the paper makes -------------------------------------------
    lla = published["checkpoints"]["llama3p3_70b"]
    check(lla["viable_under_full"] and lla["arms"]["full"]["correct"] == 192,
          "llama3p3_70b is viable and perfect under `full` (192/192)")
    check(lla["arms"]["misleading"]["correct"] == 0,
          "llama3p3_70b answers incorrectly on every misleading item (0/192)")
    check(lla["arms"]["misleading"]["frac_margin_below_0p5"] == 0.0,
          "no misleading item sits near the decision boundary")
    check(round(lla["arms"]["misleading"]["d_prime"], 2) == -5.13,
          "the misleading d' the manuscript prints is -5.13, the censored bound "
          "every other saturated cell in the paper prints")
    check(lla["arms"]["none"]["correct"] > 96,
          f"llama3p3_70b has real unaided competence ({lla['arms']['none']['correct']}/192)")

    print(f"\n{checks - len(fails)}/{checks} checks passed over {total_receipts} receipts")
    if fails:
        print("FAILED:", *fails, sep="\n  ")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
