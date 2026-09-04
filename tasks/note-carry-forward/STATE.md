# note-carry-forward

Scratch notes for the next session. Never ships; `package.py` drops it.

## What is graded

The live note table at the head of every stream, and the ordered log of
retirements, raises and absorptions on the way there. All or nothing. There is
no work counter anywhere in this task and no timing budget.

## Verifier contract, frozen before the environment was written

- graded: the table and the ordered log, per stream
- not graded: how the board stores state, what it computes first, how many
  times it walks the store
- ground truth: `tests/gt.json`, root-only, rebuilt by `authoring/build_gt.py`,
  re-proved at grading time by `tests/oracle.py`
- event order inside one revision is part of the contract and is stated in the
  brief: retires, then raises, then absorbs, each in ascending note order.
  Without that, two correct boards disagree about the log and the run audit
  bites.

## Difficulty argument

- Why a frontier agent cannot one-shot the plan: the tree hands over the diff
  engine, so the plan it forms is to ask that engine where a note's line went
  and read the answer off its kept steps. That answers a narrower question. A
  line the script dropped has usually not gone; it is standing wherever its
  own change put a line in its place, and deciding which line that is means
  deciding what one change is, which no shipped function will tell you.
- Tactics making that true: prong A (the retrieved plan is specifically wrong), prong C (no oracle for the graded quantity in the agent's tree)
- My own attack on the plan: my first plan was to widen a note's subject to
  the change group it lands in and iterate absorption to a fixed point, and it
  is wrong because group-widened subjects are group-aligned, so intersections
  are decided before any absorbing happens and the fixed point never iterates
  - measured at 0 disagreements over 400 streams, which is why the mechanism
  is carrying rather than widening.
- Estimated solves out of 8: 1, designed. Probed once at 3 of 3 on the
  previous rule and repaired; not re-probed.

Two properties of the frozen engine carry the weight and neither is stated.
**The pinned script does not compose**, and **what the engine calls one change
is not one run of moves in the script** - runs standing fewer than three kept
lines apart are one change. `grp.spans` uses that grouping and its output
cannot be used for the mapping, because it reports the lines a change came to
rest on and drops the moves that say where each of them came from.

Measured on the graded distribution, 500 generated streams:

| wrong reading | streams it moves | the case that names it |
|---|---|---|
| diff the note's origin revision straight against the head | 80.8% | `open-at-head` |
| rebuild the mapping with an ordinary LCS backtrace | 76.0% | `tie-break-picks-the-survivor` |
| raise only the lines the script added | 75.2% | `raise-kept-inside-change` |
| rebuild the mapping from `difflib` opcodes | 73.6% | `matcher-keeps-another-copy` |
| newer note wins the line | 57.2% | `absorb-older-wins` |
| never absorb | 57.2% | `absorb-older-wins` |
| retire a dropped line rather than pairing it | 49.6% | `replace-carries-the-note` |
| retire without logging it | 48.8% | `retire-dropped` |
| pair inside one run of moves, cutting at every kept line | 38.6% | `replace-across-a-gap` |
| pair a change's drops with its adds from the far end | 27.4% | `more-gone-than-came` |
| close a change one kept line later than the tool does | 3.4% | `too-far-to-pair` |

The last row is the one to read. It moves few generated streams because it
needs a drop and an add exactly three kept lines apart, and it is not a
lottery ticket, because `too-far-to-pair` names it on its own.
`authoring/readings.py` fails only a reading that is both rare and unnamed.

The shipped tree already matches on 40 of 319 streams, so the chain is four
decisions rather than three.

## Expert path

Replay the store revision by revision; read the surviving-line mapping off the
walk `scr/pin.py` produced rather than rebuilding it; cut that walk into
changes the way `scr/grp.py` cuts it and pair each change's drops to its adds
in order; raise on membership of a change span; order the log as stated.
About 75 lines across the two artifacts.

## The `grp.spans` warning is accepted deliberately

`preflight` reports `spans()` as defined and never called in the environment,
which is the dead-public-function class this repo has twice found to be a real
leak. It is left standing. It answers `raised`, which is the easy half and
which the brief has to state as a requirement anyway; it cannot answer the
mapping, which is the half the task turns on. The two repairs that would clear
the warning are both worse: deleting it removes the tool's own answer to what
a change reaches and makes `raised` a coin flip, and having `run_review.py`
print a change count per revision hands the solver the merging law empirically,
which is the second discovery.

The other seven warnings are the documented false-positive class - methods
reached through an instance or a module alias, which preflight does not
resolve.

## Probe status

Rejected **3 of 3** on 2026-09-04 at runtimes of 1m14s to 1m17s against a
14400 s budget. Trajectories, the attribution and the reconstructed submission
are in `probes/note-carry-forward/`. Repaired; **run the three-agent probe
before submitting again** - it is the only local gate that measures what the
easiness gate rejects for.

## Gates run (2026-09-04, Linux sandbox, Docker up)

- real two-image trial `--all`: **20/20** (oracle 1, nop 0, 18 cheats 0)
- real two-image trial `--variants`: **4/4** score 1
- the submission that solved the previous rule, rebuilt from the trajectories:
  **reward 0**
- `build_gt.py`: reference and sealed oracle agree on 19 hand-written and 360
  generated streams
- `readings.py`: every wrong reading is common on the graded set or named by
  an enumerated case
- `cheat_report`, `forgecheck`, `simcheck`, `solvecheck`, `deadfieldcheck`,
  `catcheck`, `hintcheck`, `structcheck` clean
- `textcheck` clean against all four briefs that cleared the AI screen
- `preflight` no errors

## Gates NOT run

- the three-agent easiness probe (the important one)
- `onelinecheck`: the task ships no `authoring/decisions.py` in the format that
  tool wants. The readings are measured by `authoring/readings.py` instead,
  whose numbers are the table above.
- the apt layer, so `pkill` is unexercised; `tests/reap.py` walks `/proc`.
