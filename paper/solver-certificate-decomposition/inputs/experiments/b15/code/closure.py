"""Forward-closure saturation and three-way entailment classification.

Certifying that a query IS derivable is easy: exhibit the proof. Certifying that
it is NOT derivable is the harder direction, and it is what an `underdetermined`
item requires. This module saturates a theory's forward closure and reports
whether the query, its negation, or neither appears.

Semantics are open-world with explicit negation: a negative literal is derivable
only if something actually derives it, never by failure to prove the positive.
Rule antecedents are ordinary positive/negative literals -- there is no
negation-as-failure -- so naive forward chaining is sound and complete here.
Applying this to a closed-world theory would be wrong.

Two safeguards the ad hoc chainer in `proofwriter_verified_trace_v4` lacked:

* an explicit round cap with a `saturated` flag, so a malformed generated theory
  fails loudly instead of spinning;
* inconsistency detection. If a theory derives both an atom and its negation it
  is unusable, and an item built on it must be rejected rather than labelled.

Stdlib only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence

Atom = tuple[str, str, str, str]              # (subject, relation, object, polarity)
Rule = tuple[tuple[Atom, ...], Atom]          # (antecedents, consequent)

VARIABLES = frozenset(("someone", "something"))
ATOM_RE = re.compile(r'\("([^"]*)"\s+"([^"]*)"\s+"([^"]*)"\s+"([+\-~])"\)')
MAX_ROUNDS = 64

ENTAILED, CONTRADICTED, UNDETERMINED = "entailed", "contradicted", "undetermined"


def _polarity(value: str) -> str:
    return "-" if value == "~" else value


def parse_atoms(representation: str) -> tuple[Atom, ...]:
    return tuple((a, b, c, _polarity(p)) for a, b, c, p in ATOM_RE.findall(representation))


def parse_atom(representation: str) -> Atom:
    found = parse_atoms(representation)
    if len(found) != 1:
        raise ValueError(f"expected exactly one atom, parsed {len(found)}: {representation!r}")
    return found[0]


def parse_rule(representation: str) -> Rule:
    """Split on the implication arrow rather than assuming the consequent is last."""
    if "->" not in representation:
        raise ValueError(f"rule has no implication arrow: {representation!r}")
    left, right = representation.split("->", 1)
    antecedents, consequents = parse_atoms(left), parse_atoms(right)
    if not antecedents:
        raise ValueError(f"rule has no antecedent: {representation!r}")
    if len(consequents) != 1:
        raise ValueError(f"rule must have exactly one consequent: {representation!r}")
    return antecedents, consequents[0]


def negate(atom: Atom) -> Atom:
    return atom[:3] + ("-" if atom[3] == "+" else "+",)


def is_ground(atom: Atom) -> bool:
    return not any(part in VARIABLES for part in atom)


def _match(pattern: Atom, observed: Atom, bindings: Mapping[str, str]) -> dict[str, str] | None:
    updated = dict(bindings)
    for expected, actual in zip(pattern, observed, strict=True):
        if expected in VARIABLES:
            prior = updated.get(expected)
            if prior is None:
                updated[expected] = actual
            elif prior != actual:
                return None
        elif expected != actual:
            return None
    return updated


def _bindings_for(antecedents: Sequence[Atom], facts: Sequence[Atom]) -> tuple[Mapping[str, str], ...]:
    candidates: tuple[Mapping[str, str], ...] = ({},)
    for antecedent in antecedents:
        nxt: list[Mapping[str, str]] = []
        for bindings in candidates:
            for fact in facts:
                matched = _match(antecedent, fact, bindings)
                if matched is not None:
                    nxt.append(matched)
        candidates = tuple(nxt)
        if not candidates:
            break
    return candidates


def _ground(pattern: Atom, bindings: Mapping[str, str]) -> Atom:
    return tuple(bindings.get(v, v) if v in VARIABLES else v for v in pattern)  # type: ignore[return-value]


@dataclass(frozen=True)
class Closure:
    atoms: frozenset[Atom]
    rounds: int
    saturated: bool
    consistent: bool
    conflicts: tuple[Atom, ...] = field(default=())

    @property
    def usable(self) -> bool:
        return self.saturated and self.consistent


def saturate(facts: Iterable[Atom], rules: Iterable[Rule], max_rounds: int = MAX_ROUNDS) -> Closure:
    known: set[Atom] = set(facts)
    rule_list = list(rules)
    rounds = 0
    saturated = False
    while rounds < max_rounds:
        rounds += 1
        snapshot = tuple(known)
        added = False
        for antecedents, consequent in rule_list:
            for bindings in _bindings_for(antecedents, snapshot):
                implied = _ground(consequent, bindings)
                if not is_ground(implied):
                    raise ValueError(f"rule consequent left unbound: {consequent}")
                if implied not in known:
                    known.add(implied)
                    added = True
        if not added:
            saturated = True
            break
    conflicts = tuple(sorted(a for a in known if a[3] == "+" and negate(a) in known))
    return Closure(frozenset(known), rounds, saturated, not conflicts, conflicts)


def classify(query: Atom, closure: Closure) -> str:
    """Three-way verdict for `query` against a saturated closure."""
    if not closure.usable:
        raise ValueError(f"closure unusable (saturated={closure.saturated}, "
                         f"consistent={closure.consistent})")
    if query in closure.atoms:
        return ENTAILED
    if negate(query) in closure.atoms:
        return CONTRADICTED
    return UNDETERMINED


def certify(query: Atom, facts: Iterable[Atom], rules: Iterable[Rule],
            max_rounds: int = MAX_ROUNDS) -> Mapping[str, object]:
    """Full evidence record for a sealed panel's source audit."""
    facts = tuple(facts)
    rules = tuple(rules)
    c = saturate(facts, rules, max_rounds)
    verdict = classify(query, c) if c.usable else None
    return {
        "query": list(query),
        "verdict": verdict,
        "query_in_closure": query in c.atoms,
        "negation_in_closure": negate(query) in c.atoms,
        "closure_size": len(c.atoms),
        "n_facts": len(facts), "n_rules": len(rules),
        "rounds": c.rounds, "saturated": c.saturated,
        "consistent": c.consistent,
        "conflicts": [list(a) for a in c.conflicts],
    }
