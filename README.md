# Solver-assisted logical prediction: paper code v1

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
