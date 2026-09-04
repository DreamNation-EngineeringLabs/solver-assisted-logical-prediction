#!/usr/bin/env python3
"""Build the manuscript-aligned v3 local release package without altering prior archives."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import package_cognitive_solver_assisted_public_release_v1 as base


base.VERSION = "solver-assisted-public-release-v3"
base.ARCHIVE_NAME = "solver_assisted_reasoning_release_v3.zip"
base.MANIFEST_NAME = "solver_assisted_reasoning_release_v3_manifest.json"
base.INCLUDE = (
    *base.INCLUDE,
    "data/cognitive_core/solver_assisted_certificate_factorial_v10",
    "runs/cognitive_core/solver_assisted_certificate_factorial_v10/qwen3_1p7b",
    "scripts/prepare_cognitive_solver_assisted_certificate_factorial_v10.py",
    "scripts/run_cognitive_solver_assisted_certificate_factorial_v10.py",
    "scripts/package_cognitive_solver_assisted_public_release_v2.py",
    "scripts/package_cognitive_solver_assisted_public_release_v3.py",
    "docs/cognitive-core/solver_assisted_certificate_factorial_design_v10.md",
    "manuscript/grounded_state_repair_preprint_v1/build_preprint_pdf.py",
    "output/pdf/solver_assisted_logical_prediction_audit_preprint.pdf",
)


def _readme() -> str:
    return """# Solver-assisted reasoning prepared release package v3

## Scope and claim boundary

The sealed ProofWriter v7 pilot supports a system-level finding: a
query-relevant solver certificate improved Qwen2.5-3B forced-choice output
relative to a valid query-irrelevant certificate. It does not establish that
the model used intermediate proof state or repaired its own reasoning.

The planned five-arm mechanism experiment was not run. Qwen2.5-3B failed the
v8 arbitrary-label and v9 open-world-unknown delivery/competence gates. The
single Qwen3-1.7B v8 qualification ended before scoring because of an MLX
bfloat16-to-NumPy conversion error; its fresh v10 successor used a distinct
sealed panel and a documented conversion fix, then failed semantic mapping
qualification (12/36 under each map and 0/36 agreement). No prospective
factorial authority was opened. These are terminal qualification records, not
treatment nulls.

## Included materials

- sealed v7 pilot panels, authorities, prompts, certificate arms, likelihood
  receipts, model/runtime freezes, and post hoc paired reanalysis;
- sealed v8 and v10 factorial public panels, authorities, protocols, source,
  preflights, qualification receipts, and terminal records;
- v9 semantic-token diagnostic source, receipts, and terminal record;
- manuscript source, bibliography, PDF builder, and rendered preprint;
- a hash manifest embedded in this archive and an adjacent hash manifest.

This is a prepared local release package. It has not been publicly posted and
does not have a DOI. Review ProofWriter and derivative-data licence terms
before public redistribution.
"""


base._readme = _readme


if __name__ == "__main__":
    base.main()
