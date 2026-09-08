"""Signal detection measures.

Accuracy on a balanced panel conflates discriminative sensitivity with response
bias. The b14 receipts are the worked example: the `irrelevant` arm scored 96/192
(50.0%, indistinguishable from chance by accuracy alone) while returning an
identical 9/96 Yes-rate in both classes, i.e. d' of exactly zero. Always report
d' and criterion alongside accuracy.
"""
from __future__ import annotations

from statistics import NormalDist
from typing import Mapping, Sequence

_NORM = NormalDist()


def _loglinear(count: int, n: int) -> float:
    """(x+0.5)/(n+1) correction so that 0/n and n/n rates stay finite."""
    return (count + 0.5) / (n + 1)


def rates(hits: int, n_signal: int, false_alarms: int, n_noise: int) -> tuple[float, float]:
    return _loglinear(hits, n_signal), _loglinear(false_alarms, n_noise)


def d_prime(hits: int, n_signal: int, false_alarms: int, n_noise: int) -> float:
    h, f = rates(hits, n_signal, false_alarms, n_noise)
    return _NORM.inv_cdf(h) - _NORM.inv_cdf(f)


def criterion(hits: int, n_signal: int, false_alarms: int, n_noise: int) -> float:
    """Positive c means bias toward the NOISE response (here: toward `No`)."""
    h, f = rates(hits, n_signal, false_alarms, n_noise)
    return -0.5 * (_NORM.inv_cdf(h) + _NORM.inv_cdf(f))


def summarise(responses: Mapping[str, str], truth: Mapping[str, str],
              signal_label: str = "Yes") -> Mapping[str, float | int]:
    """One arm's full signal-detection summary.

    `responses` and `truth` are task_id -> label. Items whose truth is
    `signal_label` are signal trials; all others are noise trials.
    """
    sig = [t for t, a in truth.items() if a == signal_label]
    noi = [t for t, a in truth.items() if a != signal_label]
    if not sig or not noi:
        raise ValueError("need both signal and noise trials to compute d'")
    hits = sum(1 for t in sig if responses[t] == signal_label)
    fas = sum(1 for t in noi if responses[t] == signal_label)
    n = len(truth)
    return {
        "hits": hits, "n_signal": len(sig),
        "false_alarms": fas, "n_noise": len(noi),
        "hit_rate": hits / len(sig), "false_alarm_rate": fas / len(noi),
        "d_prime": d_prime(hits, len(sig), fas, len(noi)),
        "criterion_c": criterion(hits, len(sig), fas, len(noi)),
        "accuracy": sum(1 for t in truth if responses[t] == truth[t]) / n,
        "signal_response_rate": sum(1 for t in truth if responses[t] == signal_label) / n,
    }


def majority_baseline(truth: Mapping[str, str]) -> Mapping[str, float | int | str]:
    """The trivial always-one-label strategy, for comparison against any arm."""
    counts: dict[str, int] = {}
    for a in truth.values():
        counts[a] = counts.get(a, 0) + 1
    label = max(counts, key=lambda k: counts[k])
    return {"label": label, "correct": counts[label], "accuracy": counts[label] / len(truth),
            "d_prime": 0.0}
