# earliest-change-script, easiness probe, 2026-09-04

Three trajectories, agents' own words only (the brief they were given is stripped from the
head of each file, so `leakcheck` is not circular).

| file | what it built | its own stated failure regime |
|---|---|---|
| `trial1.md` | frontier + LIS match-point engines, one shared tie-break DP | ~20k moves approaches 50 s; a strictly repeating cycle makes the tie-break DP slow at 1M |
| `trial2.md` | banded bit-parallel (Hyyro) + sparse Hunt-Szymanski, checkpointed | one line repeated a million times; edit distance far past 10k |
| `trial3.md` | Myers frontier + Hunt-Szymanski, interval DP for ambiguous regions | edit distance well above 15k on 1M lines exceeds 60 s |

All three solved it. All three wrote a brute-force oracle as their first or second file and
differential-tested against it.

## Attribution

- `leakcheck`: one shared phrase, `fewer than three kept lines`, in trials 1 and 3. That is
  the rule statement, which fairness requires. **Not mode A.**
- No environment ships with this task, so **not mode B**.
- One-shot correct module, then a self-built oracle goes green: **mode C**.

Trial 1 additionally named both engines in its opening sentence, before any tool call
("a match-point/LIS approach for near-unique lines and a Wu-Myers frontier approach for
few-edit files"), which is the Speed section's cost taxonomy read straight off the brief.
That paragraph was tightened on 2026-09-04; it is a real reduction in handed-over dispatch
information and it is not expected to flip the probe on its own.

## Why no repair follows

See "The ceiling, measured from the other end" in `CLAUDE.md`. The short version: the only
lever a fully specified pure function has left is speed, and the reference is not faster than
a naive per-cell implementation on any ambiguous input - it loses outright on run-structured
files. Measure before designing a regime.
