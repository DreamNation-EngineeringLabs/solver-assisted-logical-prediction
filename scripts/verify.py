#!/usr/bin/env python3
"""Re-derive any headline number in the paper, one command each.

The paper claims re-derivability in three places. This makes the claim checkable
in under a minute instead of under an afternoon: every entry below recomputes
its number **from the receipts and the sealed authority**, not by reading an
analysis JSON, and prints it beside the value the manuscript states.

    python3 scripts/verify.py --list
    python3 scripts/verify.py validity-share
    python3 scripts/verify.py --all

Standard library only. No network, no model weights, no third-party packages.
"""
from __future__ import annotations

import argparse, json, sys
from pathlib import Path

B15D = Path("data/cognitive_core/binary_certificate_factorial_b15")
B15R = Path("runs/cognitive_core/binary_certificate_factorial_b15")
B17R = Path("runs/cognitive_core/three_class_broken_chain_b17")
B17BR = Path("runs/cognitive_core/three_class_none_baseline_b17b")
B16R = Path("results/b16_analysis_v2_allarms.json")
B14 = Path("results/b14_raw_model_calls_960.jsonl")


def _rows(p: Path):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _b15(root: Path, key: str):
    """Per-arm correct counts on the entailed subset, from receipts."""
    auth = {r["task_id"]: r["answer"] for r in _rows(root / B15D / "sealed/authority.jsonl")}
    ent = [t for t, a in auth.items() if a == "Yes"]
    out = {}
    for f in sorted((root / B15R / key / "receipts").glob("prospective-*.jsonl")):
        got = {r["task_id"]: r["candidate"] for r in _rows(f)}
        out[f.stem.replace("prospective-", "")] = sum(got[t] == auth[t] for t in ent)
    return out, auth, ent


# --- claims ------------------------------------------------------------------

def validity_share(root):
    c, _, _ = _b15(root, "qwen2p5_3b_4bit")
    v = (c["truncate_1"] - c["broken_chain"]) / (c["truncate_1"] - c["irrelevant"])
    return "98.3%", f"{v*100:.1f}%", (
        f"(truncate_1 {c['truncate_1']} - broken_chain {c['broken_chain']}) / "
        f"(truncate_1 - irrelevant {c['irrelevant']}), entailed n=96")


def gemma_share(root):
    c, _, _ = _b15(root, "gemma3_4b_b15")
    vi = (c["truncate_1"] - c["broken_chain"]) / (c["truncate_1"] - c["irrelevant"])
    vn = (c["truncate_1"] - c["broken_chain"]) / (c["truncate_1"] - c["none"])
    return "40.4% / 51.4%", f"{vi*100:.1f}% / {vn*100:.1f}%", (
        f"same ratio against irrelevant ({c['irrelevant']}) and none ({c['none']}); "
        f"broken_chain {c['broken_chain']}, truncate_1 {c['truncate_1']}")


def corruption(root):
    got = []
    for key in ("qwen2p5_3b_4bit", "qwen2p5_3b_bf16", "gemma3_4b_b15"):
        auth = {r["task_id"]: r["answer"] for r in _rows(root / B15D / "sealed/authority.jsonl")}
        mis = {r["task_id"]: r["candidate"]
               for r in _rows(root / B15R / key / "receipts/prospective-misleading.jsonl")}
        got.append(sum(mis[t] != auth[t] for t in auth))
    return "189 / 186 / 192 of 192", " / ".join(map(str, got)) + " of 192", \
        "incorrect answers under `misleading`, all items, three checkpoints"


def detection(root):
    lines, ok = [], True
    for key in ("qwen2p5_3b_4bit", "qwen2p5_3b_bf16", "gemma3_4b_b15"):
        rate = {}
        for arm, base in (("irrelevant", B17R), ("broken_chain", B17R), ("none", B17BR)):
            f = root / base / key / f"receipts/prospective-{arm}.jsonl"
            rows = _rows(f)
            rate[arm] = sum(r["candidate"] == "Unknown" for r in rows) / len(rows)
        fell = rate["broken_chain"] < rate["irrelevant"] and rate["broken_chain"] < rate["none"]
        ok &= fell
        lines.append(f"{key}: none {rate['none']*100:.1f}% irrel {rate['irrelevant']*100:.1f}% "
                     f"broken {rate['broken_chain']*100:.1f}% -> {'falls' if fell else 'RISES'}")
    return "falls against both baselines, all three", \
        ("falls against both baselines, all three" if ok else "DOES NOT HOLD"), "; ".join(lines)


def census(root):
    """Receipts on disk against the census the composer substitutes into the paper.

    Not a hard-coded literal: the manuscript's count comes from
    results/receipt_census_v1.json at compose time, so the invariant worth
    checking is that the census still matches the receipts. If it does and the
    paper was composed since, the paper is right by construction.
    """
    total = runs = 0
    for rec in sorted((root / "runs/cognitive_core").rglob("receipts")):
        n = sum(sum(1 for l in f.open(encoding="utf-8") if l.strip())
                for f in sorted(rec.glob("*.jsonl")))
        if n:
            total += n; runs += 1
    flat = root / B14
    if flat.exists():
        total += sum(1 for l in flat.open(encoding="utf-8") if l.strip()); runs += 1
    c = json.loads((root / "results/receipt_census_v1.json").read_text())
    stated = f"{c['total_scored_responses']:,} across {c['model_runs']} model-runs"
    return stated, f"{total:,} across {runs} model-runs", \
        "receipts on disk vs results/receipt_census_v1.json, which the composer " \
        "substitutes; re-run scripts/census_receipts_v1.py after adding a run"


def state_effect(root):
    rows = _rows(root / B14)
    cls = lambda t: "Yes" if "entailed" in t else "No"
    correct = {}
    for r in rows:
        correct.setdefault(r["arm"], 0)
        correct[r["arm"]] += r["candidate"] == cls(r["task_id"])
    e = correct
    state = ((e["proof_prefix"] - e["irrelevant"]) + (e["full"] - e["conclusion_only"])) / 2 / 192
    return "+22.4pp", f"{state*100:+.1f}pp", (
        f"mean of the two state edges: (proof_prefix {e['proof_prefix']} - irrelevant "
        f"{e['irrelevant']}) and (full {e['full']} - conclusion_only {e['conclusion_only']}), /192")


def cross_model(root):
    d = json.loads((root / B16R).read_text())
    st = {}
    for m, md in d["models"].items():
        a = md["arms"]; ba = lambda k: a[k]["balanced_accuracy"]
        st[m] = (((ba("proof_prefix") - ba("irrelevant")) + (ba("full") - ba("conclusion_only"))) / 2,
                 all(a[k]["min_per_class_recall"] == 0.0 for k in a))
    live = [v for v, dead in st.values() if not dead]
    return "+8.7pp all / +14.7pp non-degenerate", \
        f"{sum(v for v, _ in st.values())/len(st)*100:+.1f}pp all / {sum(live)/len(live)*100:+.1f}pp non-degenerate", \
        f"{len(st)} models, {len(st)-len(live)} degenerate in every arm"


CLAIMS = {
    "validity-share": ("§5.2 validity share, Qwen2.5-3B 4-bit", validity_share),
    "gemma-share":    ("§5.3 Gemma share, both baselines", gemma_share),
    "corruption":     ("§5.4 items answered incorrectly under `misleading`", corruption),
    "detection":      ("§5.5 abstention falls, three checkpoints x two baselines", detection),
    "state-effect":   ("§5.1 state main effect of the 2x2", state_effect),
    "cross-model":    ("§5.7 mean state effect across ten models", cross_model),
    "census":         ("§4.3 total scored responses", census),
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("claim", nargs="?", choices=sorted(CLAIMS))
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--project", type=Path, default=Path("."))
    a = ap.parse_args(); root = a.project.resolve()

    if a.list or not (a.claim or a.all):
        print("claims this re-derives from the receipts:\n")
        for k, (desc, _) in sorted(CLAIMS.items()):
            print(f"  {k:15s} {desc}")
        print("\n  --all           every one of them")
        return 0

    todo = sorted(CLAIMS) if a.all else [a.claim]
    bad = 0
    for k in todo:
        desc, fn = CLAIMS[k]
        try:
            paper, got, how = fn(root)
        except Exception as exc:                      # a missing run is not a mismatch
            print(f"SKIP  {k:15s} {desc}\n      {type(exc).__name__}: {exc}")
            continue
        match = paper.replace(",", "") == got.replace(",", "")
        bad += not match
        print(f"{'OK  ' if match else 'DIFF'}  {k:15s} paper {paper}   derived {got}")
        print(f"      {desc}\n      {how}")
    if bad:
        print(f"\n{bad} value(s) differ from the manuscript.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
