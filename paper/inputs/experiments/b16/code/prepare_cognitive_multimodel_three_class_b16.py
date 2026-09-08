#!/usr/bin/env python3
"""Seal the b16 three-class panel. No model is loaded.

192 items, balanced 64 entailed / 64 contradicted / 64 undetermined, each with a
per-item nonce vocabulary generated after model release, each carrying a
`cc_instruments.closure.certify()` record proving its class. Generation aborts if
any item fails to certify to its intended class.

Unlike b14, the semantic class is NOT encoded in the task id. b14's ids read
`bcf14-prospective-entailed-...`, which meant the answer key could be
reconstructed from the public panel alone -- convenient for reanalysis, but the
authority was not really sealed. Here ids are opaque and the class lives only in
the authority file, which must therefore be preserved in the release package.

Depth is fixed by construction and recorded per item; b14 recorded no depth and
so could not stratify its failures.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from cc_instruments import closure as cl

VERSION = "multimodel-three-class-b16"
DATA = Path("data/cognitive_core/multimodel_three_class_b16")
TASK_SEED = 2026090301
DEPTH = 4                      # rule applications from the seed fact to the query
PER_CLASS = 64
CLASSES = (cl.ENTAILED, cl.CONTRADICTED, cl.UNDETERMINED)
ANSWER = {cl.ENTAILED: "Yes", cl.CONTRADICTED: "No", cl.UNDETERMINED: "Unknown"}
ARMS = ("none", "irrelevant", "conclusion_only", "proof_prefix", "full")

SYSTEM = ("Use only the supplied logical facts, rules, and solver record. "
          "Answer exactly Yes, No, or Unknown.")
BANNED = ("yes", "no", "unknown", "entailed", "contradicted")

_ONSET = ("b", "d", "f", "g", "k", "l", "m", "n", "p", "r", "s", "t", "v", "z",
          "br", "dr", "gl", "kr", "pl", "sn", "tr", "vr", "zl")
_NUCLEUS = ("a", "e", "i", "o", "u", "ae", "ei", "ou")
_CODA = ("", "", "l", "n", "r", "s", "k", "m", "th", "sk", "ft")


def _word(rng: random.Random) -> str:
    return (rng.choice(_ONSET) + rng.choice(_NUCLEUS) + rng.choice(_CODA)
            + rng.choice(_ONSET) + rng.choice(_NUCLEUS) + rng.choice(_CODA))


def _vocabulary(rng: random.Random, n_entities: int, n_predicates: int) -> tuple[list[str], list[str]]:
    seen: set[str] = set()
    out: list[str] = []
    while len(out) < n_entities + n_predicates:
        w = _word(rng)
        if len(w) < 4 or w in seen or w.lower() in BANNED:
            continue
        seen.add(w)
        out.append(w)
    ents = [w.capitalize() for w in out[:n_entities]]
    return ents, out[n_entities:]


def _fact(entity: str, predicate: str, positive: bool = True) -> cl.Atom:
    return (entity, "is", predicate, "+" if positive else "-")


def _rule(p_from: str, p_to: str, positive: bool = True) -> cl.Rule:
    return ((("someone", "is", p_from, "+"),), ("someone", "is", p_to, "+" if positive else "-"))


def _say_fact(a: cl.Atom) -> str:
    return f"{a[0]} is {'' if a[3] == '+' else 'not '}{a[2]}."


def _say_rule(r: cl.Rule) -> str:
    (ant,), con = r
    return f"All {ant[2]} people are {'' if con[3] == '+' else 'not '}{con[2]}."


def _chain_lines(entity: str, preds: Sequence[str], rules: Sequence[cl.Rule],
                 last_positive: bool) -> list[str]:
    """Rendered derivation: fact, then (rule, derived literal) per step."""
    lines = [_say_fact(_fact(entity, preds[0]))]
    for i, r in enumerate(rules):
        positive = last_positive or i < len(rules) - 1
        lines.append(_say_rule(r))
        lines.append(_say_fact(_fact(entity, preds[i + 1], positive)))
    return lines


def _build(index: int, semantic: str, rng: random.Random) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    ents, preds = _vocabulary(rng, 4, DEPTH + 1 + DEPTH + 1 + 2)
    subject, donor, d1, d2 = ents
    chain = preds[: DEPTH + 1]                        # main entity's predicate chain
    donor_chain = preds[DEPTH + 1: 2 * DEPTH + 2]     # donor's parallel chain
    noise = preds[2 * DEPTH + 2:]

    last_positive = semantic != cl.CONTRADICTED
    main_rules = [_rule(chain[i], chain[i + 1], positive=(last_positive or i < DEPTH - 1))
                  for i in range(DEPTH)]
    donor_rules = [_rule(donor_chain[i], donor_chain[i + 1]) for i in range(DEPTH)]

    withheld = None
    kept_main = list(main_rules)
    if semantic == cl.UNDETERMINED:
        withheld = rng.randrange(1, DEPTH)            # never the first rule: keep a visible partial chain
        kept_main = [r for i, r in enumerate(main_rules) if i != withheld]

    facts = [_fact(subject, chain[0]), _fact(donor, donor_chain[0]),
             _fact(d1, noise[0]), _fact(d2, noise[1])]
    rules = kept_main + donor_rules + [_rule(noise[0], noise[1])]
    rng.shuffle(facts)
    rules_shuffled = list(rules)
    rng.shuffle(rules_shuffled)

    query = _fact(subject, chain[DEPTH])
    cert = cl.certify(query, facts, rules_shuffled)
    if cert["verdict"] != semantic:
        raise RuntimeError(f"item {index} intended {semantic} but certified {cert['verdict']}")

    theory = " ".join([_say_fact(f) for f in facts] + [_say_rule(r) for r in rules_shuffled])

    # ---- certificates -------------------------------------------------------
    if semantic == cl.UNDETERMINED:
        depth_reached = withheld                       # steps completed before the break
        prefix = _chain_lines(subject, chain[: depth_reached + 1],
                              main_rules[:depth_reached], True)
        conclusion = ("neither the query nor its negation is derivable from the "
                      "stated rules.")
        full_lines = prefix + [conclusion]
    else:
        allc = _chain_lines(subject, chain, main_rules, last_positive)
        prefix, conclusion = allc[:-1], allc[-1]
        full_lines = allc
    donor_prefix = _chain_lines(donor, donor_chain, donor_rules, True)[: len(prefix)]

    certs = {
        "none": "",
        "irrelevant": "Solver record: " + " ".join(donor_prefix),
        "conclusion_only": "Solver record: " + conclusion,
        "proof_prefix": "Solver record: " + " ".join(prefix),
        "full": "Solver record: " + " ".join(full_lines),
    }
    query_text = f"{subject} is {chain[DEPTH]}."
    prompts = {
        arm: (f"{SYSTEM}\n{theory}\n" + (f"{c}\n" if c else "")
              + f"Query: {query_text} Answer:")
        for arm, c in certs.items()
    }
    for arm, text in prompts.items():
        body = text[len(SYSTEM):].lower()
        for token in BANNED:
            # whole words only: `not` in "is not tarik" must not trip the `no` check,
            # and a nonce word merely containing the letters is not a leak
            if re.search(rf"\b{token}\b", body):
                raise RuntimeError(f"item {index} arm {arm} leaks response token {token!r}")

    task_id = "b16-" + hashlib.sha256(f"{TASK_SEED}:{index}".encode()).hexdigest()[:16]
    public = {"task_id": task_id, "version": VERSION, "depth": DEPTH,
              "n_facts": len(facts), "n_rules": len(rules_shuffled),
              "theory": theory, "query": query_text, "prompts": prompts,
              "entity_mentions": {a: certs[a].count(subject) for a in ARMS}}
    authority = {"task_id": task_id, "answer": ANSWER[semantic],
                 "semantic_class": semantic, "withheld_rule_index": withheld,
                 "certification": cert}
    return public, authority


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Seal the b16 three-class panel (no model calls).")
    ap.add_argument("--project", type=Path, default=Path("."))
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    data = args.project.resolve() / DATA
    if data.exists() and not args.force:
        raise RuntimeError("b16 panel construction is consumed; refusing to overwrite")

    rng = random.Random(TASK_SEED)
    public: list[Mapping[str, Any]] = []
    authority: list[Mapping[str, Any]] = []
    index = 0
    for semantic in CLASSES:
        for _ in range(PER_CLASS):
            p, a = _build(index, semantic, rng)
            public.append(p); authority.append(a); index += 1
    if len({r["task_id"] for r in public}) != len(public):
        raise RuntimeError("task ids are not unique")

    pub_path, auth_path = data / "public/panel.jsonl", data / "sealed/authority.jsonl"
    _write(pub_path, public); _write(auth_path, authority)
    seal = {"version": VERSION, "task_seed": TASK_SEED, "depth": DEPTH,
            "n": len(public), "per_class": PER_CLASS, "classes": list(CLASSES),
            "arms": list(ARMS),
            "public_path": str(DATA / "public/panel.jsonl"),
            "public_sha256": _sha256(pub_path),
            "authority_path": str(DATA / "sealed/authority.jsonl"),
            "authority_sha256": _sha256(auth_path),
            "closure_validation": "results/closure_validation_v1.json"}
    seal["seal_id"] = hashlib.sha256(json.dumps(seal, sort_keys=True).encode()).hexdigest()
    (data / "public/seal.json").write_text(json.dumps(seal, indent=2, sort_keys=True) + "\n",
                                           encoding="utf-8")
    print(json.dumps({"status": "b16_panel_sealed", "n": len(public),
                      "seal_id": seal["seal_id"]}, sort_keys=True))


if __name__ == "__main__":
    main()
