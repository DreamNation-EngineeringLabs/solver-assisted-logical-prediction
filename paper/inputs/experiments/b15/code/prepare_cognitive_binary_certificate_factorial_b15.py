#!/usr/bin/env python3
"""Seal the b15 nine-arm mechanism panel (plus a `full` comparability anchor).

b15 asks how much of b14's proof-state effect is tracking of logical VALIDITY
and how much is surface overlap between certificate and query. It does that by
holding surface form fixed and destroying validity alone.

Deviation from the design doc, made before any data exists and recorded here:
a tenth arm, `full`, is included. The doc listed nine and named `truncate_1` the
upper anchor, but b14 showed `full` (99.5%) well above `proof_prefix` (87.0%),
so without it b15 has no within-experiment ceiling and no way to check that this
fresh panel is of comparable difficulty to b14's. It costs 192 prompts.

Self-contained by design. The b16 generator has its own copy of the vocabulary
machinery: that script is frozen against a live seal and must stay byte-identical
to what produced it, and independent auditability of each sealed script is worth
more here than removing the duplication.

No model is loaded.
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

VERSION = "binary-certificate-factorial-b15"
DATA = Path("data/cognitive_core/binary_certificate_factorial_b15")
TASK_SEED = 2026090315
QUAL_SEED = 2026090316      # separate stream: keeps the prospective panel bit-identical
QUAL_N = 36                 # 18 Yes + 18 No, direct facts, two templates
DEPTH = 4
PER_CLASS = 96                       # 96 entailed + 96 contradicted = 192
ARMS = ("none", "irrelevant", "same_entity_irrelevant", "truncate_3", "truncate_2",
        "truncate_1", "broken_chain", "misleading", "shuffled", "full")
SYSTEM = ("Use only the supplied logical facts, rules, and solver record. "
          "Answer exactly Yes or No.")
BANNED = ("yes", "no", "unknown", "entailed", "contradicted")

_ONSET = ("b", "d", "f", "g", "k", "l", "m", "n", "p", "r", "s", "t", "v", "z",
          "br", "dr", "gl", "kr", "pl", "sn", "tr", "vr", "zl")
_NUCLEUS = ("a", "e", "i", "o", "u", "ae", "ei", "ou")
_CODA = ("", "", "l", "n", "r", "s", "k", "m", "th", "sk", "ft")


def _word(rng: random.Random) -> str:
    return (rng.choice(_ONSET) + rng.choice(_NUCLEUS) + rng.choice(_CODA)
            + rng.choice(_ONSET) + rng.choice(_NUCLEUS) + rng.choice(_CODA))


def _vocabulary(rng: random.Random, n_ent: int, n_pred: int) -> tuple[list[str], list[str]]:
    seen: set[str] = set()
    out: list[str] = []
    while len(out) < n_ent + n_pred:
        w = _word(rng)
        if len(w) < 4 or w in seen or w.lower() in BANNED:
            continue
        seen.add(w); out.append(w)
    return [w.capitalize() for w in out[:n_ent]], out[n_ent:]


def _fact(e: str, p: str, positive: bool = True) -> cl.Atom:
    return (e, "is", p, "+" if positive else "-")


def _rule(a: str, b: str, positive: bool = True) -> cl.Rule:
    return ((("someone", "is", a, "+"),), ("someone", "is", b, "+" if positive else "-"))


def _say_fact(a: cl.Atom) -> str:
    return f"{a[0]} is {'' if a[3] == '+' else 'not '}{a[2]}."


def _say_rule(r: cl.Rule) -> str:
    (ant,), con = r
    return f"All {ant[2]} people are {'' if con[3] == '+' else 'not '}{con[2]}."


def _ladder(entity: str, preds: Sequence[str], rules: Sequence[cl.Rule],
            steps: int, trailing_rule: bool, last_positive: bool = True) -> list[str]:
    """fact, then `steps` complete (rule, derived) pairs, then optionally the next rule.

    `truncate_k` = ladder(steps=DEPTH-k, trailing_rule=True): b14's proof_prefix
    shape, which ends on a rule and withholds the literal that rule would license.
    """
    lines = [_say_fact(_fact(entity, preds[0]))]
    for i in range(steps):
        positive = last_positive or i < len(rules) - 1
        lines.append(_say_rule(rules[i]))
        lines.append(_say_fact(_fact(entity, preds[i + 1], positive)))
    if trailing_rule and steps < len(rules):
        lines.append(_say_rule(rules[steps]))
    return lines


def _build(index: int, entailed: bool, rng: random.Random) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    ents, preds = _vocabulary(rng, 4, 5 + 5 + 5 + 2)
    subject, donor, filler, other = ents
    main = preds[0:5]              # p0..p4, the queried chain
    side = preds[5:10]             # s0..s4, subject's unrelated chain, same length as main
    dono = preds[10:15]            # donor's parallel chain
    qx, qy = preds[15], preds[16]  # distractor pair, subject never has qx

    last_pos = entailed
    main_rules = [_rule(main[i], main[i + 1], positive=(last_pos or i < DEPTH - 1))
                  for i in range(DEPTH)]
    side_rules = [_rule(side[i], side[i + 1]) for i in range(DEPTH)]
    dono_rules = [_rule(dono[i], dono[i + 1]) for i in range(DEPTH)]
    distractor = _rule(qx, qy)

    facts = [_fact(subject, main[0]), _fact(subject, side[0]),
             _fact(donor, dono[0]), _fact(filler, qx), _fact(other, dono[0])]
    rules = main_rules + side_rules + dono_rules + [distractor]
    rng.shuffle(facts); rng.shuffle(rules)

    query = _fact(subject, main[DEPTH])
    cert = cl.certify(query, facts, rules)
    want = cl.ENTAILED if entailed else cl.CONTRADICTED
    if cert["verdict"] != want:
        raise RuntimeError(f"item {index}: intended {want}, certified {cert['verdict']}")
    theory = " ".join([_say_fact(f) for f in facts] + [_say_rule(r) for r in rules])

    # ---- arms ---------------------------------------------------------------
    t1 = _ladder(subject, main, main_rules, DEPTH - 1, True, last_pos)   # 8 lines, ends on final rule
    t2 = _ladder(subject, main, main_rules, DEPTH - 2, True, last_pos)   # 6 lines
    t3 = _ladder(subject, main, main_rules, DEPTH - 3, True, last_pos)   # 4 lines
    full = _ladder(subject, main, main_rules, DEPTH, False, last_pos)    # 9 lines, incl. terminal literal

    # broken_chain: entity-frequency matched to t1, same line-type sequence, query
    # predicate still present in the final rule -- but the antecedent that rule
    # needs is never established, and line 7 asserts a literal that is NOT in the
    # closure. Every RULE shown is a real theory rule; only that literal is false.
    broken = (_ladder(subject, main, main_rules, DEPTH - 2, False, True)
              + [_say_rule(distractor), _say_fact(_fact(subject, qy)),
                 _say_rule(main_rules[DEPTH - 1])])

    # misleading: same shape, but one fabricated final rule flips polarity, so a
    # model that follows the supplied state answers against the ground truth.
    fabricated = _rule(main[DEPTH - 1], main[DEPTH], positive=not last_pos)
    misleading = (_ladder(subject, main, main_rules, DEPTH - 1, False, True)
                  + [_say_rule(fabricated),
                     _say_fact(_fact(subject, main[DEPTH], positive=not last_pos))])

    # mirrors truncate_1 exactly in shape and subject count, but the chain runs
    # toward an unrelated predicate, so the query predicate never appears.
    same_entity = _ladder(subject, side, side_rules, DEPTH - 1, True, True)
    donor_lines = _ladder(donor, dono, dono_rules, DEPTH - 1, True, True)[: len(t1)]
    shuffled = list(t1); rng.shuffle(shuffled)

    bodies = {"none": [], "irrelevant": donor_lines, "same_entity_irrelevant": same_entity,
              "truncate_3": t3, "truncate_2": t2, "truncate_1": t1,
              "broken_chain": broken, "misleading": misleading,
              "shuffled": shuffled, "full": full}
    certs = {a: ("Solver record: " + " ".join(v) if v else "") for a, v in bodies.items()}

    # ---- construction invariants -------------------------------------------
    mentions = {a: " ".join(v).count(subject) for a, v in bodies.items()}
    # `misleading` carries a terminal literal, so its shape partner is `full`;
    # the other controls are matched to `truncate_1`.
    for arm, partner in (("broken_chain", "truncate_1"), ("same_entity_irrelevant", "truncate_1"),
                         ("shuffled", "truncate_1"), ("misleading", "full")):
        if mentions[arm] != mentions[partner]:
            raise RuntimeError(f"item {index}: {arm} mentions subject {mentions[arm]}x, "
                               f"{partner} {mentions[partner]}x")
        if len(bodies[arm]) != len(bodies[partner]):
            raise RuntimeError(f"item {index}: {arm} has {len(bodies[arm])} lines, "
                               f"{partner} has {len(bodies[partner])}")
    shown = ([_fact(subject, main[0])]
             + [_fact(subject, main[i + 1]) for i in range(DEPTH - 2)]
             + [_fact(subject, qy)])
    shown_rules = main_rules[:DEPTH - 2] + [distractor, main_rules[DEPTH - 1]]
    bc = cl.certify(query, shown, shown_rules)
    if bc["verdict"] != cl.UNDETERMINED:
        raise RuntimeError(f"item {index}: broken_chain lines still settle the query "
                           f"({bc['verdict']})")

    query_text = f"{subject} is {main[DEPTH]}."
    prompts = {a: (f"{SYSTEM}\n{theory}\n" + (f"{c}\n" if c else "") + f"Query: {query_text} Answer:")
               for a, c in certs.items()}
    for arm, text in prompts.items():
        body = text[len(SYSTEM):].lower()
        for token in BANNED:
            if re.search(rf"\b{token}\b", body):
                raise RuntimeError(f"item {index} arm {arm} leaks response token {token!r}")

    task_id = "b15-" + hashlib.sha256(f"{TASK_SEED}:{index}".encode()).hexdigest()[:16]
    public = {"task_id": task_id, "version": VERSION, "depth": DEPTH,
              "theory": theory, "query": query_text, "prompts": prompts,
              "entity_mentions": mentions,
              "line_counts": {a: len(v) for a, v in bodies.items()},
              "char_lengths": {a: len(c) for a, c in certs.items()}}
    authority = {"task_id": task_id, "answer": "Yes" if entailed else "No",
                 "semantic_class": want, "certification": cert,
                 "broken_chain_certification": bc,
                 "fabricated_lines": {"misleading": 2, "broken_chain": 1}}
    return public, authority


def _qualification_item(index: int, entailed: bool, rng: random.Random) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    """Depth-0 delivery probe: the queried fact is stated outright.

    Demoted to a recorded smoke check rather than a blocking gate. b14 ran this
    exact screen on these exact weights and passed (36/36, 33/36), and b16
    established that a direct-fact screen says nothing about task competence --
    it passed 36/36 while the model was degenerate on the real panel. Its value
    here is verifying the runtime path and preserving b14 comparability.
    """
    ents, preds = _vocabulary(rng, 4, 4)
    subject = ents[0]
    facts = [_fact(e, q, positive=True) for e, q in zip(ents[1:], preds[1:])]
    facts.append(_fact(subject, preds[0], positive=entailed))
    rng.shuffle(facts)
    sentences = [_say_fact(f) for f in facts]
    query_text = f"{subject} is {preds[0]}."
    templates = {"direct": " ".join(sentences),
                 "reordered": " ".join(reversed(sentences))}
    prompts = {k: f"{SYSTEM}\n{v}\nQuery: {query_text} Answer:" for k, v in templates.items()}
    task_id = "b15q-" + hashlib.sha256(f"{QUAL_SEED}:{index}".encode()).hexdigest()[:16]
    return ({"task_id": task_id, "version": VERSION, "stage": "qualification",
             "query": query_text, "prompts": prompts},
            {"task_id": task_id, "answer": "Yes" if entailed else "No",
             "semantic_class": cl.ENTAILED if entailed else cl.CONTRADICTED})


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _write(p: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Seal the b15 panel (no model calls).")
    ap.add_argument("--project", type=Path, default=Path("."))
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    data = args.project.resolve() / DATA
    if data.exists() and not args.force:
        raise RuntimeError("b15 panel construction is consumed; refusing to overwrite")

    rng = random.Random(TASK_SEED)
    public: list[Mapping[str, Any]] = []
    authority: list[Mapping[str, Any]] = []
    idx = 0
    for entailed in (True, False):
        for _ in range(PER_CLASS):
            p, a = _build(idx, entailed, rng)
            public.append(p); authority.append(a); idx += 1
    if len({r["task_id"] for r in public}) != len(public):
        raise RuntimeError("task ids are not unique")

    qrng = random.Random(QUAL_SEED)
    qpub: list[Mapping[str, Any]] = []
    qauth: list[Mapping[str, Any]] = []
    for i in range(QUAL_N):
        a, b = _qualification_item(i, i < QUAL_N // 2, qrng)
        qpub.append(a); qauth.append(b)
    _write(data / "public/qualification.jsonl", qpub)
    _write(data / "sealed/qualification-authority.jsonl", qauth)

    pub, auth = data / "public/panel.jsonl", data / "sealed/authority.jsonl"
    _write(pub, public); _write(auth, authority)
    seal = {"version": VERSION, "task_seed": TASK_SEED, "depth": DEPTH, "n": len(public),
            "per_class": PER_CLASS, "arms": list(ARMS),
            "public_path": str(DATA / "public/panel.jsonl"), "public_sha256": _sha256(pub),
            "authority_path": str(DATA / "sealed/authority.jsonl"), "authority_sha256": _sha256(auth),
            "qualification_n": QUAL_N, "qualification_seed": QUAL_SEED,
            "qualification_templates": ["direct", "reordered"],
            "qualification_role": "recorded smoke check, not a blocking gate",
            "qualification_public_path": str(DATA / "public/qualification.jsonl"),
            "qualification_public_sha256": _sha256(data / "public/qualification.jsonl"),
            "qualification_authority_sha256": _sha256(data / "sealed/qualification-authority.jsonl"),
            "note": "tenth arm `full` added before data collection as a comparability anchor"}
    seal["seal_id"] = hashlib.sha256(json.dumps(seal, sort_keys=True).encode()).hexdigest()
    (data / "public/seal.json").write_text(json.dumps(seal, indent=2, sort_keys=True) + "\n",
                                           encoding="utf-8")
    print(json.dumps({"status": "b15_panel_sealed", "n": len(public),
                      "arms": len(ARMS), "seal_id": seal["seal_id"]}, sort_keys=True))


if __name__ == "__main__":
    main()
