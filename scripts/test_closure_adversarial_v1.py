#!/usr/bin/env python3
"""Adversarial and differential tests for the forward-closure certifier.

Peer review observed, correctly, that agreeing with ProofWriter's OWA labels at
23,240/23,240 is a weaker check than "independent" implies: those labels are
themselves produced by forward chaining over the same fragment, so the agreement
partly measures "my chainer agrees with their chainer". It catches coding bugs;
it does not probe the failure modes that matter, and it offers no coverage at all
of the *generated nonce theories* where the certifier is actually used.

Two things here.

1. Hand-constructed adversarial theories with failure modes ProofWriter cannot
   exercise: cyclic rules, antecedents satisfiable only beyond the round cap,
   theories deriving an atom and its negation, unbound consequents, and queries
   over predicates absent from the theory.

2. A DIFFERENTIAL test on the generated panels. An independent reference
   implementation — exhaustive ground instantiation over the Herbrand base with a
   naive fixpoint, a deliberately different algorithm from the bindings-driven
   chainer — classifies every item, and the two must agree. This is the coverage
   ProofWriter does not provide.
"""
from __future__ import annotations
import argparse, itertools, json
from pathlib import Path
from cc_instruments import closure as cl

VERSION = "closure-adversarial-and-differential-v1"


# ---------------------------------------------------------------- reference
def reference_closure(facts, rules):
    """Independent implementation: ground every rule over every constant, then
    iterate to a fixpoint. Deliberately naive and structurally different from
    cc_instruments.closure, which drives from bindings per antecedent."""
    consts = {a[0] for a in facts} | {a[2] for a in facts}
    for ants, con in rules:
        for at in list(ants) + [con]:
            for part in (at[0], at[2]):
                if part not in cl.VARIABLES:
                    consts.add(part)
    known = set(facts)
    for _ in range(256):
        new = set(known)
        for ants, con in rules:
            varnames = sorted({p for at in list(ants) + [con] for p in (at[0], at[2]) if p in cl.VARIABLES})
            for combo in itertools.product(sorted(consts), repeat=len(varnames)):
                sub = dict(zip(varnames, combo))
                g = [tuple(sub.get(x, x) for x in at) for at in ants]
                if all(tuple(x) in known for x in g):
                    new.add(tuple(sub.get(x, x) for x in con))
        if new == known:
            return known
        known = new
    raise RuntimeError("reference did not reach a fixpoint")


def ref_classify(query, facts, rules):
    k = reference_closure(facts, rules)
    if any(a[3] == "+" and cl.negate(a) in k for a in k):
        return "inconsistent"
    if query in k: return cl.ENTAILED
    if cl.negate(query) in k: return cl.CONTRADICTED
    return cl.UNDETERMINED


# ---------------------------------------------------------------- adversarial
def A(e, p, pol="+"): return (e, "is", p, pol)
def R(a, b, pol="+"): return ((("someone", "is", a, "+"),), ("someone", "is", b, pol))

CASES = [
    ("cyclic rules must still saturate",
     [A("x", "p")], [R("p", "q"), R("q", "p")], A("x", "q"), cl.ENTAILED),
    ("cycle that never reaches the query",
     [A("x", "p")], [R("p", "q"), R("q", "p")], A("x", "z"), cl.UNDETERMINED),
    ("chain longer than the default round cap is still reached",
     [A("x", "p0")], [R(f"p{i}", f"p{i+1}") for i in range(40)], A("x", "p40"), cl.ENTAILED),
    ("negation derived, query positive",
     [A("x", "p")], [R("p", "q", "-")], A("x", "q"), cl.CONTRADICTED),
    ("predicate absent from the theory entirely",
     [A("x", "p")], [R("p", "q")], A("x", "absent"), cl.UNDETERMINED),
    ("query about an entity absent from the theory",
     [A("x", "p")], [R("p", "q")], A("nobody", "q"), cl.UNDETERMINED),
    ("rule fires only for the entity that satisfies it",
     [A("x", "p"), A("y", "r")], [R("p", "q")], A("y", "q"), cl.UNDETERMINED),
]

INCONSISTENT = ("theory deriving an atom and its negation is rejected, not labelled",
                [A("x", "p")], [R("p", "q"), R("p", "q", "-")])


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--project", type=Path, default=Path("."))
    a = ap.parse_args(); root = a.project.resolve()
    report = {"version": VERSION, "adversarial": [], "differential": {}}
    ok = True

    print("adversarial cases:")
    for name, facts, rules, q, want in CASES:
        got = cl.classify(q, cl.saturate(facts, rules, max_rounds=128))
        ref = ref_classify(q, facts, rules)
        good = got == want == ref
        ok &= good
        print(f"  {'OK ' if good else 'FAIL'} {name}  (certifier={got}, reference={ref}, expected={want})")
        report["adversarial"].append({"case": name, "certifier": got, "reference": ref,
                                      "expected": want, "pass": good})

    name, facts, rules = INCONSISTENT
    c = cl.saturate(facts, rules)
    good = (not c.consistent) and len(c.conflicts) > 0
    ok &= good
    print(f"  {'OK ' if good else 'FAIL'} {name}  (consistent={c.consistent}, conflicts={len(c.conflicts)})")
    report["adversarial"].append({"case": name, "consistent": c.consistent,
                                  "conflicts": len(c.conflicts), "pass": good})

    # cap behaviour must be loud, never silent
    c = cl.saturate([A("x", "p0")], [R(f"p{i}", f"p{i+1}") for i in range(40)], max_rounds=3)
    good = not c.saturated
    ok &= good
    print(f"  {'OK ' if good else 'FAIL'} exceeding the round cap reports saturated=False rather than a wrong answer")
    report["adversarial"].append({"case": "round cap is loud", "saturated": c.saturated, "pass": good})

    # ---------------- differential test on the GENERATED panels --------------
    print("\ndifferential test against an independent implementation, on the generated panels:")
    for panel, auth_path in (("binary_certificate_factorial_b15", "sealed/authority.jsonl"),
                             ("multimodel_three_class_b16", "sealed/authority.jsonl")):
        ap_ = root / f"data/cognitive_core/{panel}/{auth_path}"
        if not ap_.exists(): continue
        rows = [json.loads(l) for l in ap_.read_text().splitlines() if l.strip()]
        agree = total = 0
        for r in rows:
            cert = r["certification"]
            facts = [tuple(x) for x in cert.get("_facts", [])] if "_facts" in cert else None
            if facts is None:
                total = -1; break     # authority does not carry the theory; see note
            total += 1
        if total == -1:
            # reconstruct from the public panel's rendered theory instead
            pub = root / f"data/cognitive_core/{panel}/public/panel.jsonl"
            import re
            FACT = re.compile(r"^(\w+) is (not )?(\w+)$"); RULE = re.compile(r"^All (\w+) people are (not )?(\w+)$")
            byid = {json.loads(l)["task_id"]: json.loads(l) for l in pub.read_text().splitlines() if l.strip()}
            agree = total = 0
            for r in rows:
                row = byid[r["task_id"]]
                facts, rules = [], []
                for s in [x.strip() for x in row["theory"].split(".") if x.strip()]:
                    m = RULE.match(s)
                    if m:
                        x, neg, y = m.groups(); rules.append(R(x, y, "-" if neg else "+")); continue
                    m = FACT.match(s)
                    if m:
                        e, neg, p = m.groups(); facts.append(A(e, p, "-" if neg else "+"))
                subj, pred = row["query"].split(" is ")[0], row["query"].split(" is ")[1].rstrip(".")
                q = A(subj, pred)
                got = cl.classify(q, cl.saturate(facts, rules))
                ref = ref_classify(q, facts, rules)
                total += 1; agree += (got == ref == r["certification"]["verdict"])
        rate = agree / total if total else 0
        ok &= (agree == total)
        print(f"  {'OK ' if agree==total else 'FAIL'} {panel}: {agree}/{total} three-way agreement "
              f"(certifier = independent reference = sealed authority)")
        report["differential"][panel] = {"agree": agree, "total": total, "rate": rate}

    report["all_passed"] = ok
    out = root / "results/closure_adversarial_v1.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"\n  all passed: {ok}\n  written -> {out}")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
