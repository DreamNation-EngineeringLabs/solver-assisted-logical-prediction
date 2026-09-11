#!/usr/bin/env python3
"""b20 diagnostic — what does Qwen3-32B actually want to say at `Answer:`?

Qwen3-32B fails the viability floor under `full` while clearing it on three
other arms. That is either a real degradation, the same shape Qwen2.5-7B shows,
or an artefact of scoring a hybrid thinking model with no chat template. The
forced choice between `Yes` and `No` cannot tell the two apart, because it never
looks at what the model would have emitted unprompted.

This prints the unconstrained top-k at the answer position. If the argmax is
`Yes` or `No`, the forced choice is reading the model's actual intent and the
collapse is a finding. If it is a thinking marker or whitespace, the prompt
format is wrong for this checkpoint and the arm should not be reported.

Writes results/b20_qwen3_answer_position.json. No receipts: this is a diagnostic
about prompt format, not a scored arm.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

DATA = Path("data/cognitive_core/binary_certificate_factorial_b15")
OUT = Path("results/b20_qwen3_answer_position.json")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", type=Path, default=Path("."))
    ap.add_argument("--repo", default="Qwen/Qwen3-32B")
    ap.add_argument("--revision", default="9216db5781bf21249d130ec9da846c4624c16137")
    ap.add_argument("--items", type=int, default=12)
    ap.add_argument("--topk", type=int, default=5)
    # accepted for launcher compatibility; this script selects its own model
    ap.add_argument("--key", default=None)
    ap.add_argument("--keep-weights", action="store_true")
    a = ap.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from cc_instruments import modelcache

    rows = [json.loads(l) for l in
            (a.project / DATA / "public/panel.jsonl").read_text().splitlines() if l.strip()]
    snap = modelcache.download(a.repo, a.revision)
    tok = AutoTokenizer.from_pretrained(str(snap))
    model = AutoModelForCausalLM.from_pretrained(
        str(snap), dtype=torch.bfloat16, device_map="auto").eval()
    dev = model.get_input_embeddings().weight.device

    out = {"repo": a.repo, "revision": a.revision, "topk": a.topk, "arms": {}}
    for arm in ("full", "truncate_1", "misleading"):
        seen: dict[str, int] = {}
        rank_of_candidate = []
        for row in rows[:a.items]:
            ids = tok.encode(row["prompts"][arm])
            with torch.inference_mode():
                logits = model(torch.tensor([ids], device=dev)).logits[0, -1].float()
            top = torch.topk(logits, a.topk)
            toks = [tok.decode([int(i)]) for i in top.indices]
            seen[toks[0]] = seen.get(toks[0], 0) + 1
            order = torch.argsort(logits, descending=True).tolist()
            yes_id = tok.encode("Yes", add_special_tokens=False)[0]
            rank_of_candidate.append(order.index(yes_id))
        out["arms"][arm] = {
            "argmax_token_counts": seen,
            "median_rank_of_Yes": sorted(rank_of_candidate)[len(rank_of_candidate)//2],
            "n_items": a.items}
        print(f"  {arm:12s} argmax over {a.items} items: {seen}")
        print(f"  {arm:12s} median full-vocab rank of 'Yes': {out['arms'][arm]['median_rank_of_Yes']}")

    (a.project / OUT).parent.mkdir(parents=True, exist_ok=True)
    (a.project / OUT).write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
