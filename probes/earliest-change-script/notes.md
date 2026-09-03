# earliest-change-script: the easiness trajectories

All files here are the agents' own words and tool calls only; the instruction each was given
has been cut off the top so that `tools/leakcheck.py` is not run against text the brief itself
contains.

## 2026-09-02: the reading-order rule alone (`easiness-2026-09-02-trajectory.md`)

One of the three trajectories behind the 3 of 3 on the bundle submitted 2026-08-31 (budgets
15 s / 30 s, no hunk tier).

- **Runtime about three hours of a four-hour budget.** Not a plan available on sight.
- **The rule was reduced to the greedy in the first message**, before any tool call.
- **A brute-force oracle was its first file**, and everything after was differential-tested
  against it.
- **Four engines**: bit-parallel rows with checkpointing, Myers layers, a banded bit-parallel
  variant, and suffix patience thresholds with an undo journal, the reference's third engine.
- **Each engine was forced on small inputs and held to the oracle**, which the difficulty
  argument said could not happen and which is exactly what the verifier's own agreement
  test does.

## 2026-09-03: the three-tier rule, first cut (`easiness-2026-09-03-trajectory-{1,2,3}.md`)

3 of 3 again, on the bundle that added the fewest-hunks tier (budgets 60 s / 40 s) with the
timed families long / crowded-but-ordered / sparse.

- **All three went match-first.** Each reduced the rule to "longest chain of matched pairs,
  then most diagonal-adjacent pairs, then the latest legal pair", and built the staircase
  engine over matches as its *core*. The per-cell formulation the repair was built around
  never appeared.
- **All three handled the long and crowded-but-ordered families by decomposition**: cutting
  the pair at long common runs (rigorous forced cuts found from bit-parallel rows in
  trajectory 3; heuristic sync points in 1 and 2) and solving the small pieces with an exact
  table. A pair that differs in a few thousand places is still mostly long identical
  stretches, so both families decomposed.
- **None of them could do a crowded pair with no order.** Trajectory 2 says so ("a pair that
  is both unrelated and drawn from a handful of distinct lines ... falls back to a valid but
  non-minimal script"; "binary-alphabet pairs above ~2.5M cells can't be decomposed"), and
  1 and 2 fall back to heuristic bands there. That family had been dropped from the task
  because the reference had no algorithm for it under the hunk tier.
- Trajectory 3 is the strongest: bit-parallel rows, forced-cut detection, the staircase
  engine, and about a thousand lines.

## What was done about it

The crowded no-order family is back, graded, because the reference gained an engine for it:
the cells on shortest paths are read off bit-parallel rows with a handful of integer
operations per row (the between-row prefix-LCS difference is an alternating mark pattern,
so one subtraction fills it), and they are only a few per row, so the hunk recurrence over
them is cheap. See the CLAUDE.md entry dated 2026-09-03.
