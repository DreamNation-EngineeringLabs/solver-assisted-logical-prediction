# Solver-assisted certificate factorial: bounded successor v10

V10 is a fresh, one-time successor to the sealed v8 factorial. It exists only
because the single Qwen3 v8 qualification attempt terminated during conversion
of model logits from MLX bfloat16 to NumPy, before a score, receipt, or answer
authority was read. V8 remains terminal and is not rerun or altered.

V10 preserves the v8 research question, five matched arms, semantic task,
three-way qualification thresholds, paired primary contrast, bootstrap
interval, exact McNemar test, and analysis thresholds. It uses a newly seeded,
independently sealed 36-item interface panel and 192-item prospective panel.

The only implementation change is an explicit MLX float32 cast and conversion
through a Python list before NumPy receives the candidate-token logits. This
avoids the buffer-format failure without changing a prompt, label mapping,
model, decoding rule, certificate, item construction rule, or analysis rule.

Only Qwen3-1.7B is eligible. Qwen2.5-3B already failed v8 semantic delivery
qualification and is not retested. Qwen3 may enter the prospective panel only
if it reaches at least 27/36 correct under each mapping, at least 8/12 per
class under each mapping, and semantic agreement on at least 32/36 direct
facts. A failed qualification is terminal and is not a certificate-treatment
result.

There is one qualification attempt and, if it qualifies, one prospective run.
No retries, prompt sweeps, model substitutions, post-hoc item changes, or
automatic successor experiments are authorized.
