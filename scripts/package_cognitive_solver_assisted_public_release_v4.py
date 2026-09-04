#!/usr/bin/env python3
"""Build the final v4 prepared release package after the manuscript revision."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import package_cognitive_solver_assisted_public_release_v3 as release_v3


base = release_v3.base
base.VERSION = "solver-assisted-public-release-v4"
base.ARCHIVE_NAME = "solver_assisted_reasoning_release_v4.zip"
base.MANIFEST_NAME = "solver_assisted_reasoning_release_v4_manifest.json"
base.INCLUDE = (*base.INCLUDE, "scripts/package_cognitive_solver_assisted_public_release_v4.py")
base._readme = lambda: release_v3._readme().replace("package v3", "package v4")


if __name__ == "__main__":
    base.main()
