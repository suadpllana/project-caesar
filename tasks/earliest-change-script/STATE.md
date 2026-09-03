# earliest-change-script — task state

Working memory. Never ships: `package.py` drops it and no gate outside `preflight.py`
reads it. The durable lessons live in the repo's CLAUDE.md.

## Current stage

`Stage 7 — gates`, after an **easiness rejection (2 of 3)** on 2026-09-03 and the rule
change that answers it. Not yet resubmitted, not re-probed.

## Task summary

Given two lists of lines, return the shortest edit script under a three-tier rule: fewest
moves; of those, fewest comments, where a comment covers a run of moves together with any
later run that fewer than three kept lines separate from it; of those, the reading that
comes first with drop ahead of add ahead of keep. Graded on 52875 correctness cases, 400
medium pairs sharing a 40 s budget, and 18 large pairs with 60 s of wall clock each,
measured from outside the process.

## Why it is hard

- Expert time estimate: 24 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer — required): the second tier is not the quantity the word invites, so a position cannot carry a flag saying whether a run is open; it has to carry how many keeps have gone by since the last move, and every one of the three engines an expert recalls delivers how many moves remain and nothing else, so all three have to be rebuilt around a state they were never written to hold. The staircase engine is where that bites hardest: under a rule counting runs the reachable matches of the next rank are one contiguous stretch and one sliding minimum answers the question, and under this rule the keep straight down the diagonal carries the count forward where every other keep resets it, so it has to be held out of the minimum, which splits the stretch into two windows and is the only formulation that stays finite on the sparse family.
- Tactics making that true: prong A, since every existing diff answers the first tier and then slides runs afterwards by a heuristic that neither merges them the way a reader does nor respects the reading order, and prong C, since the third family is the only place the per-cell formulation fails and no pair small enough to check against the table looks like it.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): the first plan is the table of (moves, comments) pairs walked from the start, which is completely correct, passes all 52875 short cases and cannot finish the medium block; the second plan is the three engines with the second tier read as the number of runs of moves, which is what a careful reading that misses one sentence produces and is wrong on 10657 of the enumerated cases and 9160 of the random ones; the third plan is that submission with the sliding pass every diff tool carries bolted on afterwards, wrong on 13615 and 9082.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 2 of 8. The easiness probe solved the fewest-runs version 2 of 3, both solvers finishing in about a third of their budget, so the added state is not the whole answer; what it buys is that the recalled engines are no longer sufficient and the staircase reformulation has to be found rather than transcribed.

## Verifier contract (frozen)

Three processes. A child imports the module and holds no expected value, no clock and no
verdict. A parent harness never imports it and takes every measurement that counts. A third
account grades with pytest and asserts no submitted module reached its own `sys.modules`.
Graded all-or-nothing on exact move sequences plus per-case wall clock. The definitional
model is a table over (moves, comments) pairs carrying keeps-since-the-last-move as its
state, held to an exhaustive enumeration of every script on 15256 short pairs; the fast
implementation is held to the model on all 40875 fixed and enumerated cases with each of
its three engines forced in turn. `oracle.CONTEXT` and `reference.CONTEXT` are held equal
by a test, since neither file may import the other.

## The 2026-09-03 easiness rejection, and the fix

2 of 3, with all three trajectories supplied. Both solvers rebuilt the reference's three
engines from scratch; all three runs started at 12:26 and the two transcripts carrying an
end stamp finished at 54 and 83 minutes of a four-hour budget, the 83 being a solver. The
one that failed built the same engines and lost on speed, most likely the medium block. So the binding constraint was engineering stamina rather than any derivation, and
neither a tighter budget nor more of the same work would have moved it: the solvers had
two and a half hours spare.

The repair changes what is computed. Two runs of moves that fewer than three kept lines
separate are one comment, so the second tier is no longer the number of runs. Measured
against the graded blocks:

| reading | fixed (71) | enumerated (40804) | random (12000) |
|---|---|---|---|
| counting runs of moves, three exact engines | 20 | 10657 | 9160 |
| plus the sliding pass every diff tool carries | 31 | 13615 | 9082 |
| drops and adds as separate runs | 9 | 8821 | 9111 |
| the shortest script, reading order only | 7 | 870 | 4374 |
| difflib | 44 | 26916 | 11085 |
| the table; the per-cell frontier; `ok-cells` | 0 | 0 | 0 |

What the change costs the reference, measured on this sandbox, old build against new:

| block | counting runs | counting comments |
|---|---|---|
| medium (400) | 4.34 s | 5.40 s |
| timed 6 (crowded) | 2.77 s | 3.49 s |
| timed 9 (crowded) | 5.21 s | 5.42 s |
| timed 12 (sparse) | 4.62 s | 4.83 s |
| timed 16 (sparse) | 4.77 s | 5.10 s |

So the extra state costs between 1.04x and 1.26x and no budget had to move. The 18 timed
pairs run 0.17 to 5.58 s against 60 s, and the medium block 5.40 s against 40 s.

**Calibration for the next session:** the reference answers timed case 13 in 4.04 s and the
whole medium block in 5.40 s on this host. Measure those two before trusting any timing
recorded here.

## Local gates run here

`preflight.py` no errors (7 warnings, all the documented not-in-kit-layout class);
`solvecheck.py`, `simcheck.py` (mechanical and conceptual) and `hintcheck.py` clean;
`structcheck.py` reports only the two findings the version that cleared the AI screen also
carried; `textcheck.py` burstiness 0.609 against 0.584 for that version, and paragraph sd
44.0 against 36.6. `authoring/corners.py` ok, `authoring/counts.py` as tabled above,
`authoring/fuzz.py` 250 pairs and 2 x 150 with the row engine's memory budgets shrunk so the
checkpoint rebuild and the spilled-mask path run on every pair: 0 mismatches across all four
engine settings. The reference with the diagonal keep left inside a single sliding window,
which is the natural port of the previous rule, is wrong on 877 of 40875 forced cases.

## Gates not run here

- The apt layer in `tests/Dockerfile` cannot be built on this host: `deb.debian.org` answers
  403 through the egress proxy. `tools/ecs_trial.py` drops it, which costs `pkill`, so the
  teardown between the sandbox account and the grading account is the one shipped defence
  the local trial does not exercise.
- The three-agent probe was not run on the new rule: the account hit its session limit.
