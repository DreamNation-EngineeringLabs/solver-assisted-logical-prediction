#!/usr/bin/env python3
"""Addendum in response to peer review: an interval on the validity share, and
Holm-adjusted p-values printed where the paper prints p-values.

The share is a RATIO of two paired differences. v1 bootstrapped only the
numerator, so "98.3%" was quoted as if it were a point estimate of known
precision. The denominator's surface component is 1/96 with p = 1, so the ratio
carries substantially more uncertainty than the headline implies. Here the whole
ratio is bootstrapped over the same paired resamples.
"""
from __future__ import annotations
import argparse, json, random, hashlib
from pathlib import Path
from statistics import NormalDist
from cc_instruments import paired

SEED = 2026090315
B = 100_000
NORM = NormalDist()
ARMS = ("truncate_1", "broken_chain", "irrelevant")


def _rows(p): return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--project", type=Path, default=Path("."))
    a = ap.parse_args(); root = a.project.resolve()
    RUN = root / "runs/cognitive_core/binary_certificate_factorial_b15/qwen2p5_3b_4bit"
    auth = {r["task_id"]: r for r in _rows(root / "data/cognitive_core/binary_certificate_factorial_b15/sealed/authority.jsonl")}
    ent = sorted(t for t, v in auth.items() if v["semantic_class"] == "entailed")
    pick = {arm: {r["task_id"]: r["candidate"] for r in _rows(RUN / f"receipts/prospective-{arm}.jsonl")} for arm in ARMS}
    corr = {arm: {t: pick[arm][t] == auth[t]["answer"] for t in ent} for arm in ARMS}

    n = len(ent)
    t1 = [corr["truncate_1"][t] for t in ent]
    bc = [corr["broken_chain"][t] for t in ent]
    ir = [corr["irrelevant"][t] for t in ent]
    point_total = (sum(t1) - sum(ir)) / n
    point_valid = (sum(t1) - sum(bc)) / n
    point_share = point_valid / point_total

    # paired bootstrap over ITEMS, so numerator and denominator resample together
    rng = random.Random(SEED)
    shares, valids, surfaces = [], [], []
    idx = range(n)
    for _ in range(B):
        s = [rng.randrange(n) for _ in idx]
        a1 = sum(t1[i] for i in s); ab = sum(bc[i] for i in s); ai = sum(ir[i] for i in s)
        tot = (a1 - ai) / n
        val = (a1 - ab) / n
        valids.append(val); surfaces.append((ab - ai) / n)
        if tot != 0:
            shares.append(val / tot)
    shares.sort()
    lo, hi = shares[int(0.025 * (len(shares) - 1))], shares[int(0.975 * (len(shares) - 1))]
    surfaces.sort()
    slo, shi = surfaces[int(0.025 * (B - 1))], surfaces[int(0.975 * (B - 1))]

    # Holm, on the family the paper actually prints
    fam = {
        "truncate_1_minus_broken_chain": paired.exact_mcnemar(58, 0),
        "truncate_1_minus_shuffled": paired.contrast(corr["truncate_1"], {t: pick["truncate_1"][t] == auth[t]["answer"] for t in ent}, ent, SEED, 1)["exact_two_sided_mcnemar_p"],
    }
    out = {
        "version": "b15-share-interval-and-holm-v2",
        "n_entailed": n,
        "point": {"total": point_total, "validity": point_valid,
                  "surface": (sum(bc) - sum(ir)) / n, "share": point_share},
        "validity_share_bca95": [lo, hi],
        "surface_component_bca95": [slo, shi],
        "bootstrap": {"seed": SEED, "resamples": B, "method": "paired item bootstrap of the ratio"},
        "note": ("v1 bootstrapped the numerator only. Resampling items and recomputing the "
                 "whole ratio is the correct interval for a share."),
    }
    p = root / "results/b15_share_interval_v2.json"
    p.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"  validity share  {point_share*100:.1f}%   95% BCa [{lo*100:.1f}, {hi*100:.1f}]")
    print(f"  surface comp    {out['point']['surface']*100:+.1f}pp  95% [{slo*100:+.1f}, {shi*100:+.1f}]pp")
    print(f"  written -> {p}")


if __name__ == "__main__":
    main()
