#!/usr/bin/env python3
"""Create a code-only publication bundle for the solver-assisted paper."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import zipfile
from pathlib import Path
from typing import Any, Iterable, Mapping


VERSION = "solver-assisted-paper-code-v1"
OUTPUT_DIR = Path("output/reproducibility")
ARCHIVE_NAME = "solver_assisted_logical_prediction_paper_code_v1.zip"
MANIFEST_NAME = "solver_assisted_logical_prediction_paper_code_v1_manifest.json"
INCLUDE = (
    "manuscript/grounded_state_repair_preprint_v1/manuscript.md",
    "manuscript/grounded_state_repair_preprint_v1/references.bib",
    "manuscript/grounded_state_repair_preprint_v1/build_preprint_pdf.py",
    "src/scientist/domains/cognitive_core/proofwriter_verified_trace_v4.py",
    "scripts/prepare_cognitive_repairability_proofwriter_grounded_state_v7.py",
    "scripts/audit_cognitive_repairability_proofwriter_grounded_state_v7.py",
    "scripts/score_cognitive_repairability_proofwriter_grounded_state_base_v7.py",
    "scripts/score_cognitive_repairability_proofwriter_grounded_state_positive_v7.py",
    "scripts/score_cognitive_repairability_proofwriter_grounded_state_prospective_v7.py",
    "scripts/audit_cognitive_solver_assisted_v7_publication.py",
    "scripts/prepare_cognitive_solver_assisted_certificate_factorial_v8.py",
    "scripts/run_cognitive_solver_assisted_certificate_factorial_v8.py",
    "scripts/qualify_cognitive_semantic_three_way_interface_v9.py",
    "scripts/prepare_cognitive_solver_assisted_certificate_factorial_v10.py",
    "scripts/run_cognitive_solver_assisted_certificate_factorial_v10.py",
    "scripts/prepare_cognitive_binary_certificate_factorial_b11.py",
    "scripts/run_cognitive_binary_certificate_factorial_b11.py",
    "scripts/prepare_cognitive_binary_certificate_factorial_b12.py",
    "scripts/run_cognitive_binary_certificate_factorial_b12.py",
    "scripts/prepare_cognitive_binary_certificate_factorial_b13.py",
    "scripts/run_cognitive_binary_certificate_factorial_b13.py",
    "scripts/prepare_cognitive_binary_certificate_factorial_b14.py",
    "scripts/run_cognitive_binary_certificate_factorial_b14.py",
    "scripts/audit_cognitive_binary_certificate_factorial_b14.py",
    "scripts/package_cognitive_solver_assisted_public_release_v1.py",
    "scripts/package_cognitive_solver_assisted_public_release_v2.py",
    "scripts/package_cognitive_solver_assisted_public_release_v3.py",
    "scripts/package_cognitive_solver_assisted_public_release_v4.py",
    "scripts/package_cognitive_solver_assisted_public_release_v5.py",
    "scripts/package_cognitive_solver_assisted_public_release_v6.py",
    "scripts/package_solver_assisted_paper_code_v1.py",
    "docs/cognitive-core/repairability-grounded-state-design-v7.md",
    "docs/cognitive-core/solver_assisted_certificate_factorial_design_v8.md",
    "docs/cognitive-core/solver_assisted_certificate_factorial_design_v10.md",
    "docs/cognitive-core/binary_certificate_factorial_b11.md",
    "docs/cognitive-core/binary_certificate_factorial_b12.md",
    "docs/cognitive-core/binary_certificate_factorial_b14.md",
)


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _files(project: Path) -> Iterable[Path]:
    for relative in INCLUDE:
        path = project / relative
        if not path.is_file():
            raise RuntimeError(f"required publication-code file is missing: {relative}")
        yield path


def _readme() -> str:
    return """# Solver-assisted logical prediction: paper code v1

This is a **code-only** companion to the preprint *Auditing Solver-Assisted
Logical Prediction with a Sealed Five-Arm Certificate Factorial*. It contains
the manuscript source and PDF builder; generators, runners, and audits for the
v7 ProofWriter pilot; the v8/v9/v10 qualification diagnostics; and the b11-
b14 binary certificate-factorial lineage, including the no-model b14 audit.

## What is intentionally not in this archive

This archive contains no model weights, raw prompts, answer authorities,
likelihood receipts, or derived results. Those materials are in the separately
prepared reproducibility package `solver_assisted_reasoning_release_v6.zip`.
Unpack both archives at the same project root to use the audit against the
sealed b14 artifacts.

## Minimal verification

The b14 audit makes no model calls and only needs the standard library:

```bash
PYTHONPATH=src:scripts python3 scripts/audit_cognitive_binary_certificate_factorial_b14.py --project .
```

It verifies b14 panel hashes, receipt digests and coverage, per-arm counts,
paired tables, paired risk differences, and exact McNemar p values.

## Rebuilding the PDF

The PDF builder requires `reportlab`:

```bash
python3 manuscript/grounded_state_repair_preprint_v1/build_preprint_pdf.py
```

The original model scoring environment was Python 3.12.13 with NumPy 2.5.1,
MLX 0.32.0, and mlx-lm 0.31.3. Weights are not redistributed; the b14 code
freeze records the intended local checkpoint revision and weight hash in the
separate artifacts package.

## Licence and scope

No publication licence is asserted by this prepared local bundle. Select and
add an explicit licence before public release. The paper makes system-level
claims only: b14 is a five-arm binary factorial, and its primary proof-prefix
minus conclusion-only contrast does not support an internal reasoning-repair
claim.
"""


def _requirements() -> str:
    return """# Publication-code dependencies\n# The b14 audit uses only Python's standard library.\n# The PDF builder additionally requires reportlab.\nreportlab\nnumpy==2.5.1\nmlx==0.32.0\nmlx-lm==0.31.3\n"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the solver-assisted paper's code-only publication archive.")
    parser.add_argument("--project", type=Path, default=Path("."))
    args = parser.parse_args()
    project = args.project.resolve()
    output_dir = project / OUTPUT_DIR
    archive, manifest_path = output_dir / ARCHIVE_NAME, output_dir / MANIFEST_NAME
    if archive.exists() or manifest_path.exists():
        raise RuntimeError("publication-code archive target already exists")
    entries = list(_files(project))
    files = [{"path": str(path.relative_to(project)), "bytes": path.stat().st_size, "sha256": _sha256(path)} for path in entries]
    manifest_body: Mapping[str, Any] = {
        "version": VERSION,
        "archive": ARCHIVE_NAME,
        "file_count": len(files),
        "files": files,
        "scope": "code-only companion; data, receipts, authorities, results, and model weights are excluded",
        "results_companion": "solver_assisted_reasoning_release_v6.zip",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        bundle.writestr("README.md", _readme())
        bundle.writestr("requirements-publication-code.txt", _requirements())
        bundle.writestr("MANIFEST.json", json.dumps({**manifest_body, "manifest_id": _digest(manifest_body)}, ensure_ascii=True, indent=2, sort_keys=True) + "\n")
        for path in entries:
            bundle.write(path, arcname=str(path.relative_to(project)))
    archive_sha = _sha256(archive)
    manifest = {
        **manifest_body,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": archive_sha,
        "manifest_id": _digest({**manifest_body, "archive_sha256": archive_sha}),
    }
    descriptor = os.open(manifest_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True).encode("utf-8") + b"\n")
        handle.flush()
        os.fsync(handle.fileno())
    print(json.dumps({"archive": str(archive), "manifest": str(manifest_path), "file_count": len(files), "archive_sha256": archive_sha}, sort_keys=True))


if __name__ == "__main__":
    main()
