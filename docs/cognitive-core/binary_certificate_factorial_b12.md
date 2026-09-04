# Binary solver-certificate factorial b12: interruption-safe execution

B12 is the sole fresh successor to b11. B11's qualified prospective run was
externally interrupted after reporting progress through 24 no-evidence items,
before it persisted a prospective receipt or opened an answer authority. B11
remains terminal and is not rerun.

B12 preserves the b11 binary derivable-query task, direct `Yes`/`No` scoring,
five matched arms, sample size, primary contrast, and analysis plan. It uses a
newly seeded, sealed panel. The execution transport alone changes: each arm is
divided into eight fixed 24-item shards. Each shard has an exclusive start
record, an exclusive complete receipt, and an exclusive completion record.
The answer authority remains unopened until all 40 receipts exist.

Qualification is one fresh 36-item direct/reordered Yes/No screen. After a
pass, every one of the 40 arm-shards is run exactly once. A completed shard is
never rerun. An interrupted shard without its complete receipt terminates the
study rather than being reissued. The finalizer scores only a complete set of
all preregistered receipts.
