#!/usr/bin/env python3
"""Build the manuscript-aligned prepared release package including b14."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import package_cognitive_solver_assisted_public_release_v4 as release_v4


base = release_v4.base
base.VERSION = "solver-assisted-public-release-v5"
base.ARCHIVE_NAME = "solver_assisted_reasoning_release_v5.zip"
base.MANIFEST_NAME = "solver_assisted_reasoning_release_v5_manifest.json"
base.INCLUDE = (
    *base.INCLUDE,
    "data/cognitive_core/binary_certificate_factorial_b14",
    "runs/cognitive_core/binary_certificate_factorial_b14/qwen2p5_3b",
    "scripts/prepare_cognitive_binary_certificate_factorial_b11.py",
    "scripts/run_cognitive_binary_certificate_factorial_b11.py",
    "scripts/prepare_cognitive_binary_certificate_factorial_b12.py",
    "scripts/run_cognitive_binary_certificate_factorial_b12.py",
    "scripts/prepare_cognitive_binary_certificate_factorial_b13.py",
    "scripts/run_cognitive_binary_certificate_factorial_b13.py",
    "scripts/prepare_cognitive_binary_certificate_factorial_b14.py",
    "scripts/run_cognitive_binary_certificate_factorial_b14.py",
    "scripts/audit_cognitive_binary_certificate_factorial_b14.py",
    "scripts/package_cognitive_solver_assisted_public_release_v5.py",
    "docs/cognitive-core/binary_certificate_factorial_b11.md",
    "docs/cognitive-core/binary_certificate_factorial_b12.md",
    "docs/cognitive-core/binary_certificate_factorial_b14.md",
)


def _readme() -> str:
    return """# Solver-assisted reasoning prepared release package v5

## Scope and claim boundary

The sealed ProofWriter v7 pilot supports a system-level finding: a
query-relevant solver certificate improved Qwen2.5-3B forced-choice output
relative to a valid query-irrelevant certificate. It does not establish that
the model used intermediate proof state or repaired its own reasoning.

The completed b14 study is a fresh **five-arm binary factorial**: no
certificate, irrelevant proof, conclusion only, proof prefix with the terminal
literal omitted, and full proof. Qwen2.5-3B passed its direct Yes/No delivery
gate before one 192-item prospective execution. The prespecified primary
prefix-minus-conclusion-only contrast was -9/192 (exact McNemar p=0.078), so
the archive does not support a claim that proof prefix exceeds direct
conclusion evidence. Prefix-minus-irrelevant was +71/192 and
full-minus-conclusion-only was +15/192; these are limited system-level effects
of query-relevant solver material in a binary synthetic task.

The v8/v9/v10 three-class diagnostics are retained as terminal records. They
are not treatment nulls and are not replications of b14.

## Included materials

- sealed v7 pilot panels, authorities, prompts, certificate arms, likelihood
  receipts, model/runtime freezes, and post hoc paired reanalysis;
- sealed v8/v9/v10 diagnostic panels, protocols, receipts, and terminal
  records;
- sealed b14 public and authority panels, protocol and seal, code freezes,
  direct Yes/No qualification, all 960 prospective likelihood receipts,
  terminal result, and a no-model audit script;
- manuscript source, bibliography, PDF builder, rendered preprint, and the
  hash manifest embedded in this archive and adjacent to it.

This is a prepared local release package. It has not been publicly posted and
does not have a DOI. Review source-data and derivative-data licence terms
before public redistribution.
"""


base._readme = _readme


if __name__ == "__main__":
    base.main()
