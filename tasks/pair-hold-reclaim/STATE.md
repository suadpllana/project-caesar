# pair-hold-reclaim — working notes

Scratch for the next session. Never ships; `package.py` drops it and no gate reads it.

## What the task is

A small object store under `/app`. Cells, links, two conditional entry tables, watches of
two kinds, one-shot cleanups, and a pass that reclaims. The pass has been rewritten wrong
and the agent repairs it by editing four files: `core/rch.py`, `core/cln.py`,
`core/pss.py`, `core/obs.py`. `core/obs.py` is already correct and needs no change.

## Verifier contract, frozen 2026-09-02 before any environment code

Graded, exactly, all or nothing:

- the ordered ledger for every stream (`cn`, `em`, `dp`, `db`, `rl`, `sh` rows)
- the final store state (cells with links, both entry tables, watch targets, bound names)

Streams: the 31 enumerated ones in `tests/scen.py`, plus 300 built inside the verifier
from a nonce made out of `/dev/urandom` at trial time.

Not graded, on purpose, because two correct readings differ on them: how many times a
submission marks, how many rounds it takes to settle, what it caches, which data
structures it keeps. Six alternative correct implementations live in
`authoring/variants/` and all six must score 1.

The load-bearing half of this is also in the module docstring of `tests/test_outputs.py`,
which is the copy that ships and the one the run audit reads.

## Difficulty

- Why a frontier agent cannot one-shot the plan: the pass has to hold two nested fixed
  points that no sentence of the brief names — conditional entries make reach a least
  fixed point rather than a traversal, and a cleanup that unbinds a name makes another
  cleanup fall due, so the pass is rounds rather than a phase pipeline — and on top of
  that the ordering question has two seeds that agree on every stream in the shipped tree
  and disagree only where a two-key entry straddles the boundary between what is held and
  what is being cleaned up.
- Tactics making that true: A1, A2, B1, B2, C1, C4, prong A, prong B, prong C. The phase
  pipeline every collector is described with is specifically wrong here (A1), the
  conditional entry is described and never named (A2), the op set and the meaning of a
  ledger row are recovered by reading the store rather than a document (B1), reach and
  ordering and emptying interact rather than stack (B2), every fence is graded from both
  sides (C1), and three hundred generated streams are what a rule fitted to the shipped
  ones dies on (C4).
- My own attack on the plan: my first plan was mark from the bound names through links and
  entries, doom the rest, empty the plain watches, run the pending cleanups oldest first,
  re-mark once, let go of what is still out of reach. It is wrong in three places. It
  sweeps the entry tables once instead of to a fixed point; it runs one round of cleanups
  where a cleanup that unbinds a name makes a second one due in the same pass; and it
  orders cleanups by age where the rule orders them by reach, with the seed for that
  question including the held cells, which only a two-key entry can tell apart.
- Estimated solves out of 8: 2. Designed at 1, and the shipped tree already passes 15 of
  the 31 enumerated streams, so the real chain is the other 16.

## Measured, 2026-09-02

| | enumerated | generated |
|---|---|---|
| reference | 31/31 | 300/300 |
| shipped tree | 15/31 | 40/331 overall |
| answer-key probe (holds `gt.json`) | 31/31 | 18/150 |
| `pending-seed` (the near-miss) | 30/31 | 36/250 |

- reference against the sealed model: 2000 streams, 25042 rows, 0 disagreements; and
  again at 600 and 400 after every environment change.
- `tools/docker_trial2.py --all`: 28/28 before the last environment edit, re-run after.
- `tools/docker_trial2.py --variants`: 5/5.
- `tools/onelinecheck.py`: no graded decision has an exact rule at depth <= 2.
- `tools/readingcheck.py`: all 17 wrong readings separated by an enumerated case.
- `tools/deadfieldcheck.py`: clean after deleting `Cell.i`; ground truth came back
  byte-identical, which is what says the deletion was a leak fix and not a behaviour
  change.

## Expert path

Read `core/st.py` to learn the op set and what each ledger row means, then `core/ex.py`
for when a pass happens. Notice that the entry tables are conditional and that the
condition is answered by the set being built, so reach is a least fixed point. Notice
that a cleanup's action mutates the store the pass is deciding from, so the marking the
pass acts on cannot be the one it started from, and that a cleanup which unbinds a name
can make a second cleanup due, so one extra marking is not enough either. Then work out
that the ordering question is asked from the pending cell with the names still bound.
Build the enumerated shapes by hand and run them through `run_ops.py`.

## Not done / open

- No probe run. The user asked for none.
- `harbor check` was not run; it is not installed here.
