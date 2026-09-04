#!/usr/bin/env python3
"""Seal a fresh binary proof-certificate factorial without loading a model.

This study narrows the question to derivable binary queries.  It does not
reopen any three-way panel or make an open-world-unknown claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Mapping, Sequence


VERSION = "binary-certificate-factorial-b11"
DATA = Path("data/cognitive_core/binary_certificate_factorial_b11")
TASK_SEED = 2026090127
CLASSES = ("entailed", "contradicted")
ANSWER = {"entailed": "Yes", "contradicted": "No"}
QUALIFICATION_PER_CLASS = 18
DEVELOPMENT_PER_CLASS = 36
PROSPECTIVE_PER_CLASS = 96
ARMS = ("none", "irrelevant", "conclusion_only", "proof_prefix", "full")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_new(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _write_rows_new(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _word(index: int, role: str) -> str:
    digest = hashlib.sha256(f"{TASK_SEED}:{role}:{index}".encode("utf-8")).digest()
    onsets = ("b", "d", "f", "g", "k", "l", "m", "n", "p", "r", "s", "t", "v", "z")
    vowels = ("a", "e", "i", "o", "u")
    return "".join(onsets[digest[offset * 2] % len(onsets)] + vowels[digest[offset * 2 + 1] % len(vowels)] for offset in range(3)) + str(index)


def _literal(entity: str, prop: str, *, negative: bool = False) -> str:
    return f"{entity} is {'not ' if negative else ''}{prop}"


def _prompt(theory: str, query: str, certificate: str | None, *, reordered: bool = False) -> str:
    record = "" if certificate is None else f"\n\n{certificate}"
    suffix = (
        "Reply with exactly Yes if the query follows, or No if its inverse follows.\nAnswer:"
        if not reordered
        else "Choose one word only: No if the inverse follows; Yes if the query follows.\nAnswer:"
    )
    return f"Use only the stated facts, rules, and any solver record.\n\n{theory}{record}\n\nQuery: {query}.\n\n{suffix}"


def _chain(entity: str, props: Sequence[str]) -> tuple[list[str], list[str]]:
    if len(props) != 5:
        raise ValueError("five properties required")
    full = [f"[F01] {_literal(entity, props[0])}."]
    for step in range(4):
        full.append(f"[R{step + 1:02d}] All {props[step]} people are {props[step + 1]}.")
        full.append(f"[{'I01' if step == 3 else f'I{4 - step:02d}'}] {_literal(entity, props[step + 1])}.")
    return full[:-1], full


def _certificate(header: str, lines: Sequence[str]) -> str:
    return header + "\n" + "\n".join(lines)


def _factorial_item(index: int, split: str, semantic: str) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    if semantic not in ANSWER:
        raise ValueError("unsupported binary class")
    entity, donor = _word(index, f"{split}-entity"), _word(index, f"{split}-donor")
    props = [_word(index * 17 + offset, f"{split}-property") for offset in range(7)]
    donor_props = [_word(index * 17 + offset, f"{split}-donor-property") for offset in range(7)]
    prefix, full_lines = _chain(entity, props[:5])
    donor_prefix, donor_full = _chain(donor, donor_props[:5])
    del donor_prefix
    rule_text = [
        f"All {chain_props[step]} people are {chain_props[step + 1]}."
        for chain_props in (props[:5], donor_props[:5])
        for step in range(4)
    ]
    theory = "Facts:\n" + "\n".join((f"[F01] {_literal(entity, props[0])}.", f"[F02] {_literal(donor, donor_props[0])}.")) + "\nRules:\n" + "\n".join(
        f"[R{line + 1:02d}] {rule}" for line, rule in enumerate(rule_text)
    )
    conclusion = f"[I01] {_literal(entity, props[4])}."
    query = _literal(entity, props[4], negative=semantic == "contradicted")
    certificates = {
        "irrelevant": _certificate("Solver-verified derivation certificate:", donor_full),
        "conclusion_only": _certificate("Solver-verified conclusion:", (conclusion,)),
        "proof_prefix": _certificate("Solver-verified derivation prefix (terminal literal omitted):", prefix),
        "full": _certificate("Solver-verified derivation certificate:", full_lines),
    }
    forbidden = ("Yes", "No", "entailed", "contradicted")
    if any(any(re.search(rf"\\b{re.escape(token)}\\b", certificate, flags=re.IGNORECASE) for token in forbidden) for certificate in certificates.values()):
        raise RuntimeError("certificate leaked response semantics")
    task_id = f"bcf11-{split}-{semantic}-{index:03d}"
    prompts = {"none": _prompt(theory, query, None)}
    prompts.update({arm: _prompt(theory, query, certificate) for arm, certificate in certificates.items()})
    public = {
        "version": VERSION,
        "task_id": task_id,
        "split": split,
        "semantic_class": semantic,
        "generation": {"seed": TASK_SEED, "generator_index": index, "nonce_vocabulary": True, "posttraining_exact_item_generation_claim": True},
        "theory": theory,
        "query": query,
        "prompts": prompts,
        "certificates": certificates,
        "certificate_sha256": {arm: _digest(value) for arm, value in certificates.items()},
    }
    return public, {"task_id": task_id, "semantic_class": semantic, "answer": ANSWER[semantic]}


def _qualification_item(index: int, semantic: str) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    entity, prop = _word(index, "qualification-entity"), _word(index, "qualification-property")
    query = _literal(entity, prop, negative=semantic == "contradicted")
    theory = f"Facts:\n[F01] {_literal(entity, prop)}.\nRules:\n(no rules)"
    task_id = f"bcf11-interface-{semantic}-{index:03d}"
    return {
        "version": VERSION,
        "task_id": task_id,
        "semantic_class": semantic,
        "direct_prompt": _prompt(theory, query, None),
        "reordered_prompt": _prompt(theory, query, None, reordered=True),
    }, {"task_id": task_id, "semantic_class": semantic, "answer": ANSWER[semantic]}


def _panel(split: str, per_class: int) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]]]:
    public: list[Mapping[str, Any]] = []
    authority: list[Mapping[str, Any]] = []
    offset = 1000 if split == "development" else 100_000
    for semantic in CLASSES:
        for _ in range(per_class):
            item, answer = _factorial_item(offset + len(public), split, semantic)
            public.append(item)
            authority.append(answer)
    return public, authority


def _protocol() -> Mapping[str, Any]:
    body = {
        "version": VERSION,
        "research_question": "For binary derivable logical queries, does a solver proof prefix with its terminal conclusion withheld improve direct Yes/No prediction beyond conclusion-only solver evidence and a matched irrelevant proof?",
        "scope_boundary": "This is a binary derivable-query test. It does not test or claim open-world unknown competence.",
        "task": {"family": "posttraining_procedural_binary_rule_reasoning", "classes": list(CLASSES), "class_balance": True, "exact_item_novelty": "deterministic nonce generation after model release", "pretraining_independence_claim": "not established"},
        "arms": {"none": "no solver material", "irrelevant": "valid matched derivation for a donor entity", "conclusion_only": "terminal derived literal only", "proof_prefix": "facts, rules, and intermediates with terminal literal omitted", "full": "complete derivation including terminal literal"},
        "primary_contrast": "proof_prefix_minus_conclusion_only",
        "secondary_contrasts": ["proof_prefix_minus_irrelevant", "full_minus_conclusion_only"],
        "analysis": {"paired_table": True, "test": "exact_two_sided_mcnemar", "interval": "95_percent_paired_BCa_bootstrap_100000_seeded_resamples", "secondary_multiplicity": "Holm within model"},
        "qualification": {"n": QUALIFICATION_PER_CLASS * 2, "templates": ["direct_Yes_No", "reordered_Yes_No"], "minimum_accuracy_each_template": 0.75, "minimum_class_accuracy_each_template": 2 / 3, "minimum_candidate_agreement": 32, "failure_interpretation": "delivery failure, not certificate-treatment null"},
        "panels": {"development": {"n": DEVELOPMENT_PER_CLASS * 2, "per_class": DEVELOPMENT_PER_CLASS}, "prospective": {"n": PROSPECTIVE_PER_CLASS * 2, "per_class": PROSPECTIVE_PER_CLASS}},
        "power_design": {"target_paired_risk_difference": 0.15, "expected_discordance": 0.35, "normal_approximation_n_for_80_percent_power": 123, "prospective_n": PROSPECTIVE_PER_CLASS * 2},
        "model": {"allowed": ["qwen2p5_3b"], "reason": "Qwen2.5-3B showed direct Yes/No competence on the entailed/contradicted subset; unknown is explicitly out of scope"},
        "execution_policy": {"data_construction_attempts": 1, "qualification_attempts_per_model": 1, "prospective_attempts_per_qualified_model": 1, "automatic_restarts_authorized": 0, "automatic_successors_authorized": 0, "prompt_sweeps_authorized": 0},
    }
    return {**body, "protocol_id": _digest(body)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Seal the b11 binary certificate factorial without model calls.")
    parser.add_argument("--project", type=Path, default=Path("."))
    args = parser.parse_args()
    project, data = args.project.resolve(), args.project.resolve() / DATA
    if data.exists():
        raise RuntimeError("b11 data path already exists; construction is consumed")
    interface_public: list[Mapping[str, Any]] = []
    interface_authority: list[Mapping[str, Any]] = []
    for semantic in CLASSES:
        for _ in range(QUALIFICATION_PER_CLASS):
            task, answer = _qualification_item(len(interface_public), semantic)
            interface_public.append(task)
            interface_authority.append(answer)
    development_public, development_authority = _panel("development", DEVELOPMENT_PER_CLASS)
    prospective_public, prospective_authority = _panel("prospective", PROSPECTIVE_PER_CLASS)
    all_tasks = [*interface_public, *development_public, *prospective_public]
    if len({str(task["task_id"]) for task in all_tasks}) != len(all_tasks):
        raise RuntimeError("task identifiers are not unique")
    protocol = _protocol()
    public = {"interface": interface_public, "development": development_public, "prospective": prospective_public}
    authority = {"interface": interface_authority, "development": development_authority, "prospective": prospective_authority}
    for name in public:
        _write_rows_new(data / f"public/{name}.jsonl", public[name])
        _write_rows_new(data / f"sealed/{name}-authority.jsonl", authority[name])
    _write_new(data / "public/protocol.json", protocol)
    seal_body = {
        "version": VERSION,
        "protocol_id": protocol["protocol_id"],
        "protocol_sha256": _sha256(data / "public/protocol.json"),
        "generator": {"script": "scripts/prepare_cognitive_binary_certificate_factorial_b11.py", "script_sha256": _sha256(Path(__file__).resolve()), "task_seed": TASK_SEED},
        "panels": {name: {"public_path": str((DATA / f"public/{name}.jsonl").as_posix()), "public_sha256": _sha256(data / f"public/{name}.jsonl"), "authority_path": str((DATA / f"sealed/{name}-authority.jsonl").as_posix()), "authority_sha256": _sha256(data / f"sealed/{name}-authority.jsonl"), "n": len(public[name])} for name in public},
    }
    _write_new(data / "public/seal.json", {**seal_body, "seal_id": _digest(seal_body)})
    print(json.dumps({"status": "b11_data_sealed_without_model_calls", "panels": {name: len(rows) for name, rows in public.items()}, "protocol_id": protocol["protocol_id"], "model_calls": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
