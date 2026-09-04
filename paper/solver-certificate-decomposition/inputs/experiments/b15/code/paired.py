"""Paired binary-outcome analysis: exact McNemar, seeded BCa, Holm.

Matches the analysis plan used across the b-series: complete 2x2 paired table,
exact two-sided McNemar as the decision criterion, and a seeded 100,000-resample
paired BCa interval. Stdlib only.
"""
from __future__ import annotations

import math
import random
from statistics import NormalDist
from typing import Mapping, Sequence

_NORM = NormalDist()
DEFAULT_RESAMPLES = 100_000


def exact_mcnemar(left_only: int, right_only: int) -> float:
    """Exact two-sided McNemar. Only discordant pairs carry information."""
    d = left_only + right_only
    if d == 0:
        return 1.0
    tail = sum(math.comb(d, k) for k in range(min(left_only, right_only) + 1))
    return min(1.0, 2.0 * tail / (2 ** d))


def paired_table(left: Mapping[str, bool], right: Mapping[str, bool],
                 ids: Sequence[str]) -> Mapping[str, int]:
    both = lo = ro = neither = 0
    for t in ids:
        l, r = left[t], right[t]
        if l and r: both += 1
        elif l: lo += 1
        elif r: ro += 1
        else: neither += 1
    return {"both_correct": both, "left_only_correct": lo,
            "right_only_correct": ro, "neither_correct": neither}


def bca(diffs: Sequence[int], seed: int, resamples: int = DEFAULT_RESAMPLES) -> tuple[float, float]:
    """Seeded BCa interval for the mean of per-item differences in {-1,0,1}.

    Resampling is done as a multinomial over the three outcome counts, which is
    equivalent to resampling items and far cheaper.
    """
    rng = random.Random(seed)
    n = len(diffs)
    theta = sum(diffs) / n
    p_plus, p_minus = diffs.count(1) / n, diffs.count(-1) / n
    reps: list[float] = []
    for _ in range(resamples):
        plus = rng.binomialvariate(n, p_plus)
        rest = n - plus
        minus = rng.binomialvariate(rest, p_minus / (1 - p_plus)) if rest and p_plus < 1 else 0
        reps.append((plus - minus) / n)
    reps.sort()
    below = sum(1 for r in reps if r < theta) / len(reps)
    if below <= 0 or below >= 1:                       # degenerate; fall back to percentile
        return reps[int(0.025 * (len(reps) - 1))], reps[int(0.975 * (len(reps) - 1))]
    z0 = _NORM.inv_cdf(below)
    jack = [(n * theta - d) / (n - 1) for d in diffs]
    jbar = sum(jack) / n
    den = 6.0 * (sum((jbar - j) ** 2 for j in jack) ** 1.5)
    a = (sum((jbar - j) ** 3 for j in jack) / den) if den else 0.0
    out: list[float] = []
    for q in (0.025, 0.975):
        z = _NORM.inv_cdf(q)
        adj = z0 + (z0 + z) / (1 - a * (z0 + z))
        idx = min(max(int(_NORM.cdf(adj) * (len(reps) - 1)), 0), len(reps) - 1)
        out.append(reps[idx])
    return out[0], out[1]


def contrast(left: Mapping[str, bool], right: Mapping[str, bool], ids: Sequence[str],
             seed: int, resamples: int = DEFAULT_RESAMPLES) -> Mapping[str, object]:
    tab = paired_table(left, right, ids)
    diffs = [1 if left[t] and not right[t] else -1 if right[t] and not left[t] else 0 for t in ids]
    lo_, hi_ = bca(diffs, seed, resamples)
    return {
        "paired_table": tab,
        "left_correct": tab["both_correct"] + tab["left_only_correct"],
        "right_correct": tab["both_correct"] + tab["right_only_correct"],
        "paired_risk_difference": (tab["left_only_correct"] - tab["right_only_correct"]) / len(ids),
        "exact_two_sided_mcnemar_p": exact_mcnemar(tab["left_only_correct"], tab["right_only_correct"]),
        "bca_95": [lo_, hi_],
    }


def holm(pvals: Mapping[str, float]) -> Mapping[str, float]:
    """Holm step-down adjustment within a declared family."""
    ordered = sorted(pvals.items(), key=lambda kv: kv[1])
    m, out, running = len(ordered), {}, 0.0
    for i, (k, p) in enumerate(ordered):
        running = max(running, min(1.0, (m - i) * p))
        out[k] = running
    return out
