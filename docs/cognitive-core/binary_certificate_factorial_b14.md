# Binary solver-certificate factorial b14: persistent local execution

B14 is the sole fresh successor to b13. The binary experimental design is
unchanged: direct Yes/No delivery qualification, then five matched arms on a
new 192-item binary derivable-query panel. Its only change is execution
transport: a single persistent local supervisor process runs the qualification
and, only if it passes, the prospective factorial.

The foreground execution service interrupted b11 through b13 before those
runs could persist a complete result. B14 must be launched as one persistent
local process with its stdout/stderr saved under the run directory. No retries,
prompt changes, data substitutions, or automatic successors are authorized.
