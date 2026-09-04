#!/usr/bin/env python3
"""Run b14 through a single persistent local supervisor process."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import run_cognitive_binary_certificate_factorial_b11 as base


VERSION = "binary-certificate-factorial-b14"
DATA = Path("data/cognitive_core/binary_certificate_factorial_b14")
RUN = Path("runs/cognitive_core/binary_certificate_factorial_b14")
BOOTSTRAP_SEED = 2026090134
SCRIPT = "scripts/run_cognitive_binary_certificate_factorial_b14.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _configure() -> None:
    base.VERSION = VERSION
    base.DATA = DATA
    base.RUN = RUN
    base.BOOTSTRAP_SEED = BOOTSTRAP_SEED
    base.common.SYSTEM = base.SYSTEM
    base.common.BOOTSTRAP_SEED = BOOTSTRAP_SEED


def _implementation(project: Path) -> None:
    path = project / RUN / base.MODEL / "control/implementation.json"
    if not path.exists():
        body = {"version": VERSION, "runner": {"script": SCRIPT, "sha256": _sha256(Path(__file__).resolve())}, "transport": "persistent local supervisor process", "qualification_then_prospective": True, "automatic_restarts_authorized": 0, "automatic_successors_authorized": 0}
        base.common._write_new(path, {**body, "implementation_id": base.common._digest(body)})


def main() -> None:
    parser = argparse.ArgumentParser(description="Run b14 in a persistent local process.")
    parser.add_argument("stage", choices=("preflight", "qualify", "prospective", "all"))
    parser.add_argument("--project", type=Path, default=Path("."))
    args = parser.parse_args()
    project = args.project.resolve()
    _configure()
    _implementation(project)
    if args.stage == "preflight":
        print(json.dumps(base._preflight(project), sort_keys=True))
        return
    if args.stage in ("qualify", "all"):
        base._qualification(project)
    if args.stage in ("prospective", "all"):
        qualification = base._read(project / RUN / base.MODEL / "results/qualification.json")
        if qualification.get("prospective_authorized") is not True:
            print(json.dumps({"status": "prospective_not_authorized_after_qualification", "qualified": False}, sort_keys=True))
            return
        base._prospective(project)


if __name__ == "__main__":
    main()
