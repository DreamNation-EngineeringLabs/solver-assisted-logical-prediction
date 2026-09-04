#!/usr/bin/env python3
"""Independently audit the sealed b15 panel. No model is loaded.

The point of this script is that it does NOT trust the generator. It re-parses
the rendered English of every theory and every certificate back into logic, then
re-derives each construction invariant from that parse. The convenience fields
the generator wrote (`entity_mentions`, `line_counts`) are checked AGAINST the
independent parse rather than read as truth.

Checks, per item, for all 192:
  1  panel and authority hashes match the seal
  2  theory text re-parses, and re-certifies to the recorded class
  3  every arm's line count, subject-mention count and query-predicate presence,
     recomputed from text, match what the design requires
  4  shape partners agree exactly (broken_chain/same_entity/shuffled -> truncate_1,
     misleading -> full)
  5  broken_chain's shown lines leave the query undetermined
  6  every rule shown in every arm is a real theory rule, EXCEPT exactly one
     fabricated polarity-flipping rule in `misleading`
  7  shuffled is a permutation of truncate_1
  8  no arm leaks a response token
Stdlib plus cc_instruments.closure.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

from cc_instruments import closure as cl

VERSION = "binary-certificate-factorial-b15-audit-v1"
DATA = Path("data/cognitive_core/binary_certificate_factorial_b15")
ARMS = ("none", "irrelevant", "same_entity_irrelevant", "truncate_3", "truncate_2",
        "truncate_1", "broken_chain", "misleading", "shuffled", "full")
PARTNERS = {"broken_chain": "truncate_1", "same_entity_irrelevant": "truncate_1",
            "shuffled": "truncate_1", "misleading": "full"}
EXPECTED_LINES = {"none": 0, "irrelevant": 8, "same_entity_irrelevant": 8, "truncate_3": 4,
                  "truncate_2": 6, "truncate_1": 8, "broken_chain": 8, "misleading": 9,
                  "shuffled": 8, "full": 9}
QUERY_PREDICATE_REQUIRED = {"truncate_1": True, "broken_chain": True, "misleading": True,
                            "shuffled": True, "full": True, "irrelevant": False,
                            "same_entity_irrelevant": False, "truncate_2": False,
                            "truncate_3": False}
BANNED = ("yes", "no", "unknown", "entailed", "contradicted")

FACT_RE = re.compile(r"^(\w+) is (not )?(\w+)$")
RULE_RE = re.compile(r"^All (\w+) people are (not )?(\w+)$")


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in text.split(".") if s.strip()]


def _parse(text: str) -> tuple[list[cl.Atom], list[cl.Rule], list[str]]:
    """Rendered English -> (facts, rules, unparsed). Independent of the generator."""
    facts: list[cl.Atom] = []
    rules: list[cl.Rule] = []
    bad: list[str] = []
    for s in _sentences(text):
        m = RULE_RE.match(s)
        if m:
            a, neg, b = m.groups()
            rules.append(((("someone", "is", a, "+"),), ("someone", "is", b, "-" if neg else "+")))
            continue
        m = FACT_RE.match(s)
        if m:
            e, neg, p = m.groups()
            facts.append((e, "is", p, "-" if neg else "+"))
            continue
        bad.append(s)
    return facts, rules, bad


def _certificate(prompt: str) -> str:
    if "Solver record: " not in prompt:
        return ""
    return prompt.split("Solver record: ", 1)[1].split("\nQuery", 1)[0]


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description="Audit the sealed b15 panel without model calls.")
    ap.add_argument("--project", type=Path, default=Path("."))
    args = ap.parse_args()
    root = args.project.resolve() / DATA
    seal = json.loads((root / "public/seal.json").read_text(encoding="utf-8"))

    pub_path = args.project.resolve() / seal["public_path"]
    auth_path = args.project.resolve() / seal["authority_path"]
    failures: list[str] = []

    def check(cond: bool, msg: str) -> None:
        if not cond:
            failures.append(msg)

    check(_sha256(pub_path) == seal["public_sha256"], "public panel hash mismatch")
    check(_sha256(auth_path) == seal["authority_sha256"], "authority hash mismatch")

    pub = [json.loads(l) for l in pub_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    aut = {r["task_id"]: r for r in
           (json.loads(l) for l in auth_path.read_text(encoding="utf-8").splitlines() if l.strip())}
    check(len(pub) == seal["n"], f"panel has {len(pub)} rows, seal says {seal['n']}")
    check(set(aut) == {r["task_id"] for r in pub}, "authority does not cover the panel exactly")
    check(collections.Counter(a["semantic_class"] for a in aut.values())
          == {"entailed": 96, "contradicted": 96}, "class balance is not 96/96")

    # ---- qualification panel (recorded smoke check, not a gate) -------------
    qpub_path = args.project.resolve() / seal["qualification_public_path"]
    check(_sha256(qpub_path) == seal["qualification_public_sha256"],
          "qualification panel hash mismatch")
    qpub = [json.loads(l) for l in qpub_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    qauth = {r["task_id"]: r for r in (json.loads(l) for l in
             (root / "sealed/qualification-authority.jsonl").read_text(encoding="utf-8").splitlines() if l.strip())}
    check(len(qpub) == seal["qualification_n"], f"qualification has {len(qpub)} items")
    check(collections.Counter(v["answer"] for v in qauth.values()) == {"Yes": 18, "No": 18},
          "qualification is not balanced 18/18")
    for row in qpub:
        subject, predicate = row["query"].split(" is ")[0], row["query"].split(" is ")[1].rstrip(".")
        direct, reordered = row["prompts"]["direct"], row["prompts"]["reordered"]
        fd, rd, bd = _parse(direct.split("\n")[1])
        fr, _, _ = _parse(reordered.split("\n")[1])
        check(not rd and not bd, f"{row['task_id']}: qualification item is not depth-0")
        check(sorted(fd) == sorted(fr),
              f"{row['task_id']}: reordered template is not a permutation of direct")
        stated = [x for x in fd if x[0] == subject and x[2] == predicate]
        check(len(stated) == 1, f"{row['task_id']}: queried fact not stated exactly once")
        if stated:
            expected = "Yes" if stated[0][3] == "+" else "No"
            check(qauth[row["task_id"]]["answer"] == expected,
                  f"{row['task_id']}: qualification answer contradicts the stated fact")

    stats: collections.Counter = collections.Counter()
    for row in pub:
        tid = row["task_id"]
        a = aut[tid]
        subject, predicate = row["query"].split(" is ")[0], row["query"].split(" is ")[1].rstrip(".")
        query = (subject, "is", predicate, "+")

        # (2) re-parse the theory and re-certify independently of the generator
        facts, rules, bad = _parse(row["theory"])
        check(not bad, f"{tid}: theory has unparsed sentences {bad[:2]}")
        cert = cl.certify(query, facts, rules)
        check(cert["verdict"] == a["semantic_class"],
              f"{tid}: theory re-certifies as {cert['verdict']}, authority says {a['semantic_class']}")
        check(a["answer"] == ("Yes" if a["semantic_class"] == "entailed" else "No"),
              f"{tid}: answer does not match class")
        theory_rules = set(rules)

        parsed: dict[str, tuple[list[cl.Atom], list[cl.Rule]]] = {}
        for arm in ARMS:
            text = _certificate(row["prompts"][arm])
            f, r, b = _parse(text)
            check(not b, f"{tid}/{arm}: unparsed certificate sentences {b[:2]}")
            parsed[arm] = (f, r)
            n_lines = len(_sentences(text))

            # (3) recomputed from text, never from the generator's metadata
            check(n_lines == EXPECTED_LINES[arm],
                  f"{tid}/{arm}: {n_lines} lines, expected {EXPECTED_LINES[arm]}")
            check(n_lines == row["line_counts"][arm],
                  f"{tid}/{arm}: recomputed lines disagree with recorded metadata")
            mentions = sum(1 for x in f if x[0] == subject)
            check(mentions == row["entity_mentions"][arm],
                  f"{tid}/{arm}: recomputed subject mentions disagree with metadata")
            if arm != "none":
                has_pred = any(predicate in (x[2],) for x in f) or any(
                    predicate in (rr[1][2], rr[0][0][2]) for rr in r)
                check(has_pred == QUERY_PREDICATE_REQUIRED[arm],
                      f"{tid}/{arm}: query predicate present={has_pred}, "
                      f"expected {QUERY_PREDICATE_REQUIRED[arm]}")

            # (6) fabricated rules
            foreign = [rr for rr in r if rr not in theory_rules]
            if arm == "misleading":
                check(len(foreign) == 1, f"{tid}/misleading: {len(foreign)} fabricated rules, expected 1")
                # the flip is relative to the item's own truth, not absolute: an
                # entailed item's true final rule is positive so the fabrication is
                # negative, and a contradicted item's is the reverse.
                if foreign:
                    want = "-" if a["semantic_class"] == "entailed" else "+"
                    check(foreign[0][1][3] == want,
                          f"{tid}/misleading: fabricated rule polarity {foreign[0][1][3]}, expected {want}")
            else:
                check(not foreign, f"{tid}/{arm}: {len(foreign)} rules are not in the theory")

            # (8) response-token leak
            for token in BANNED:
                check(not re.search(rf"\b{token}\b", text.lower()),
                      f"{tid}/{arm}: leaks response token {token!r}")

        # (4) shape partners
        for arm, partner in PARTNERS.items():
            fa, _ = parsed[arm]
            fp, _ = parsed[partner]
            check(len(_sentences(_certificate(row["prompts"][arm])))
                  == len(_sentences(_certificate(row["prompts"][partner]))),
                  f"{tid}: {arm} line count != {partner}")
            check(sum(1 for x in fa if x[0] == subject) == sum(1 for x in fp if x[0] == subject),
                  f"{tid}: {arm} subject mentions != {partner}")

        # (5) broken_chain must not settle the query
        bf, br = parsed["broken_chain"]
        bc = cl.certify(query, bf, br)
        check(bc["verdict"] == cl.UNDETERMINED,
              f"{tid}: broken_chain lines settle the query as {bc['verdict']}")

        # (7) shuffled is a permutation of truncate_1
        check(sorted(_sentences(_certificate(row["prompts"]["shuffled"])))
              == sorted(_sentences(_certificate(row["prompts"]["truncate_1"]))),
              f"{tid}: shuffled is not a permutation of truncate_1")
        stats[a["semantic_class"]] += 1

    result = {"version": VERSION, "n": len(pub), "classes": dict(stats),
              "qualification_n": len(qpub),
              "seal_id": seal["seal_id"], "failures": failures[:40],
              "failure_count": len(failures),
              "status": "b15_audit_passed" if not failures else "b15_audit_FAILED"}
    print(json.dumps(result, indent=2, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
