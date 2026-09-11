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

Writes results/b20_answer_position_<checkpoint>.json. No receipts: this is a diagnostic
about prompt format, not a scored arm.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

DATA = Path("data/cognitive_core/binary_certificate_factorial_b15")
OUT_TEMPLATE = "results/b20_answer_position_{slug}.json"


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
    ap.add_argument("--entailed", default="", help="comma-separated task ids")
    ap.add_argument("--contradicted", default="", help="comma-separated task ids")
    a = ap.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from cc_instruments import modelcache

    rows = [json.loads(l) for l in
            (a.project / DATA / "public/panel.jsonl").read_text().splitlines() if l.strip()]
    # The panel is ordered by class, so a prefix samples one class only -- the
    # mistake the first version of this diagnostic made. Stratifying needs the
    # answer key, which never leaves the local machine, so the caller selects the
    # sample and passes ids and labels in. --entailed and --contradicted are
    # comma-separated task ids.
    by_id = {r["task_id"]: r for r in rows}
    ent_ids = [t for t in a.entailed.split(",") if t]
    con_ids = [t for t in a.contradicted.split(",") if t]
    if not ent_ids or not con_ids:
        raise SystemExit("pass --entailed and --contradicted task ids (see --help)")
    missing = [t for t in ent_ids + con_ids if t not in by_id]
    if missing:
        raise SystemExit(f"task ids not in the panel: {missing[:3]}")
    sample = ([(by_id[t], "Yes") for t in ent_ids] + [(by_id[t], "No") for t in con_ids])
    ent, con = ent_ids, con_ids

    snap = modelcache.download(a.repo, a.revision)
    tok = AutoTokenizer.from_pretrained(str(snap))
    model = AutoModelForCausalLM.from_pretrained(
        str(snap), dtype=torch.bfloat16, device_map="auto").eval()
    dev = model.get_input_embeddings().weight.device

    def one(text: str) -> int:
        e = tok.encode(text, add_special_tokens=False)
        if len(e) != 1:
            raise RuntimeError(f"{text!r} is not one token: {e}")
        return e[0]
    # bare candidates are what every runner scores; the space-prefixed pair is
    # what a prompt ending in "Answer:" actually invites
    ids = {"bare": (one("Yes"), one("No")), "spaced": (one(" Yes"), one(" No"))}

    out = {"repo": a.repo, "revision": a.revision, "topk": a.topk,
           "n_entailed": len(ent), "n_contradicted": len(con),
           "candidate_token_ids": {k: list(v) for k, v in ids.items()}, "arms": {}}
    for arm in ("full", "truncate_1", "misleading"):
        argmax_tok, agree, rank_bare, per_class = {}, 0, [], {"Yes": [], "No": []}
        for row, truth in sample:
            enc = tok.encode(row["prompts"][arm])
            with torch.inference_mode():
                lg = model(torch.tensor([enc], device=dev)).logits[0, -1].float()
            top = torch.topk(lg, a.topk)
            t0 = tok.decode([int(top.indices[0])])
            argmax_tok[t0] = argmax_tok.get(t0, 0) + 1
            order = torch.argsort(lg, descending=True).tolist()
            rank_bare.append(order.index(ids["bare"][0]))
            vb = "Yes" if lg[ids["bare"][0]] > lg[ids["bare"][1]] else "No"
            vs = "Yes" if lg[ids["spaced"][0]] > lg[ids["spaced"][1]] else "No"
            agree += (vb == vs)
            per_class[truth].append(vb)
        out["arms"][arm] = {
            "argmax_tokens": argmax_tok,
            "median_rank_of_bare_Yes": sorted(rank_bare)[len(rank_bare) // 2],
            "bare_and_spaced_agree": f"{agree}/{len(sample)}",
            "bare_verdicts_on_entailed": per_class["Yes"],
            "bare_verdicts_on_contradicted": per_class["No"]}
        print(f"  {arm:12s} argmax {argmax_tok}")
        print(f"  {arm:12s} bare-vs-spaced verdict agreement {agree}/{len(sample)}"
              f"   median rank of bare 'Yes' {out['arms'][arm]['median_rank_of_bare_Yes']}")
        print(f"  {arm:12s} bare verdicts: entailed {per_class['Yes']}  contradicted {per_class['No']}")

    slug = a.repo.split("/")[-1].lower().replace(".", "p")
    out_path = Path(OUT_TEMPLATE.format(slug=slug))
    (a.project / out_path).parent.mkdir(parents=True, exist_ok=True)
    (a.project / out_path).write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
