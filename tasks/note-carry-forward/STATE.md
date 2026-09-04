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
  and read the answer off, which is correct-looking, cheaper, and wrong,
  because the pinned script does not compose and nothing in the tree says so.
- Tactics making that true: prong A (the retrieved plan is specifically
  wrong), prong C (no oracle for the graded quantity in the agent's tree).
- My own attack on the plan: my first plan was to widen a note's subject to
  the change group it lands in and iterate absorption to a fixed point, and it
  is wrong because group-widened subjects are group-aligned, so intersections
  are decided before any absorbing happens and the fixed point never iterates
  - measured at 0 disagreements over 400 streams, which is why the mechanism
  is carrying rather than widening.
- Estimated solves out of 8: 1, designed. Not probed.

The tree ships the engine that pins a change script, so nobody has to write a
diff. The weight is in one property of that engine nobody states: **the pinned
script does not compose**. Measured on the graded distribution:

| wrong reading | streams it moves |
|---|---|
| diff the note's origin revision straight against the head | 66.4% |
| rebuild the mapping with an ordinary LCS backtrace | 62.0% |
| rebuild the mapping from `difflib` opcodes | 59.0% |
| raise only the lines the script added | 51.8% |
| retire without logging it | 60.6% |
| newer note wins the line | 43.6% |
| never absorb | 43.6% |

The shipped tree does the first of those. It is stateless in the way the brief
asks for, it is one engine call per note instead of one per revision, and it
resurrects notes whose line died revisions ago and whose text was typed again
later. `/app/streams/guard.txt` is that, observed.

## Expert path

Replay the store revision by revision; read the surviving-line mapping off the
walk `scr/pin.py` produced rather than rebuilding it; raise on membership of a
change span rather than on being an added line; order the log as stated.
60 lines across the two artifacts.

## Probe status

Not probed. **Run the three-agent probe before
submitting** - it is the only local gate that measures what the easiness gate
rejects for.

## Gates run (2026-09-04, Linux sandbox, Docker up)

- real two-image trial `--all`: **16/16** (oracle 1, nop 0, 14 cheats 0)
- real two-image trial `--variants`: **3/3** score 1
- `build_gt.py`: reference and sealed oracle agree on 13 hand-written and 360
  generated streams
- `textcheck` clean against all three briefs that cleared the AI screen;
  `structcheck` and `hintcheck` clean
- `preflight` clean of errors

## Gates NOT run

- the three-agent easiness probe (the important one)
- `readingcheck` and `onelinecheck`: the task ships no `authoring/readings.py`
  or `authoring/decisions.py` in the format those tools want. The readings are
  measured instead by `authoring/readings.py` in this task's own shape, whose
  numbers are the table above.
- the apt layer, so `pkill` is unexercised; `tests/reap.py` walks `/proc`.
