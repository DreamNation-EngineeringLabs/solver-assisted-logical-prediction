#!/usr/bin/env python3
"""Build a hash-addressed public artifact archive for the solver-assisted pilot."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import zipfile
from pathlib import Path
from typing import Any, Iterable, Mapping


VERSION = "solver-assisted-public-release-v1"
OUTPUT_DIR = Path("output/reproducibility")
ARCHIVE_NAME = "solver_assisted_reasoning_release_v1.zip"
MANIFEST_NAME = "solver_assisted_reasoning_release_v1_manifest.json"
INCLUDE = (
    "data/cognitive_core/repairability_proofwriter_grounded_state_v7",
    "runs/cognitive_core/repairability_proofwriter_grounded_state_v7",
    "artifacts/solver_assisted_v7_publication_analysis/v7_paired_analysis.json",
    "data/cognitive_core/solver_assisted_certificate_factorial_v8",
    "runs/cognitive_core/solver_assisted_certificate_factorial_v8/qwen2p5_3b",
    "runs/cognitive_core/semantic_three_way_interface_v9/qwen2p5_3b",
    "scripts/prepare_cognitive_repairability_proofwriter_grounded_state_v7.py",
    "scripts/audit_cognitive_repairability_proofwriter_grounded_state_v7.py",
    "scripts/score_cognitive_repairability_proofwriter_grounded_state_base_v7.py",
    "scripts/score_cognitive_repairability_proofwriter_grounded_state_positive_v7.py",
    "scripts/score_cognitive_repairability_proofwriter_grounded_state_prospective_v7.py",
    "scripts/audit_cognitive_solver_assisted_v7_publication.py",
    "scripts/prepare_cognitive_solver_assisted_certificate_factorial_v8.py",
    "scripts/run_cognitive_solver_assisted_certificate_factorial_v8.py",
    "scripts/qualify_cognitive_semantic_three_way_interface_v9.py",
    "scripts/package_cognitive_solver_assisted_public_release_v1.py",
    "src/scientist/domains/cognitive_core/proofwriter_verified_trace_v4.py",
    "docs/cognitive-core/repairability-grounded-state-design-v7.md",
    "docs/cognitive-core/solver_assisted_certificate_factorial_design_v8.md",
    "manuscript/grounded_state_repair_preprint_v1/manuscript.md",
    "manuscript/grounded_state_repair_preprint_v1/references.bib",
)


def _sha256(path: Path) -> str:
    block = hashlib.sha256()
    with path.open("rb") as handle:
        for payload in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            block.update(payload)
    return block.hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _files(project: Path) -> Iterable[Path]:
    for relative in INCLUDE:
        path = project / relative
        if not path.exists():
            raise RuntimeError(f"required release path is missing: {relative}")
        if path.is_file():
            yield path
        else:
            yield from sorted(item for item in path.rglob("*") if item.is_file() and "__pycache__" not in item.parts)


def _readme() -> str:
    return """# Solver-assisted reasoning public release v1

## What this archive supports

The sealed ProofWriter v7 pilot supports a system-level finding: a
query-relevant solver certificate improved Qwen2.5-3B direct forced-choice
accuracy relative to a valid query-irrelevant certificate. It does not show
that the model used intermediate proof state or repaired its own reasoning.

The archive includes the completed v7 pilot, a standard paired reanalysis, and
two later delivery/competence diagnostics. The v8 arbitrary-label screen failed
for Qwen2.5-3B. A separate semantic-token screen was consistent across two
templates but scored 0/12 on open-world unknown items. The planned three-way
factorial was therefore not opened. Neither failed qualification is a treatment
null.

## Reproduction map

- `data/...grounded_state_v7/`: sealed v7 panels, answer authorities, prompts,
  certificates, and SHA-256 seal.
- `runs/...grounded_state_v7/`: gate records and per-item A/B likelihood
  receipts for all primary arms.
- `scripts/audit_cognitive_solver_assisted_v7_publication.py`: recomputes the
  paired 2x2 tables, exact McNemar p values, and seeded paired BCa intervals.
- `artifacts/.../v7_paired_analysis.json`: immutable publication-facing output
  from that analysis.
- `data/...factorial_v8/`, `runs/...factorial_v8/`, and
  `runs/...semantic_three_way_interface_v9/`: separately sealed follow-up
  diagnostics and their terminal records.

All files are enumerated and SHA-256 hashed in the adjacent manifest. The
ProofWriter source archive itself is not redistributed here; its official
archive hash and the regenerated selected panels are recorded in the v7 seal.
Review its licence before redistribution or derivative release.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Create one immutable solver-assisted public release archive.")
    parser.add_argument("--project", type=Path, default=Path("."))
    args = parser.parse_args()
    project = args.project.resolve()
    output_dir = project / OUTPUT_DIR
    archive, manifest_path = output_dir / ARCHIVE_NAME, output_dir / MANIFEST_NAME
    if archive.exists() or manifest_path.exists():
        raise RuntimeError("public release archive target already exists")
    entries = list(_files(project))
    files = [{"path": str(path.relative_to(project)), "bytes": path.stat().st_size, "sha256": _sha256(path)} for path in entries]
    manifest_body: Mapping[str, Any] = {"version": VERSION, "archive": ARCHIVE_NAME, "file_count": len(files), "files": files, "claim_boundary": "v7 is a system-level solver-assisted prediction pilot; v8/v9 diagnose delivery and open-world unknown competence boundaries; no factorial mechanism result is claimed."}
    output_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        bundle.writestr("README.md", _readme())
        bundle.writestr("MANIFEST.json", json.dumps({**manifest_body, "manifest_id": _digest(manifest_body)}, ensure_ascii=True, indent=2, sort_keys=True) + "\n")
        for path in entries:
            bundle.write(path, arcname=str(path.relative_to(project)))
    archive_sha = _sha256(archive)
    manifest = {**manifest_body, "archive_bytes": archive.stat().st_size, "archive_sha256": archive_sha, "manifest_id": _digest({**manifest_body, "archive_sha256": archive_sha})}
    descriptor = os.open(manifest_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True).encode("utf-8") + b"\n")
        handle.flush()
        os.fsync(handle.fileno())
    print(json.dumps({"archive": str(archive), "manifest": str(manifest_path), "file_count": len(files), "archive_sha256": archive_sha}, sort_keys=True))


if __name__ == "__main__":
    main()
