#!/usr/bin/env python3
"""Run the sealed-panel scorers on Modal GPUs.

Infrastructure, not an experiment. It shells out to the existing versioned
runner rather than reimplementing scoring, so the frozen script stays frozen and
the receipts are produced by exactly the code that produced b19's.

What crosses the network: the *public* panel (items + seal), models.toml, the
runner, and cc_instruments. The sealed answer authority is never uploaded --
the runners never read it, and it stays on the local machine by construction.

    pip install modal && modal setup
    modal run scripts/modal_app.py::score --key qwen2p5_3b            # validate
    modal run scripts/modal_app.py::score --key qwen3_32b  --gpu H100
    modal run scripts/modal_app.py::score --key llama3p3_70b --gpu "H100:2"
    modal volume get cc-receipts / ./runs/cognitive_core/_modal

Weights land in a persistent Volume, so a 141 GB checkpoint downloads once
across every later invocation.
"""
from __future__ import annotations
import pathlib
import modal

PROJECT = pathlib.Path(__file__).resolve().parents[1]
ROOT = PROJECT.parent                      # cognitive-core/, for shared-instruments
RUNNER = "scripts/run_multimodel_three_class_b19_cuda.py"

app = modal.App("cognitive-core-scoring")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("torch", "transformers", "huggingface_hub[hf_transfer]",
                 "accelerate", "safetensors", "sentencepiece")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1", "HF_HOME": "/cache/hf"})
    # public panel only: sealed/ is deliberately not uploaded
    .add_local_dir(PROJECT / "data/cognitive_core/multimodel_three_class_b16/public",
                   "/work/data/cognitive_core/multimodel_three_class_b16/public")
    .add_local_dir(PROJECT / "data/cognitive_core/binary_certificate_factorial_b15/public",
                   "/work/data/cognitive_core/binary_certificate_factorial_b15/public")
    .add_local_dir(ROOT / "shared-instruments/src/cc_instruments", "/work/cc_instruments")
    .add_local_dir(PROJECT / "scripts", "/work/scripts")
    .add_local_file(PROJECT / "models.toml", "/work/models.toml")
)

hf_cache = modal.Volume.from_name("hf-cache", create_if_missing=True)
receipts = modal.Volume.from_name("cc-receipts", create_if_missing=True)


# No Modal Secret is declared: every repo we score has an ungated path, which
# follows the b19 convention ("ungated mirror of a gated upstream repo"). A
# gated repo would need a token forwarded here as an ephemeral secret.
@app.function(image=image, volumes={"/cache": hf_cache, "/out": receipts},
              timeout=60 * 60 * 6)
def _score(key: str, runner: str, extra: list[str]) -> str:
    """Run one model's sweep inside the container and persist its receipts."""
    import os, shutil, subprocess, sys
    os.environ["PYTHONPATH"] = "/work"
    cmd = [sys.executable, f"/work/{runner}", "--project", "/work",
           "--key", key, "--keep-weights", *extra]
    print("$", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd="/work")
    hf_cache.commit()                       # keep the weights for the next call
    if r.returncode != 0:
        raise RuntimeError(f"{key}: runner exited {r.returncode}")

    produced = pathlib.Path("/work/runs")
    if not produced.exists():
        raise RuntimeError(f"{key}: runner wrote no runs/ directory")
    for src in produced.rglob("*"):
        if src.is_file():
            dst = pathlib.Path("/out") / src.relative_to(produced)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    receipts.commit()
    return f"{key}: receipts committed to the cc-receipts volume"


@app.local_entrypoint()
def score(key: str, gpu: str = "H100", runner: str = RUNNER, extra: str = "") -> None:
    """`modal run scripts/modal_app.py::score --key <model> [--gpu H100:2]`"""
    fn = _score.with_options(gpu=gpu)
    print(fn.remote(key, runner, [x for x in extra.split() if x]))
