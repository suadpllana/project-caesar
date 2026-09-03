# earliest-change-script — task state

Working memory. Never ships: `package.py` drops it and no gate outside `preflight.py`
reads it. The durable lessons live in the repo's CLAUDE.md.

## Current stage

`Stage 7 — gates`, after a **quality-review rejection on 2026-09-04** (two blocking
criteria) and the repair below. The rule change that answered the 2026-09-03 easiness
rejection is unchanged by it. Not resubmitted, not re-probed.

## Task summary

Given two lists of lines, return the shortest edit script under a three-tier rule: fewest
moves; of those, fewest comments, where a comment covers a run of moves together with any
later run that fewer than three kept lines separate from it; of those, the reading that
comes first with drop ahead of add ahead of keep. Graded on 52875 correctness cases, 400
medium pairs sharing a 40 s budget, and 18 large pairs with 60 s of wall clock each,
measured from outside the process.

## Why it is hard

- Expert time estimate: 10 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer — required): the second tier is not the quantity the word invites, so a position cannot carry a flag saying whether a run is open; it has to carry how many keeps have gone by since the last move, and both engines an expert recalls deliver how many moves remain and nothing else, so both have to be rebuilt around a state they were never written to hold. The staircase engine is where that bites hardest: under a rule counting runs the reachable matches of the next rank are one contiguous stretch and one sliding minimum answers the question, and under this rule the keep straight down the diagonal carries the count forward where every other keep resets it, so it has to be held out of the minimum, which splits the stretch into two windows and is the only formulation that stays finite on the pairs that share no order.
- Tactics making that true: prong A, since every existing diff answers the first tier and then slides runs afterwards by a heuristic that neither merges them the way a reader does nor respects the reading order, and prong C, since the six pairs that share no order are the only place the single-window formulation fails and no pair small enough to check against the table looks like them.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): the first plan is the table of (moves, comments) pairs walked from the start, which is completely correct, passes all 52875 short cases and cannot finish the medium block; the second plan is both engines with the second tier read as the number of runs of moves, which is what a careful reading that misses one sentence produces and is wrong on 10657 of the enumerated cases and 9160 of the random ones; the third plan is that submission with the sliding pass every diff tool carries bolted on afterwards, wrong on 13615 and 9082.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 3 of 8. The easiness probe solved the fewest-runs version 2 of 3, and the quality review then forced the third engine out, which removes implementation bulk rather than derivation. The honest reading is that the merge tier raises the floor and the lost engine lowers the ceiling, so this is nearer the middle of the band than the previous build was.

## Verifier contract (frozen)

Three processes. A child imports the module and holds no expected value, no clock and no
verdict. A parent harness never imports it and takes every measurement that counts. A third
account grades with pytest and asserts no submitted module reached its own `sys.modules`.
Graded all-or-nothing on exact move sequences plus per-case wall clock. The definitional
model is a table over (moves, comments) pairs carrying keeps-since-the-last-move as its
state, held to an exhaustive enumeration of every script on 15256 short pairs; the fast
implementation is held to the model on all 40875 fixed and enumerated cases with each of
its two engines forced in turn. `oracle.CONTEXT` and `reference.CONTEXT` are held equal by
a test, since neither file may import the other.

## The 2026-09-03 easiness rejection, and the rule change

2 of 3, with all three trajectories supplied. All three runs started at 12:26 and the two
transcripts carrying an end stamp finished at 54 and 83 minutes of a four-hour budget, the
83 being a solver. So the binding constraint was engineering stamina rather than any
derivation, and neither a tighter budget nor more of the same work would have moved it.

The repair changes what is computed: two runs of moves that fewer than three kept lines
separate are one comment. Measured against the graded blocks:

| reading | fixed (71) | enumerated (40804) | random (12000) |
|---|---|---|---|
| counting runs of moves, both engines exact | 20 | 10657 | 9160 |
| plus the sliding pass every diff tool carries | 31 | 13615 | 9082 |
| drops and adds as separate runs | 9 | 8821 | 9111 |
| the shortest script, reading order only | 7 | 870 | 4374 |
| difflib | 44 | 26916 | 11085 |
| the table; the per-cell frontier; `frontier_only`; `ok-cells` | 0 | 0 | 0 |

The single-window staircase, which is the natural port of the previous rule, is wrong on
**877 of 40875** fixed and enumerated cases with the staircase engine forced on.

## The 2026-09-04 quality-review rejection, and the repair

Two blocking criteria, on a build that had already cleared the structural, AI, similarity
and reference-verification gates and whose oracle scored 1 in the real two-image trial.

**`no extraneous files`.** `authoring/` and `authoring/variants/ok-cells/` shipped inside
the bundle: development tooling nothing in the build, run, solve or verify path uses, and
`verification_explanation` itself described the variant as kept "outside the bundle". Fixed
by moving the whole tree to `authoring/earliest-change-script/` at the repo root, which
makes that sentence true. **This is repo-wide**: 12 of the 13 bundles here ship an
`authoring/` directory, and `typeahead-query-controller`, the only bundle that has ever
cleared a quality review, ships none.

**`solvable`.** "~700 lines of dense algorithmic code comprising three independently hard
engines, the case families deliberately constructed so none can be skipped, and the
author's own expert estimate is 24 focused hours. That is days of implementation work even
for an expert who already knows the approach, exceeding the 'few hours at most' bar." Note
that `docs/RULES.md` says to aim at work needing "hours to days", so the bar the reviewer
applied is not the one the transcribed guideline states, and the declared 24 expert-hours
sat against a 4-hour agent budget.

Repaired by dropping the bit-parallel row engine and making the crowded family
frontier-reachable — 40 to 55 thousand lines over two to six distinct ones differing in a
few thousand places, rather than sharing no order at all. Reference 740 to 540 lines,
solution 789 to 570, three independently hard engines to two, expert estimate 24 to 10
hours. The comment tier and the dual-window staircase derivation are untouched, so what
was removed is implementation bulk and textbook recall rather than the thing that has to
be derived.

Timings after the cut, on this host:

| block | seconds | budget |
|---|---|---|
| medium (400) | 8.03 | 40 |
| timed, long (6) | 0.13–0.34 | 60 each |
| timed, crowded (6) | 0.63–3.15 | 60 each |
| timed, sparse (6) | 4.04–5.08 | 60 each |

**Calibration for the next session:** the reference answers timed case 13 in 4.04 s and the
whole medium block in 8.03 s on this host. Measure those two before trusting any timing
recorded here.

## Local gates run here

`preflight.py` no errors; `solvecheck.py`, `simcheck.py` (mechanical and conceptual) and
`hintcheck.py` clean; `structcheck.py` reports only the two findings the version that
cleared the AI screen also carried; `textcheck.py` burstiness 0.623 against 0.584 for that
version. `corners.py` ok, `counts.py` as tabled above, `fuzz.py` clean with the engines
forced in turn.

The three-engine build that this one replaces cleared the full two-image trial **12 of 12**
on 2026-09-03: oracle 1, nop 0, nine cheats 0, `ok-cells` 1. The trial has to be re-run on
the two-engine build.

## Gates not run here

- The apt layer in `tests/Dockerfile` cannot be built on this host: `deb.debian.org` answers
  403 through the egress proxy. `tools/ecs_trial.py` drops it, which costs `pkill`, so the
  teardown between the sandbox account and the grading account is the one shipped defence
  the local trial does not exercise.
- The three-agent probe has never been run on the comment-merge rule: the account hit its
  session limit.
