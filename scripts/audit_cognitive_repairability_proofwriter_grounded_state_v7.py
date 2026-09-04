#!/usr/bin/env python3
"""Independent non-model audit of the v7 grounded-certificate package."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import zipfile
from pathlib import Path
from typing import Any, Iterable, Mapping

from scientist.domains.cognitive_core.proofwriter_verified_trace_v4 import target_atom, verify_record_question


VERSION = "cognitive-repairability-proofwriter-grounded-state-v7"
ARCHIVE = Path("third_party/proofwriter/proofwriter-dataset-V2020.12.3.zip")
ARCHIVE_SHA256 = "bbc5694901e8306d0bd659aa1ad53ccfd02c201864f4b320ffa3777827d1fc26"
ROOT = "proofwriter-dataset-V2020.12.3/"
DATA = Path("data/cognitive_core/repairability_proofwriter_grounded_state_v7")
RUN = Path("runs/cognitive_core/repairability_proofwriter_grounded_state_v7")
OLD_DATA = (Path("data/cognitive_core/repairability_proofwriter_hidden_state_v4"), Path("data/cognitive_core/repairability_proofwriter_explicit_state_v6"))
PREPARER = "scripts/prepare_cognitive_repairability_proofwriter_grounded_state_v7.py"
FILE = "scripts/audit_cognitive_repairability_proofwriter_grounded_state_v7.py"
STAGES = {"base_qualification": ("OWA/depth-3/meta-train.jsonl", 32, 3), "positive_control": ("OWA/depth-3/meta-test.jsonl", 96, 3), "prospective": ("OWA/depth-5/meta-train.jsonl", 192, 4)}


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def _rows(path: Path) -> list[Mapping[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _write_new(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())


def _terminal(project: Path, status: str, error: Exception | None = None) -> None:
    path = project / RUN / "control/terminal.json"
    if path.exists():
        return
    body: dict[str, Any] = {"version": VERSION, "stage": "nonmodel-grounded-certificate-audit", "status": status, "automatic_restarts_authorized": 0, "automatic_successors_authorized": 0}
    if error is not None:
        body.update(error_type=type(error).__name__, error=str(error)[:500])
    _write_new(path, {**body, "terminal_id": _digest(body)})


def _archive_rows(archive: zipfile.ZipFile, member: str) -> Iterable[Mapping[str, Any]]:
    with archive.open(ROOT + member) as handle:
        for line in handle:
            value = json.loads(line)
            if not isinstance(value, Mapping):
                raise RuntimeError("archive row is not an object")
            yield value


def _certificate(record: Mapping[str, Any], question: Mapping[str, Any]) -> tuple[str, tuple[str, ...]]:
    trace, _ = verify_record_question(record, question)
    refs: list[str] = []
    for kind, digits in re.findall(r"\b([FRI])(\d{2})\b", trace):
        ref = kind + digits
        if ref not in refs:
            refs.append(ref)
    triples, rules = record.get("triples"), record.get("rules")
    options = question.get("proofsWithIntermediates")
    if not isinstance(triples, Mapping) or not isinstance(rules, Mapping) or not isinstance(options, list) or not options or not isinstance(options[0], Mapping):
        raise RuntimeError("certificate source is malformed")
    intermediate = options[0].get("intermediates")
    if not isinstance(intermediate, Mapping):
        raise RuntimeError("certificate intermediates are malformed")
    lines, shape = ["Solver-verified derivation certificate (no answer label):"], []
    for ref in refs:
        kind, number = ref[0], int(ref[1:])
        source: Any = triples.get(f"triple{number}") if kind == "F" else rules.get(f"rule{number}") if kind == "R" else intermediate.get(f"int{number}")
        if not isinstance(source, Mapping) or not isinstance(source.get("text"), str):
            raise RuntimeError("certificate reference is unresolved")
        lines.append(f"[{ref}] {source['text']}")
        shape.append(kind)
    value = "\n".join(lines)
    if "F" not in shape or "R" not in shape or re.search(r"\b(?:A|B|entailed|contradicted)\b", value, flags=re.IGNORECASE):
        raise RuntimeError("certificate structure or label exclusion failed")
    return value, tuple(shape)


def _old_theories(project: Path) -> frozenset[str]:
    values: set[str] = set()
    for root in OLD_DATA:
        for path in sorted((project / root / "public").glob("*.jsonl")):
            for row in _rows(path):
                if "source_theory_id" in row:
                    values.add(str(row["source_theory_id"]))
    if not values:
        raise RuntimeError("prior theory manifests are missing")
    return frozenset(values)


def _prompt_check(row: Mapping[str, Any]) -> None:
    verified, irrelevant = str(row["verified_certificate"]), str(row["irrelevant_certificate"])
    none, real, control = str(row["prompt_no_state"]), str(row["prompt_verified_state"]), str(row["prompt_irrelevant_state"])
    if verified in none or irrelevant in none or real.count(verified) != 1 or control.count(irrelevant) != 1 or irrelevant in real or verified in control:
        raise RuntimeError("certificate prompt incorporation is invalid")
    if not all("A = entailed. B = contradicted.\nAnswer:" in prompt for prompt in (none, real, control)):
        raise RuntimeError("direct A/B interface differs")


def _audit_panel(project: Path, archive: zipfile.ZipFile, seal: Mapping[str, Any], stage: str, member: str, n: int, depth: int, forbidden: frozenset[str]) -> Mapping[str, Any]:
    panel = seal.get("panels", {}).get(stage, {})
    public_path, authority_path = project / str(panel.get("public_path", "")), project / str(panel.get("authority_path", ""))
    if _sha256(public_path) != panel.get("public_sha256") or _sha256(authority_path) != panel.get("authority_sha256"):
        raise RuntimeError(f"{stage} panel hash differs from seal")
    public, authority = _rows(public_path), _rows(authority_path)
    answer = {str(row["task_id"]): str(row["answer"]) for row in authority}
    if len(public) != n or len(answer) != n or {str(row["task_id"]) for row in public} != set(answer) or sum(value == "A" for value in answer.values()) != n // 2:
        raise RuntimeError(f"{stage} panel identities or balance are invalid")
    source: dict[tuple[str, str], tuple[Mapping[str, Any], Mapping[str, Any]]] = {}
    for record in _archive_rows(archive, member):
        theory_id, questions = record.get("id"), record.get("questions")
        if isinstance(theory_id, str) and isinstance(questions, Mapping):
            for question_id, question in questions.items():
                if isinstance(question_id, str) and isinstance(question, Mapping):
                    source[(theory_id, question_id)] = (record, question)
    theories: set[str] = set()
    digest_pairs = []
    for row in public:
        task_id, theory_id, qid, donor_id = str(row["task_id"]), str(row["source_theory_id"]), str(row["source_question_id"]), str(row["control_source_question_id"])
        theories.add(theory_id)
        if theory_id in forbidden or int(row["proof_depth"]) != depth:
            raise RuntimeError(f"{stage} uses a prior theory or wrong depth")
        record, question = source.get((theory_id, qid), (None, None))
        donor_record, donor = source.get((theory_id, donor_id), (None, None))
        if record is None or question is None or donor_record is None or donor is None:
            raise RuntimeError(f"{stage} selected source question is absent")
        verified, shape = _certificate(record, question)
        irrelevant, donor_shape = _certificate(donor_record, donor)
        if str(row["verified_certificate"]) != verified or str(row["irrelevant_certificate"]) != irrelevant or tuple(row["certificate_shape"]) != shape or shape != donor_shape:
            raise RuntimeError(f"{stage} certificates differ from independent regeneration")
        if target_atom(question) == target_atom(donor):
            raise RuntimeError(f"{stage} control certificate proves the query target")
        if str(row["verified_certificate_sha256"]) != hashlib.sha256(verified.encode()).hexdigest() or str(row["irrelevant_certificate_sha256"]) != hashlib.sha256(irrelevant.encode()).hexdigest():
            raise RuntimeError(f"{stage} certificate digest differs")
        _prompt_check(row)
        expected = "A" if question.get("answer") is True else "B"
        if answer[task_id] != expected:
            raise RuntimeError(f"{stage} authority differs from source answer")
        digest_pairs.append((hashlib.sha256(verified.encode()).hexdigest(), hashlib.sha256(irrelevant.encode()).hexdigest()))
    return {"n": n, "proof_depth": depth, "theory_count": len(theories), "answer_balance": {"A": sum(value == "A" for value in answer.values()), "B": sum(value == "B" for value in answer.values())}, "certificate_pair_digest": _digest(digest_pairs), "checks": {"target_and_intermediate_proofs_regenerated": True, "both_certificates_solver_valid": True, "control_target_differs_from_query_target": True, "certificate_shapes_identical": True, "certificate_answer_labels_excluded": True, "direct_interface_identical": True}}


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit v7 grounded ProofWriter certificates without a model.")
    parser.add_argument("--project", type=Path, default=Path("."))
    args = parser.parse_args()
    project, data, run = args.project.resolve(), args.project.resolve() / DATA, args.project.resolve() / RUN
    try:
        if run.exists():
            raise RuntimeError("v7 audit output path already exists")
        archive = project / ARCHIVE
        if not archive.is_file() or _sha256(archive) != ARCHIVE_SHA256:
            raise RuntimeError("official archive is unavailable or changed")
        seal, protocol = _read(data / "public/seal.json"), _read(data / "public/protocol.json")
        if seal.get("version") != VERSION or protocol.get("version") != VERSION or seal.get("protocol_id") != protocol.get("protocol_id") or _sha256(data / "public/protocol.json") != seal.get("protocol_sha256"):
            raise RuntimeError("v7 protocol/seal identity mismatch")
        if seal.get("source_provenance", {}).get(PREPARER) != _sha256(project / PREPARER):
            raise RuntimeError("v7 preparer changed after sealing")
        forbidden = _old_theories(project)
        with zipfile.ZipFile(archive) as bundle:
            if bundle.testzip() is not None:
                raise RuntimeError("archive integrity failure")
            panels = {stage: _audit_panel(project, bundle, seal, stage, member, n, depth, forbidden) for stage, (member, n, depth) in STAGES.items()}
        sets = {stage: {str(row["source_theory_id"]) for row in _rows(project / str(seal["panels"][stage]["public_path"]))} for stage in STAGES}
        overlap = {f"{left}|{right}": sorted(sets[left] & sets[right]) for index, left in enumerate(STAGES) for right in list(STAGES)[index + 1 :]}
        if any(overlap.values()):
            raise RuntimeError("v7 theory identities overlap across panels")
        body = {"version": VERSION, "status": "grounded_certificate_source_and_delivery_preflight_qualified_nonmodel", "protocol_id": protocol["protocol_id"], "seal_id": seal["seal_id"], "archive_sha256": ARCHIVE_SHA256, "panels": panels, "prior_theory_exclusion": {"excluded_count": len(forbidden), "overlap": overlap, "all_v7_theories_fresh": True}, "source_sha256": {PREPARER: _sha256(project / PREPARER), FILE: _sha256(project / FILE)}, "benchmark_items_scored": 0, "model_calls": 0, "next_authorized_action": "one_frozen_base_qualification_only", "automatic_restarts_authorized": 0}
        certificate = {**body, "certificate_id": _digest(body)}
        _write_new(run / "preflight/nonmodel-certificate.json", certificate)
        auth = {"version": VERSION, "status": "one_base_qualification_authorized", "certificate_id": certificate["certificate_id"], "base_qualification_attempts": 1, "positive_control_attempts": 0, "prospective_attempts": 0, "automatic_restarts_authorized": 0, "automatic_successors_authorized": 0}
        _write_new(run / "control/authorization.json", {**auth, "authorization_id": _digest(auth)})
        print(json.dumps({"status": certificate["status"], "panels": {stage: value["n"] for stage, value in panels.items()}, "model_calls": 0}, sort_keys=True))
    except Exception as error:
        _terminal(project, "grounded_certificate_source_or_delivery_preflight_not_qualified_terminal", error)
        raise


if __name__ == "__main__":
    main()
