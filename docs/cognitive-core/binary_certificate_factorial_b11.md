# Binary solver-certificate factorial b11

This is a fresh, bounded causal test motivated by the unresolved distinction
between external answer provision and usable intermediate proof state. It does
not reopen the v7 pilot or the failed three-way v8/v10 delivery screens.

The task contains only binary derivable items: an entailed query or a query
whose inverse is derivable. The model responds through direct semantic
single-token candidates `Yes` and `No`; open-world unknown is deliberately out
of scope. A fresh 36-item direct/reordered Yes/No qualification requires at
least 27 correct under each template, 12/18 correct in each class under each
template, and 32 identical candidate choices across templates.

Each of 192 fresh nonce-generated prospective items appears in five arms:
`none`, matched `irrelevant` donor proof, `conclusion_only`, `proof_prefix`
with the terminal literal omitted, and `full` proof. The primary contrast is
paired correctness for proof prefix minus conclusion only. Proof prefix minus
irrelevant and full minus conclusion only are secondary, Holm-adjusted
contrasts. Every comparison reports the complete paired table, exact
two-sided McNemar test, and seeded 100,000-resample paired BCa interval.

There is exactly one Qwen2.5-3B qualification attempt and, conditional on
passing, one prospective run. No retries, prompt sweeps, substitutions, or
automatic successors are authorized.
