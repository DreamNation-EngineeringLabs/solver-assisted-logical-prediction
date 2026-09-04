"""ProofWriter v4 source checks and canonical proof-reference traces.

These pure-Python helpers operate on public dataset records.  They neither load
nor call a language model.  The forward chainer is intentionally restricted to
the selected OWA binary-proof subset, where rule antecedents are ordinary
positive/negative literals rather than closed-world negation-as-failure.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Iterable, Mapping


VERSION = "cognitive-repairability-proofwriter-data-runtime-v4"
VARIABLES = frozenset(("someone", "something"))
ATOM_RE = re.compile(r'\("([^"]+)"\s+"([^"]+)"\s+"([^"]+)"\s+"([+\-~])"\)')
TRACE_REF_RE = re.compile(r"\b(triple|rule|int)(\d+)\b")

Atom = tuple[str, str, str, str]
Rule = tuple[tuple[Atom, ...], Atom]


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalize_polarity(value: str) -> str:
    return "-" if value == "~" else value


def atoms(representation: str) -> tuple[Atom, ...]:
    return tuple((a, b, c, _normalize_polarity(p)) for a, b, c, p in ATOM_RE.findall(representation))


def _rules(record: Mapping[str, Any]) -> tuple[Rule, ...]:
    values: list[Rule] = []
    rules = record.get("rules")
    if not isinstance(rules, Mapping):
        raise ValueError("ProofWriter record has no rules mapping")
    for row in rules.values():
        if not isinstance(row, Mapping):
            raise ValueError("ProofWriter rule is malformed")
        parsed = atoms(str(row.get("representation", "")))
        if len(parsed) < 2:
            raise ValueError("ProofWriter rule lacks antecedent or consequent atom")
        values.append((parsed[:-1], parsed[-1]))
    return tuple(values)


def _initial_facts(record: Mapping[str, Any]) -> frozenset[Atom]:
    triples = record.get("triples")
    if not isinstance(triples, Mapping):
        raise ValueError("ProofWriter record has no triples mapping")
    facts: set[Atom] = set()
    for row in triples.values():
        if not isinstance(row, Mapping):
            raise ValueError("ProofWriter triple is malformed")
        parsed = atoms(str(row.get("representation", "")))
        if len(parsed) != 1:
            raise ValueError("ProofWriter triple is not one atom")
        facts.add(parsed[0])
    return frozenset(facts)


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


def _bindings_for(antecedents: Iterable[Atom], facts: Iterable[Atom]) -> tuple[Mapping[str, str], ...]:
    candidates: tuple[Mapping[str, str], ...] = ({},)
    fact_values = tuple(facts)
    for antecedent in antecedents:
        updated: list[Mapping[str, str]] = []
        for bindings in candidates:
            for fact in fact_values:
                matched = _match(antecedent, fact, bindings)
                if matched is not None:
                    updated.append(matched)
        candidates = tuple(updated)
        if not candidates:
            break
    return candidates


def _ground(pattern: Atom, bindings: Mapping[str, str]) -> Atom:
    return tuple(bindings.get(value, value) if value in VARIABLES else value for value in pattern)  # type: ignore[return-value]


def closure(record: Mapping[str, Any]) -> frozenset[Atom]:
    known = set(_initial_facts(record))
    rules = _rules(record)
    changed = True
    while changed:
        changed = False
        snapshot = tuple(known)
        for antecedents, consequent in rules:
            for bindings in _bindings_for(antecedents, snapshot):
                implied = _ground(consequent, bindings)
                if implied not in known:
                    known.add(implied)
                    changed = True
    return frozenset(known)


def target_atom(question: Mapping[str, Any]) -> Atom:
    parsed = atoms(str(question.get("representation", "")))
    if len(parsed) != 1:
        raise ValueError("ProofWriter query is not one atom")
    answer = question.get("answer")
    if not isinstance(answer, bool):
        raise ValueError("selected ProofWriter query must be binary")
    atom = parsed[0]
    if answer:
        return atom
    flip = "+" if atom[-1] == "-" else "-"
    return atom[:-1] + (flip,)


def canonical_trace(record: Mapping[str, Any], question: Mapping[str, Any]) -> str:
    options = question.get("proofsWithIntermediates")
    if not isinstance(options, list) or not options or not isinstance(options[0], Mapping):
        raise ValueError("selected ProofWriter query has no canonical proof trace")
    representation = str(options[0].get("representation", ""))
    if not representation:
        raise ValueError("canonical proof trace is empty")

    def rewrite(match: re.Match[str]) -> str:
        kind, value = match.groups()
        label = {"triple": "F", "rule": "R", "int": "I"}[kind]
        return label + f"{int(value):02d}"

    trace = TRACE_REF_RE.sub(rewrite, representation)
    if trace == representation or "F" not in trace or "R" not in trace:
        raise ValueError("canonical trace does not contain fact and rule references")
    return "TRACE " + trace


def corrupted_trace(record: Mapping[str, Any], trace: str) -> str:
    triples = record.get("triples")
    rules = record.get("rules")
    if not isinstance(triples, Mapping) or not isinstance(rules, Mapping) or len(triples) < 2 or len(rules) < 2:
        raise ValueError("trace derangement requires at least two facts and rules")
    fact_count, rule_count = len(triples), len(rules)

    def rewrite(match: re.Match[str]) -> str:
        kind, digits = match.groups()
        value = int(digits)
        if kind == "F":
            return "F" + f"{(value % fact_count) + 1:02d}"
        if kind == "R":
            return "R" + f"{(value % rule_count) + 1:02d}"
        return "I" + digits

    result = re.sub(r"\b([FRI])(\d{2})\b", rewrite, trace)
    if result == trace or len(result) != len(trace):
        raise ValueError("trace derangement is not content-changing and length-preserving")
    return result


def verify_record_question(record: Mapping[str, Any], question: Mapping[str, Any]) -> tuple[str, str]:
    derived = closure(record)
    target = target_atom(question)
    if target not in derived:
        raise ValueError("stored binary ProofWriter answer is not independently derivable")
    options = question.get("proofsWithIntermediates")
    if not isinstance(options, list) or not options or not isinstance(options[0], Mapping):
        raise ValueError("stored binary ProofWriter answer lacks an intermediate proof")
    intermediates = options[0].get("intermediates", {})
    if not isinstance(intermediates, Mapping):
        raise ValueError("stored intermediate proof is malformed")
    for intermediate in intermediates.values():
        if not isinstance(intermediate, Mapping):
            raise ValueError("stored intermediate statement is malformed")
        parsed = atoms(str(intermediate.get("representation", "")))
        if len(parsed) != 1 or parsed[0] not in derived:
            raise ValueError("stored proof intermediate is not independently derivable")
    trace = canonical_trace(record, question)
    return trace, corrupted_trace(record, trace)
