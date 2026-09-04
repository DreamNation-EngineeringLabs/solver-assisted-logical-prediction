#!/usr/bin/env python3
"""Seal a fresh three-way solver-certificate factorial without loading a model."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence


VERSION = "solver-assisted-certificate-factorial-v8"
DATA = Path("data/cognitive_core/solver_assisted_certificate_factorial_v8")
TASK_SEED = 2026090108
LABELS = ("A", "B", "C")
NORMAL_MAP = {"entailed": "A", "contradicted": "B", "unknown": "C"}
ALTERNATE_MAP = {"entailed": "C", "contradicted": "A", "unknown": "B"}
QUALIFICATION_PER_CLASS = 12
DEVELOPMENT_PER_CLASS = 24
PROSPECTIVE_PER_CLASS = 64


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_new(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(body)
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
    """Stable pronounceable nonce term derived from the public generation seed."""
    digest = hashlib.sha256(f"{TASK_SEED}:{role}:{index}".encode("utf-8")).digest()
    onsets = ("b", "d", "f", "g", "k", "l", "m", "n", "p", "r", "s", "t", "v", "z")
    vowels = ("a", "e", "i", "o", "u")
    syllables = []
    for offset in range(3):
        syllables.append(onsets[digest[2 * offset] % len(onsets)] + vowels[digest[2 * offset + 1] % len(vowels)])
    return "".join(syllables) + str(index)


def _literal(entity: str, prop: str, *, negative: bool = False) -> str:
    return f"{entity} is {'not ' if negative else ''}{prop}"


def _mapping_lines(mapping: Mapping[str, str]) -> str:
    inverse = {label: semantic for semantic, label in mapping.items()}
    return "\n".join(f"{label} = {inverse[label]}." for label in LABELS)


def _prompt(theory: str, query: str, certificate: str | None, mapping: Mapping[str, str]) -> str:
    certificate_block = "" if certificate is None else f"\n\n{certificate}"
    return (
        "Use only the stated rules, facts, and any solver record. Return exactly one response label.\n\n"
        f"{theory}{certificate_block}\n\nQuery: {query}.\n\n"
        f"{_mapping_lines(mapping)}\nAnswer:"
    )


def _chain(entity: str, props: Sequence[str], *, final_tag: str = "I01") -> tuple[list[str], list[str]]:
    if len(props) != 5:
        raise ValueError("certificate chains require five properties")
    all_lines = [f"[F01] {_literal(entity, props[0])}."]
    for step in range(4):
        rule_tag = f"R{step + 1:02d}"
        result_tag = final_tag if step == 3 else f"I{4 - step:02d}"
        all_lines.append(f"[{rule_tag}] All {props[step]} people are {props[step + 1]}.")
        all_lines.append(f"[{result_tag}] {_literal(entity, props[step + 1])}.")
    prefix = all_lines[:-1]
    return prefix, all_lines


def _certificate(header: str, lines: Sequence[str]) -> str:
    return header + "\n" + "\n".join(lines)


def _factorial_item(index: int, split: str, semantic: str) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    if semantic not in NORMAL_MAP:
        raise ValueError("unsupported semantic class")
    entity = _word(index, f"{split}-entity")
    donor = _word(index, f"{split}-donor")
    props = [_word(index * 11 + offset, f"{split}-property") for offset in range(7)]
    donor_props = [_word(index * 11 + offset, f"{split}-donor-property") for offset in range(7)]
    prefix, full_lines = _chain(entity, props[:5])
    donor_prefix, donor_full_lines = _chain(donor, donor_props[:5])
    facts = [f"[F01] {_literal(entity, props[0])}.", f"[F02] {_literal(donor, donor_props[0])}."]
    rules = []
    for chain_props in (props[:5], donor_props[:5]):
        for step in range(4):
            rules.append(f"All {chain_props[step]} people are {chain_props[step + 1]}.")
    theory = "Facts:\n" + "\n".join(facts) + "\nRules:\n" + "\n".join(
        f"[R{line + 1:02d}] {rule}" for line, rule in enumerate(rules)
    )
    if semantic == "entailed":
        query = _literal(entity, props[4])
        conclusion = f"[I01] {_literal(entity, props[4])}."
        irrelevant = _certificate("Solver-verified derivation certificate (no response label):", donor_full_lines)
        conclusion_only = _certificate("Solver-verified conclusion (no response label):", [conclusion])
        prefix_certificate = _certificate("Solver-verified derivation prefix (final conclusion omitted):", prefix)
        full = _certificate("Solver-verified derivation certificate (no response label):", full_lines)
        certificate_type = "derivation"
    elif semantic == "contradicted":
        query = _literal(entity, props[4], negative=True)
        conclusion = f"[I01] {_literal(entity, props[4])}."
        irrelevant = _certificate("Solver-verified derivation certificate (no response label):", donor_full_lines)
        conclusion_only = _certificate("Solver-verified conclusion (no response label):", [conclusion])
        prefix_certificate = _certificate("Solver-verified derivation prefix (final conclusion omitted):", prefix)
        full = _certificate("Solver-verified derivation certificate (no response label):", full_lines)
        certificate_type = "derivation"
    else:
        query = _literal(entity, props[5])
        inverse = _literal(entity, props[5], negative=True)
        donor_query = _literal(donor, donor_props[5])
        donor_inverse = _literal(donor, donor_props[5], negative=True)
        status = f"[C01] Complete solver closure contains neither {query} nor {inverse}."
        donor_status = f"[C01] Complete solver closure contains neither {donor_query} nor {donor_inverse}."
        irrelevant = _certificate("Solver-verified closure certificate (no response label):", [*donor_full_lines, donor_status])
        conclusion_only = _certificate("Solver-verified closure status (no response label):", [status])
        prefix_certificate = _certificate("Solver-verified closure prefix (final status omitted):", full_lines)
        full = _certificate("Solver-verified closure certificate (no response label):", [*full_lines, status])
        certificate_type = "closure"
    forbidden = ("A =", "B =", "C =", "entailed", "contradicted", "unknown")
    certificates = {"irrelevant": irrelevant, "conclusion_only": conclusion_only, "proof_prefix": prefix_certificate, "full": full}
    if any(any(token in certificate.lower() for token in ("entailed", "contradicted", "unknown")) for certificate in certificates.values()):
        raise RuntimeError("certificate leaked a semantic class word")
    if any(any(token in certificate for token in forbidden[:3]) for certificate in certificates.values()):
        raise RuntimeError("certificate leaked a response mapping")
    task_id = f"scf8-{split}-{semantic}-{index:03d}"
    prompts = {"none": _prompt(theory, query, None, NORMAL_MAP)}
    prompts.update({arm: _prompt(theory, query, certificate, NORMAL_MAP) for arm, certificate in certificates.items()})
    public = {
        "version": VERSION,
        "task_id": task_id,
        "split": split,
        "semantic_class": semantic,
        "generation": {"seed": TASK_SEED, "generator_index": index, "nonce_vocabulary": True, "posttraining_exact_item_generation_claim": True},
        "certificate_type": certificate_type,
        "theory": theory,
        "query": query,
        "prompts": prompts,
        "certificates": certificates,
        "certificate_sha256": {arm: _digest(certificate) for arm, certificate in certificates.items()},
    }
    authority = {"task_id": task_id, "semantic_class": semantic, "answer": NORMAL_MAP[semantic]}
    return public, authority


def _qualification_item(index: int, semantic: str) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    entity = _word(index, "qualification-entity")
    prop = _word(index, "qualification-property")
    other = _word(index, "qualification-other-property")
    if semantic == "entailed":
        facts, query = [f"[F01] {_literal(entity, prop)}."], _literal(entity, prop)
    elif semantic == "contradicted":
        facts, query = [f"[F01] {_literal(entity, prop)}."], _literal(entity, prop, negative=True)
    elif semantic == "unknown":
        facts, query = [f"[F01] {_literal(entity, other)}."], _literal(entity, prop)
    else:
        raise ValueError("unsupported qualification class")
    theory = "Facts:\n" + "\n".join(facts) + "\nRules:\n(no rules)"
    task_id = f"scf8-interface-{semantic}-{index:03d}"
    public = {"version": VERSION, "task_id": task_id, "semantic_class": semantic, "normal_prompt": _prompt(theory, query, None, NORMAL_MAP), "alternate_prompt": _prompt(theory, query, None, ALTERNATE_MAP)}
    authority = {"task_id": task_id, "semantic_class": semantic, "normal_answer": NORMAL_MAP[semantic], "alternate_answer": ALTERNATE_MAP[semantic]}
    return public, authority


def _panel(split: str, per_class: int) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]]]:
    public: list[Mapping[str, Any]] = []
    authority: list[Mapping[str, Any]] = []
    offset = 1000 if split == "development" else 100_000
    for semantic in NORMAL_MAP:
        for index in range(per_class):
            task, answer = _factorial_item(offset + len(public), split, semantic)
            public.append(task)
            authority.append(answer)
    return public, authority


def _protocol() -> Mapping[str, Any]:
    body: dict[str, Any] = {
        "version": VERSION,
        "research_question": "Does a solver proof prefix with its final conclusion omitted improve three-way logical prediction beyond conclusion-only solver evidence and a valid matched irrelevant proof?",
        "prior_boundary": "ProofWriter v7 is a completed limited pilot of query-relevant solver-assisted prediction. It is not reopened, pooled, or used as evidence that intermediate proof state supports inference.",
        "task": {"family": "posttraining_procedural_open_world_rule_reasoning", "exact_item_novelty": "deterministic public-seed nonce generated after model release", "pretraining_independence_claim": "not established", "classes": list(NORMAL_MAP), "class_balance": True},
        "arms": {"none": "no solver material", "irrelevant": "valid same-shape solver certificate for a different conclusion", "conclusion_only": "solver conclusion or closure status for the query", "proof_prefix": "solver facts/rules/intermediates with final conclusion or status omitted", "full": "complete current solver certificate"},
        "primary_contrast": "proof_prefix_minus_conclusion_only",
        "secondary_contrasts": ["proof_prefix_minus_irrelevant", "full_minus_conclusion_only"],
        "analysis": {"paired_table": True, "test": "exact_two_sided_mcnemar", "interval": "95_percent_paired_BCa_bootstrap_100000_seeded_resamples", "secondary_multiplicity": "Holm within model", "strata": "three semantic classes descriptive unless separately powered"},
        "qualification": {"n": 36, "per_class": QUALIFICATION_PER_CLASS, "templates": ["normal", "alternate_label_mapping"], "minimum_accuracy_each_template": 0.75, "minimum_class_accuracy_each_template": 2 / 3, "minimum_semantic_agreement": 32, "failure_interpretation": "delivery failure, not certificate null"},
        "panels": {"development": {"n": DEVELOPMENT_PER_CLASS * 3, "per_class": DEVELOPMENT_PER_CLASS}, "prospective": {"n": PROSPECTIVE_PER_CLASS * 3, "per_class": PROSPECTIVE_PER_CLASS}},
        "power_design": {"target_paired_risk_difference": 0.15, "expected_discordance": 0.35, "normal_approximation_n_for_80_percent_power": 123, "prospective_n": PROSPECTIVE_PER_CLASS * 3, "analysable_pair_floor_after_10_percent_receipt_buffer": 172},
        "models": {"allowed": ["qwen2p5_3b", "qwen3_1p7b"], "aggregation": "qualified models are reported separately; a model failing qualification is excluded"},
        "execution_policy": {"data_construction_attempts": 1, "qualification_attempts_per_model": 1, "prospective_attempts_per_qualified_model": 1, "automatic_restarts_authorized": 0, "automatic_successors_authorized": 0, "prompt_sweeps_authorized": 0},
        "release_requirements": ["code", "generator_seed", "public_panels", "sealed_authorities_after_terminal_scoring", "prompt_templates", "certificates", "model_config_weight_manifest", "candidate_token_ids", "runtime_manifest", "per_item_likelihood_receipts", "analysis_script", "sha256_manifest"],
    }
    return {**body, "protocol_id": _digest(body)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Seal the v8 solver-certificate factorial data.")
    parser.add_argument("--project", type=Path, default=Path("."))
    args = parser.parse_args()
    project, data = args.project.resolve(), args.project.resolve() / DATA
    if data.exists():
        raise RuntimeError("v8 data path already exists; this construction attempt is consumed")
    interface_public: list[Mapping[str, Any]] = []
    interface_authority: list[Mapping[str, Any]] = []
    for semantic in NORMAL_MAP:
        for index in range(QUALIFICATION_PER_CLASS):
            task, answer = _qualification_item(len(interface_public), semantic)
            interface_public.append(task)
            interface_authority.append(answer)
    development_public, development_authority = _panel("development", DEVELOPMENT_PER_CLASS)
    prospective_public, prospective_authority = _panel("prospective", PROSPECTIVE_PER_CLASS)
    if len({task["task_id"] for task in [*interface_public, *development_public, *prospective_public]}) != len(interface_public) + len(development_public) + len(prospective_public):
        raise RuntimeError("task identifiers are not unique")
    protocol = _protocol()
    public = {"interface": interface_public, "development": development_public, "prospective": prospective_public}
    authorities = {"interface": interface_authority, "development": development_authority, "prospective": prospective_authority}
    for name in public:
        _write_rows_new(data / f"public/{name}.jsonl", public[name])
        _write_rows_new(data / f"sealed/{name}-authority.jsonl", authorities[name])
    _write_new(data / "public/protocol.json", protocol)
    seal_body = {"version": VERSION, "protocol_id": protocol["protocol_id"], "protocol_sha256": _sha256(data / "public/protocol.json"), "generator": {"script": "scripts/prepare_cognitive_solver_assisted_certificate_factorial_v8.py", "script_sha256": _sha256(Path(__file__).resolve()), "task_seed": TASK_SEED}, "panels": {name: {"public_path": str((DATA / f"public/{name}.jsonl").as_posix()), "public_sha256": _sha256(data / f"public/{name}.jsonl"), "authority_path": str((DATA / f"sealed/{name}-authority.jsonl").as_posix()), "authority_sha256": _sha256(data / f"sealed/{name}-authority.jsonl"), "n": len(public[name])} for name in public}}
    _write_new(data / "public/seal.json", {**seal_body, "seal_id": _digest(seal_body)})
    print(json.dumps({"status": "v8_data_sealed_without_model_calls", "panels": {name: len(rows) for name, rows in public.items()}, "protocol_id": protocol["protocol_id"], "model_calls": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
