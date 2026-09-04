#!/usr/bin/env python3
"""Build the final manuscript-aligned public artifact archive without altering v1."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import package_cognitive_solver_assisted_public_release_v1 as base


base.VERSION = "solver-assisted-public-release-v2"
base.ARCHIVE_NAME = "solver_assisted_reasoning_release_v2.zip"
base.MANIFEST_NAME = "solver_assisted_reasoning_release_v2_manifest.json"
base.INCLUDE = (*base.INCLUDE, "scripts/package_cognitive_solver_assisted_public_release_v2.py", "manuscript/grounded_state_repair_preprint_v1/build_preprint_pdf.py", "output/pdf/solver_assisted_logical_prediction_audit_preprint.pdf")
_prior_readme = base._readme
base._readme = lambda: _prior_readme().replace("public release v1", "public release v2")


if __name__ == "__main__":
    base.main()
