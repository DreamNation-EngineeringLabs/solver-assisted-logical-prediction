#!/usr/bin/env python3
"""Seal answer-blind, solver-grounded ProofWriter v7 panels without a model."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import zipfile
from pathlib import Path
from typing import Any, Iterable, Mapping

from scientist.domains.cognitive_core.proofwriter_verified_trace_v4 import TRACE_REF_RE, digest, target_atom, verify_record_question


VERSION = "cognitive-repairability-proofwriter-grounded-state-v7"
ARCHIVE = Path("third_party/proofwriter/proofwriter-dataset-V2020.12.3.zip")
ARCHIVE_SHA256 = "bbc5694901e8306d0bd659aa1ad53ccfd02c201864f4b320ffa3777827d1fc26"
ROOT = "proofwriter-dataset-V2020.12.3/"
OLD_DATA = (Path("data/cognitive_core/repairability_proofwriter_hidden_state_v4"), Path("data/cognitive_core/repairability_proofwriter_explicit_state_v6"))
DATA = Path("data/cognitive_core/repairability_proofwriter_grounded_state_v7")
STAGES = {
    "base_qualification": ("OWA/depth-3/meta-train.jsonl", 3, 16),
    "positive_control": ("OWA/depth-3/meta-test.jsonl", 3, 48),
    "prospective": ("OWA/depth-5/meta-train.jsonl", 4, 96),
}


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_new(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())


def _write_jsonl_new(path: Path, values: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        for value in values:
            handle.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _rows(archive: zipfile.ZipFile, member: str) -> Iterable[Mapping[str, Any]]:
    with archive.open(ROOT + member) as handle:
        for line in handle:
            row = json.loads(line)
            if not isinstance(row, Mapping):
                raise RuntimeError("ProofWriter row is not an object")
            yield row


def _rank(stage: str, theory_id: str, question_id: str, control_id: str) -> str:
    return digest(f"{VERSION}|{stage}|{theory_id}|{question_id}|{control_id}")


def _number(value: str, prefix: str) -> int:
    if not value.startswith(prefix):
        raise ValueError(f"unexpected ProofWriter reference {value}")
    return int(value[len(prefix) :])


def _theory(record: Mapping[str, Any]) -> str:
    triples, rules = record.get("triples"), record.get("rules")
    if not isinstance(triples, Mapping) or not isinstance(rules, Mapping):
        raise ValueError("malformed ProofWriter theory")
    facts = [f"[F{_number(str(key), 'triple'):02d}] {value['text']}" for key, value in sorted(triples.items(), key=lambda pair: _number(str(pair[0]), "triple")) if isinstance(value, Mapping)]
    rule_lines = [f"[R{_number(str(key), 'rule'):02d}] {value['text']}" for key, value in sorted(rules.items(), key=lambda pair: _number(str(pair[0]), "rule")) if isinstance(value, Mapping)]
    if len(facts) != len(triples) or len(rule_lines) != len(rules):
        raise ValueError("malformed fact/rule text")
    return "\n".join(["Facts:", *facts, "Rules:", *rule_lines])


def _certificate(record: Mapping[str, Any], question: Mapping[str, Any]) -> tuple[str, tuple[str, ...]]:
    trace, _ = verify_record_question(record, question)
    refs = []
    for kind, digits in re.findall(r"\b([FRI])(\d{2})\b", trace):
        reference = kind + digits
        if reference not in refs:
            refs.append(reference)
    triples, rules = record.get("triples"), record.get("rules")
    options = question.get("proofsWithIntermediates")
    if not isinstance(triples, Mapping) or not isinstance(rules, Mapping) or not isinstance(options, list) or not options or not isinstance(options[0], Mapping):
        raise ValueError("certificate source is malformed")
    intermediates = options[0].get("intermediates")
    if not isinstance(intermediates, Mapping):
        raise ValueError("certificate intermediates are malformed")
    lines = ["Solver-verified derivation certificate (no answer label):"]
    kinds: list[str] = []
    for reference in refs:
        kind, number = reference[0], int(reference[1:])
        source: Any
        if kind == "F":
            source = triples.get(f"triple{number}")
        elif kind == "R":
            source = rules.get(f"rule{number}")
        else:
            source = intermediates.get(f"int{number}")
        if not isinstance(source, Mapping) or not isinstance(source.get("text"), str):
            raise ValueError("certificate reference is unresolved")
        lines.append(f"[{reference}] {source['text']}")
        kinds.append(kind)
    certificate = "\n".join(lines)
    if not kinds or "F" not in kinds or "R" not in kinds or re.search(r"\b(?:A|B|entailed|contradicted)\b", certificate, flags=re.IGNORECASE):
        raise ValueError("certificate leaks a label or lacks proof structure")
    return certificate, tuple(kinds)


def _prompt(theory: str, question: str, certificate: str | None) -> str:
    block = "" if certificate is None else f"\n\n{certificate}"
    return f"{theory}{block}\n\nQuery: {question}\n\nA = entailed. B = contradicted.\nAnswer:"


def _old_theories(project: Path) -> frozenset[str]:
    values: set[str] = set()
    for root in OLD_DATA:
        for path in sorted((project / root / "public").glob("*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                if "source_theory_id" in row:
                    values.add(str(row["source_theory_id"]))
    if not values:
        raise RuntimeError("prior theory manifests are missing")
    return frozenset(values)


def _details(record: Mapping[str, Any], question_id: str, question: Mapping[str, Any]) -> Mapping[str, Any] | None:
    if question.get("strategy") not in {"proof", "inv-proof"} or not isinstance(question.get("answer"), bool) or not isinstance(question.get("QDep"), int):
        return None
    try:
        certificate, shape = _certificate(record, question)
        return {"question_id": question_id, "question": question, "target": target_atom(question), "certificate": certificate, "shape": shape}
    except ValueError:
        return None


def _select(archive: zipfile.ZipFile, stage: str, member: str, depth: int, per_label: int, excluded: frozenset[str]) -> list[Mapping[str, Any]]:
    candidates: dict[bool, list[Mapping[str, Any]]] = {False: [], True: []}
    for record in _rows(archive, member):
        theory_id, questions = record.get("id"), record.get("questions")
        if not isinstance(theory_id, str) or theory_id in excluded or not isinstance(questions, Mapping):
            continue
        details = [item for question_id, question in questions.items() if isinstance(question_id, str) and isinstance(question, Mapping) and question.get("QDep") == depth for item in [_details(record, question_id, question)] if item is not None]
        for item in details:
            donors = [other for other in details if other["question_id"] != item["question_id"] and other["shape"] == item["shape"] and other["target"] != item["target"]]
            if not donors:
                continue
            donor = min(donors, key=lambda other: _rank(stage, theory_id, str(item["question_id"]), str(other["question_id"])))
            question = item["question"]
            candidates[bool(question["answer"])].append({"rank": _rank(stage, theory_id, str(item["question_id"]), str(donor["question_id"])), "theory_id": theory_id, "question_id": item["question_id"], "control_question_id": donor["question_id"], "question": question, "control_question": donor["question"], "theory": _theory(record), "verified_certificate": item["certificate"], "irrelevant_certificate": donor["certificate"], "shape": item["shape"]})
    selected: list[Mapping[str, Any]] = []
    for label in (False, True):
        ordered = sorted(candidates[label], key=lambda item: str(item["rank"]))
        if len(ordered) < per_label:
            raise RuntimeError(f"insufficient grounded-certificate candidates for {stage}/{label}")
        selected.extend(ordered[:per_label])
    return sorted(selected, key=lambda item: str(item["rank"]))


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare v7 grounded-certificate data without a model.")
    parser.add_argument("--project", type=Path, default=Path("."))
    args = parser.parse_args()
    project, data = args.project.resolve(), args.project.resolve() / DATA
    if data.exists():
        raise RuntimeError("v7 data path already exists")
    archive = project / ARCHIVE
    if not archive.is_file() or _sha256(archive) != ARCHIVE_SHA256:
        raise RuntimeError("official ProofWriter archive is unavailable or changed")
    excluded = _old_theories(project)
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:
            raise RuntimeError("ProofWriter archive integrity check failed")
        selected = {stage: _select(bundle, stage, member, depth, per_label, excluded) for stage, (member, depth, per_label) in STAGES.items()}
    theory_sets = {stage: {str(item["theory_id"]) for item in rows} for stage, rows in selected.items()}
    if any(theory_sets[left] & theory_sets[right] for index, left in enumerate(selected) for right in list(selected)[index + 1 :]):
        raise RuntimeError("v7 theory identities overlap across panels")
    public: dict[str, list[Mapping[str, Any]]] = {}
    authorities: dict[str, list[Mapping[str, Any]]] = {}
    for stage, rows in selected.items():
        public[stage], authorities[stage] = [], []
        for index, item in enumerate(rows):
            question, control = item["question"], item["control_question"]
            verified, irrelevant = str(item["verified_certificate"]), str(item["irrelevant_certificate"])
            task_id = f"pwgs-v7-{stage}-{index:03d}"
            public[stage].append({"task_id": task_id, "split": stage, "source_theory_id": item["theory_id"], "source_question_id": item["question_id"], "control_source_question_id": item["control_question_id"], "proof_depth": int(question["QDep"]), "certificate_shape": list(item["shape"]), "prompt_no_state": _prompt(str(item["theory"]), str(question["question"]), None), "prompt_verified_state": _prompt(str(item["theory"]), str(question["question"]), verified), "prompt_irrelevant_state": _prompt(str(item["theory"]), str(question["question"]), irrelevant), "verified_certificate": verified, "irrelevant_certificate": irrelevant, "verified_certificate_sha256": digest(verified), "irrelevant_certificate_sha256": digest(irrelevant)})
            authorities[stage].append({"task_id": task_id, "answer": "A" if question["answer"] else "B"})
    protocol_body = {"version": VERSION, "prior_constraint": "v6 opaque proof-reference states had no usable effect, so v7 tests natural-language grounding with a valid query-irrelevant certificate control", "research_question": "Does a solver-verified, grounded natural-language derivation certificate supplied at inference improve ProofWriter A/B prediction beyond an equally structured valid certificate for an unrelated conclusion from the same theory?", "model": {"primary": "qwen2p5_3b", "allowed_parameter_class": "3B", "transport_model": "qwen3_1p7b"}, "intervention": {"kind": "inference_time_grounded_solver_certificate", "primary_control": "same-shape valid query-irrelevant certificate", "label_exposure": "forbidden", "training": False}, "scoring": {"interface": "direct next-token likelihood", "labels": {"A": "entailed", "B": "contradicted"}, "free_text_generation": False}, "panels": {stage: {"n": len(rows), "depth": STAGES[stage][1], "balanced": True} for stage, rows in public.items()}, "gates": {"base_qualification": {"n": 32, "correct_inclusive": [8, 24], "arm": "no_state"}, "positive_control": {"n": 96, "primary_comparison": "verified_state_minus_irrelevant_state", "minimum_correct_gain": 6, "exact_two_sided_mcnemar_p": 0.05, "verified_must_not_score_below_no_state": True}, "prospective": {"n": 192, "primary_comparison": "verified_state_minus_irrelevant_state", "exact_two_sided_mcnemar_p": 0.05, "boundary_aware_paired_lower_bound_above_zero": True, "verified_must_not_score_below_no_state": True}}, "execution_policy": {"construction_attempts": 1, "audit_attempts": 1, "training_attempts": 0, "base_qualification_attempts": 1, "positive_control_attempts": 1, "prospective_attempts": 1, "automatic_restarts_authorized": 0, "automatic_successors_authorized": 0}, "interpretive_boundary": "A success identifies a system-level grounded explicit-state/verification effect in this task envelope, not a learned-representation effect or a universal repairability law."}
    protocol = {**protocol_body, "protocol_id": _digest(protocol_body)}
    for stage, rows in public.items():
        _write_jsonl_new(data / f"public/{stage}.jsonl", rows)
        _write_jsonl_new(data / f"sealed/{stage}-authority.jsonl", authorities[stage])
    _write_new(data / "public/protocol.json", protocol)
    seal_body = {"version": VERSION, "archive_sha256": ARCHIVE_SHA256, "excluded_prior_theory_count": len(excluded), "protocol_id": protocol["protocol_id"], "protocol_sha256": _sha256(data / "public/protocol.json"), "panels": {stage: {"public_path": f"data/cognitive_core/repairability_proofwriter_grounded_state_v7/public/{stage}.jsonl", "public_sha256": _sha256(data / f"public/{stage}.jsonl"), "authority_path": f"data/cognitive_core/repairability_proofwriter_grounded_state_v7/sealed/{stage}-authority.jsonl", "authority_sha256": _sha256(data / f"sealed/{stage}-authority.jsonl")} for stage in public}, "source_provenance": {"scripts/prepare_cognitive_repairability_proofwriter_grounded_state_v7.py": _sha256(project / "scripts/prepare_cognitive_repairability_proofwriter_grounded_state_v7.py"), "src/scientist/domains/cognitive_core/proofwriter_verified_trace_v4.py": _sha256(project / "src/scientist/domains/cognitive_core/proofwriter_verified_trace_v4.py")}}
    _write_new(data / "public/seal.json", {**seal_body, "seal_id": _digest(seal_body)})
    print(json.dumps({"status": "v7_grounded_certificate_panels_sealed_nonmodel", "panels": {stage: len(rows) for stage, rows in public.items()}, "model_calls": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
