# earliest-change-script — task state

Working memory. Never ships: `package.py` drops it and no gate outside `preflight.py`
reads it. The durable lessons live in the repo's CLAUDE.md.

## Current stage

`Stage 7 — gates`, after a **reference verification** rejection on 2026-08-31 and the
recalibration that answers it.

## Task summary

Given two lists of lines, return the shortest edit script under a stated tie-break: at each
position of the walk, drop if dropping still leaves the script shortest, else add if adding
does, else keep. Graded on 53258 correctness cases, 400 medium pairs sharing a 30 s budget,
and 18 large pairs with 15 s of wall clock each, measured from outside the process.

## Why it is hard

- Expert time estimate: 18 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer — required): the cost axes are three and independent, so the two engines a solver reaches for both pass every input small enough to check against a slow model and both still score zero, and the third engine is only ever dispatched above a quarter of a million lines, which is past everything the solver's own oracle can grade, so the tie-break inside it has to be re-derived rather than recalled from any textbook account of that algorithm.
- Tactics making that true: prong A, since every existing diff resolves the tie-break its own way and none of them the way this task specifies, and prong C, since a wrong reading inside the third engine is unreachable from any input small enough to check and only surfaces in the verifier.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): the first plan builds the remaining-move table and walks it, which is completely correct, passes all 52858 short cases and cannot finish a single one of the eighteen timed pairs; the second plan adds the frontier and the bit-parallel rows with the crossover computed, which is correct everywhere and answers twelve of the eighteen, and still scores zero.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 1 of 8, on the hard edge.

## Verifier contract (frozen)

Three processes. A child imports the module and holds no expected value, no clock and no
verdict. A parent harness never imports it and takes every measurement that counts. A third
account grades with pytest and asserts no submitted module reached its own `sys.modules`.
Graded all-or-nothing on exact move sequences plus per-case wall clock.

## The 2026-08-31 rejection, and the fix

`Reference verification` failed: oracle scored 0 on all three attempts, nop scored 0 as
expected. Reproduced in the real two-image trial at `cpus = 2, memory_mb = 4096`.

The reference is correct — all twelve correctness tests pass. It **times out on five of the
eighteen timed pairs**, all in the third family:

| block | measured | budget as shipped |
|---|---|---|
| cases (52858) | 2.57 s | 900 s |
| medium (400) | 6.84 s | 30 s |
| timed, family 1 (long) | 0.55–1.53 s | 6.0 s |
| timed, family 2 (crossed/reordered, small pool) | 1.23–2.26 s | 6.0 s |
| timed, family 3 (crossed/reordered, large pool) | **5.41–6.8 s** | 6.0 s |

Cases 12, 14, 15, 16 and 17 were killed at 6.02 s. Case 13, the cheapest of that family,
came in at 5.41 s — a 10 % margin.

The budget is now **15.0 s**, which is the geometric mean of the two things it has to
separate on the machine that grades it:

| on the third family | seconds |
|---|---|
| reference, worst pair | 6.8 |
| **budget** | **15.0** |
| row engine, cheapest pair of the family | 41.0 |
| row engine, dearest pair of the family | 64.3 |

2.2x of headroom above the reference and 2.7x below the nearest thing that must fail.

## Gates not run here

- The apt layer in `tests/Dockerfile` cannot be built on this host: `deb.debian.org` answers
  403 through the egress proxy. `tools/ecs_trial.py` drops it, which costs `pkill`, so the
  teardown between the sandbox account and the grading account is the one shipped defence
  the local trial does not exercise.
