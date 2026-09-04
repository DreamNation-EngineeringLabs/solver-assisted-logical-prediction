#!/usr/bin/env python3
"""Build the corrected b14-inclusive prepared release package."""
from __future__ import annotations

import argparse
import json
import os
import sys
import zipfile
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parent))
import package_cognitive_solver_assisted_public_release_v5 as release_v5


base = release_v5.base
VERSION = "solver-assisted-public-release-v6"
ARCHIVE_NAME = "solver_assisted_reasoning_release_v6.zip"
MANIFEST_NAME = "solver_assisted_reasoning_release_v6_manifest.json"
base.INCLUDE = (*base.INCLUDE, "scripts/package_cognitive_solver_assisted_public_release_v6.py")


def _readme() -> str:
    return release_v5._readme().replace("package v5", "package v6")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the b14-inclusive prepared release package.")
    parser.add_argument("--project", type=Path, default=Path("."))
    args = parser.parse_args()
    project = args.project.resolve()
    output_dir = project / base.OUTPUT_DIR
    archive, manifest_path = output_dir / ARCHIVE_NAME, output_dir / MANIFEST_NAME
    if archive.exists() or manifest_path.exists():
        raise RuntimeError("prepared release archive target already exists")
    entries = list(base._files(project))
    files = [
        {"path": str(path.relative_to(project)), "bytes": path.stat().st_size, "sha256": base._sha256(path)}
        for path in entries
    ]
    manifest_body: Mapping[str, Any] = {
        "version": VERSION,
        "archive": ARCHIVE_NAME,
        "file_count": len(files),
        "files": files,
        "claim_boundary": (
            "v7 is a system-level solver-assisted prediction pilot; b14 is a completed "
            "five-arm binary system-level factorial. Its primary proof-prefix-minus-"
            "conclusion-only contrast did not support an internal-state repair claim; "
            "v8/v9/v10 diagnose delivery and open-world competence boundaries."
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        bundle.writestr("README.md", _readme())
        bundle.writestr("MANIFEST.json", json.dumps({**manifest_body, "manifest_id": base._digest(manifest_body)}, ensure_ascii=True, indent=2, sort_keys=True) + "\n")
        for path in entries:
            bundle.write(path, arcname=str(path.relative_to(project)))
    archive_sha = base._sha256(archive)
    manifest = {
        **manifest_body,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": archive_sha,
        "manifest_id": base._digest({**manifest_body, "archive_sha256": archive_sha}),
    }
    descriptor = os.open(manifest_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True).encode("utf-8") + b"\n")
        handle.flush()
        os.fsync(handle.fileno())
    print(json.dumps({"archive": str(archive), "manifest": str(manifest_path), "file_count": len(files), "archive_sha256": archive_sha}, sort_keys=True))


if __name__ == "__main__":
    main()
