# Task state

Working memory. Never ships - `package.py` drops it. Rewritten 2026-09-05 after the
quality-review rejection on `no extraneous files`, because the bundle came back from the
pipeline as a zip and the zip does not carry this file.

## Current stage

`Stage 8 - resubmission`. The bundle cleared the structural check, the AI screen, the
similarity screen and reference verification on 2026-09-05, and failed the quality review
on one blocking criterion.

## Task summary

A multiplexed ingest link with a two-level permit budget: a shared link ceiling and a
per-feed one. The shipped tree accounts for permit the way every receiver-side window is
written up - return permit when the consumer draws rows off, judge an arrival against the
ceiling standing now, withhold a raise until it clears the threshold - and that accounting
is coherent, conventional and wrong here. The graded artifact is the published obligation:
which ceiling each level is told and on which tick, plus the store the stream leaves behind.

## Why it is hard

Two defects that cannot be repaired in either order independently.

Rows charged to the link can leave without ever being drawn - parked on a feed when it is
torn down, or arriving during the three ticks a teardown takes to reach the producer - so a
ceiling built on what the consumer took runs permanently short. And the decision to publish
below the threshold turns on whether a producer is stuck, which is a fact about what that
producer was last *told*, not about what the book holds now. Nothing in the environment
records the published history; a policy that wants it has to have been keeping it. In the
shipped tree those two quantities coincide, so the natural implementation reads the answer
off the book and is right - and fixing the first defect is exactly what pulls them apart.

- Expert time estimate: 8 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the plan it
  reconstructs from its prior is the shipped tree's own accounting, correct on one level with
  one producer and wrong here, and the environment witnesses neither defect - discarded rows
  leave no counter and the published history is stored nowhere, so both must be derived rather
  than read off a field.
- Tactics making that true: prong A (the distinction lives in frozen code, never in the
  brief), prong C (no oracle for the published obligation - the agent's own harness cannot
  tell it that its ceiling is short), and B2 (the second discovery invalidates the natural
  implementation of the first).
- My own attack on the plan (my first plan, and where it is wrong): my first plan was to
  return permit at teardown for whatever was parked, which fixes the arithmetic on the
  enumerated streams and still loses, because the rows arriving inside the teardown window
  are charged too and because the obligation is then published against a book that no longer
  tracks what the buffers report.
- Estimated solves out of 8: 1 of 8, designed for the bottom of the band

## Verifier contract (frozen)

Graded all-or-nothing on three axes: the published rows per level per tick, the parked
store at the end of the stream, and the lifecycle log. 24 enumerated streams and 300
generated inside the verifier from a nonce made after the agent has finished. Ground truth
is re-proved at verification time by `tests/oracle.py`, which shares no code with the engine.

## What ran, 2026-09-05

`prove` 300 streams 0 disagreements, `audit` all 24 states agree and all 7 variants agree,
`variant_check` 7/7 on 200 streams, `readingcheck` 11 readings all separated, `tiecheck`
424 streams 0 double rows and the mirror variant agrees, `determinism` identical across 5
hash seeds, `build_gt` byte-identical, `shipped` 9 of 24 enumerated and 0 of 300 generated,
`extraneouscheck`, `solvecheck`, `deadfieldcheck`, `catcheck`, `hintcheck`, `structcheck`,
`simcheck` and `zipcheck` clean, `onelinecheck` no exact rule at depth 2 on either decision.

## Gates NOT run

Docker is absent on this host, so **the two-image trial did not run**: the privilege drop,
the root-owned reward channel, the root-only ground truth, `reap.py` and the 23 cheats are
unexercised here. `cheat_report.py` and `authoring/trial.py` need a host with docker. The
three-agent easiness probe has never been run on this bundle either.
