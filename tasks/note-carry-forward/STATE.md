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

Measured by `authoring/readings.py` over 400 streams from the graded
generator:

| wrong reading | streams it moves |
|---|---|
| diff the note's origin revision straight against the head | 99.0% |
| the standard library's matcher for the mapping | 96.5% |
| retire without logging it | 96.8% |
| an ordinary LCS walk for the mapping | 95.2% |
| a change read as the lines the script added | 95.2% |
| two notes left sitting on one line | 87.2% |
| **raise every revision the note spends inside a change** | **56.8%** |
| newer note wins the line | 19.8% |

**Both editable files ship wrong and the two discoveries are locked together.**
`note/board.py` does origin-to-head. `note/rule.py` raises on the present
state instead of on becoming part of a change, which is the discovery that
makes the walk load-bearing: the answer depends on where the note stood when
the previous revision closed, and a board with no walk has nowhere to keep it.
`/app/streams/guard.txt` is the board defect, observed.

## Expert path

Walk the store one revision at a time; read the surviving-line mapping off the
walk `scr/pin.py` produced rather than rebuilding it; raise on membership of a
change span rather than on being an added line; order the log as stated.
About sixty lines across the two artifacts.

## Probe status

Not probed. **Run the three-agent probe before
submitting** - it is the only local gate that measures what the easiness gate
rejects for.

## Easiness rejection, 2026-09-04 (second round), and what changed

Solved 3 of 3 in **75 seconds a trial** against a 14400 s budget. All three
trajectories show one `cat > note/rule.py`, one `cat > note/board.py`, both
correct first time. `leakcheck` is quiet on all three, so it was not the
wording. Two causes, and the second is the real one:

- **Mode B, arrows.** The shipped `note/rule.py` carried `from scr import pin`
  and never used it, and `grp.spans` was called by nothing while the brief
  named both modules. `preflight` warned about exactly that and the warning
  was dismissed as the documented false-positive class. It was not. Both
  frozen modules are now genuinely used by the shipped code, so nothing says
  "wire me in".
- **The mechanism was too shallow.** Every defect was self-announcing against
  a brief that stated the rule completely, so the work was transcription. The
  repair is a second discovery that is not a question about any one revision:
  a note is raised when its line *becomes* part of a change, so the answer
  depends on the note's own history and only a walking board can supply it.
  Measured at 56.8% of streams, and it makes the origin-to-head defect
  unfixable in isolation rather than merely wrong.

The generated streams are shorter and edited harder than before (5-16 lines,
3-9 edits a revision, 4-10 revisions, up to 3 notes opened per revision),
because that is the shape that leaves a note inside a change for more than one
revision running. Under the old shape the new rule moved 6.5% of streams,
which is a lottery ticket; `authoring/readings.py` now fails if any reading
falls under a tenth.

## Quality-review rejection, 2026-09-04, and what changed

Failed on four blocking criteria: `difficult`, `difficulty explanation
quality`, `instruction concision`, `no extraneous files`. The fixes:

- **difficult**: the brief stated the method. It said carry "one revision at a
  time", said what `pin.py` settles is what the board carries notes through,
  said `grp.py` says where a change begins and ends, and shipped a correct
  `rule.py` so the work was one file. The method sentences are gone, and
  `rule.py` now ships wrong in both of its functions, so the work is three
  independent decisions across two files rather than one careful replay.
- **difficulty explanation quality**: it omitted who does this for a living
  and what the streams actually are. Both are now stated, including that the
  streams are synthetic token lists and why that distribution is chosen.
- **instruction concision**: 926 words to 603. Narrative preamble, oblique
  phrasing and the paragraph describing verifier internals are gone.
- **no extraneous files**: `authoring/probe*.py` deleted (scratch, hardcoded
  paths, calls to a function that no longer exists); `readings.py` rewritten
  self-contained; `cheat_report.py` no longer imports anything outside the
  bundle.

`authoring/variants/` stays: `guard-mark-unwind` and `share-register-screen`
both ship variants and both cleared this review.

## Gates run (2026-09-04, Linux sandbox, Docker up)

- real two-image trial `--all`: **17/17** (oracle 1, nop 0, 15 cheats 0)
- real two-image trial `--variants`: **4/4** score 1
- `build_gt.py`: reference and sealed oracle agree on 15 hand-written and 360
  generated streams
- `textcheck` clean against all three briefs that cleared the AI screen;
  `structcheck` and `hintcheck` clean
- `preflight` clean of errors

## Gates NOT run

- the three-agent easiness probe (the important one)
- `onelinecheck`: the task ships no `authoring/decisions.py` in the format that
  tool wants. The wrong readings are measured instead by
  `authoring/readings.py`, which is self-contained and fails if any reading
  moves under a tenth of the set; its numbers are the table above.
- the apt layer, so `pkill` is unexercised; `tests/reap.py` walks `/proc`.
