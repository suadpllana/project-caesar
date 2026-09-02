# earliest-change-script — task state

Working memory. Never ships: `package.py` drops it and no gate outside `preflight.py`
reads it. The durable lessons live in the repo's CLAUDE.md.

## Current stage

`Stage 7 — gates`, after an **easiness rejection (3 of 3)** on 2026-09-02 and the rule
change that answers it. Not yet resubmitted.

## Task summary

Given two lists of lines, return the shortest edit script under a three-tier rule: fewest
moves; of those, fewest hunks, a hunk being a maximal run of consecutive moves in the
reading; of those, the reading that comes first with drop ahead of add ahead of keep.
Graded on 52865 correctness cases, 400 medium pairs sharing a 40 s budget, and 18 large
pairs with 60 s of wall clock each, measured from outside the process.

## Why it is hard

- Expert time estimate: 24 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer — required): every fast diff technique computes how many moves remain from a position and nothing else, and the reading-order tier is a greedy walk over exactly that number, so the engines an expert recalls answer the first and third tiers natively and are wrong on the second on a quarter of the enumerated block; the hunk count is a second quantity with its own recurrence that is only affordable on the cells that lie on some shortest path, and the natural implementation of that restriction, one cell at a time, is correct on the two families a solver can reach with a frontier and dies on the third, where the shortest-path cells between one match and the next are whole rectangles and only a formulation over the matches themselves, by rank, is finite.
- Tactics making that true: prong A, since every existing diff answers the first tier and slides hunks afterwards by a heuristic that neither minimises them nor respects the reading order, and prong C, since the third family is the only place the per-cell formulation fails and no pair small enough to check against the table looks like it.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): the first plan is the table of (moves, hunks) pairs walked from the start, which is completely correct, passes all 52865 short cases and cannot finish the medium block; the second plan is the shortest-script engines from the previous version of this task with the hunk count repaired afterwards by sliding, which is wrong on 6352 of the enumerated cases; the third plan is the frontier with the hunk recurrence on every shortest-path cell, which is correct everywhere and answers twelve of the eighteen timed pairs.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 2 of 8. The easiness probe solved the previous version 3 of 3 with a strict superset of the reference built in three hours; the added tier removes every recalled engine's sufficiency and adds two derivations, and the honest estimate is that one such agent in four finishes both inside four hours.

## Verifier contract (frozen)

Three processes. A child imports the module and holds no expected value, no clock and no
verdict. A parent harness never imports it and takes every measurement that counts. A third
account grades with pytest and asserts no submitted module reached its own `sys.modules`.
Graded all-or-nothing on exact move sequences plus per-case wall clock. The definitional
model is a two-state table over (moves, hunks) pairs, held to an exhaustive enumeration of
every script on 15252 short pairs; the fast implementation is held to the model on all
40865 fixed and enumerated cases with each of its two engines forced in turn.

## The 2026-09-02 easiness rejection, and the fix

3 of 3. The trajectory is at `probes/earliest-change-script/` with notes. The agent derived
the greedy on sight from the stated rule, wrote a brute-force oracle first, built four
engines including the journaled-thresholds one, and forced each on small inputs against
its oracle. Its module was a superset of the reference, so no budget could separate them.

The repair is a second tier to the rule, fewest hunks among shortest scripts. Measured:

| | fixed (61) | enumerated (40804) | random (12000) |
|---|---|---|---|
| previous reference, reading order only | 9 | 9885 | 8601 |
| plus hunk sliding afterwards | 12 | 6352 | 7263 |
| drops and adds as separate hunks | 7 | 10436 | 4696 |
| difflib | 28 | 20243 | 10130 |
| table, per-cell frontier, ok-cells variant | 0 | 0 | 0 |

Container timings on the 2026-09-02 sandbox at `cpus = 2, memory_mb = 4096`, before
scaling by the 2.7 host factor recorded in `tools/ecs_trial.py`:

| block | reference | budget |
|---|---|---|
| cases | 4.4 s | 900 s |
| medium (400) | 3.4 s | 60 s |
| timed, long | 0.38–0.74 s | 60 s |
| timed, crowded | 0.76–3.12 s | 60 s |
| timed, sparse | 4.44–5.77 s | 60 s |

**The sandbox's speed drifted by 3-4x within the session.** The same container, image and
pair measured 4.6 s at 19:00 and 11-21 s at 20:05, with nothing else running and the
child's peak RSS at 472 MB, so it is not memory. The budgets above were widened to 60 s
per pair and 40 s for the medium block on the strength of the slow state; nothing the
timings separate is within an order of magnitude of either line.

## The two-image trial, 2026-09-02

`tools/ecs_trial.py` on the sandbox, `--cpus=2 --memory=4096m`, apt layer dropped:

| submission | reward | caught by |
|---|---|---|
| oracle | 1 | - |
| nop | 0 | every correctness block and both budgets |
| variant `ok-cells` | **1** | - |
| `lex_first_only` | 0 | fixed, random, enumerated, medium, large answers |
| `slide_hunks_afterwards` | 0 | fixed, random, enumerated, medium, large answers |
| `split_hunks` | 0 | every answer block, and both budgets |
| `delegate_to_difflib` | 0 | every answer block, and the large budget |
| `forge_the_result` | 0 | the tamper record, and every answer block |
| `table_walk` | 0 | medium answers and budget, large answers and budget |
| `cells_on_shortest_paths` | 0 | large answers only: the six sparse pairs never come back |

## Gates not run here

- The apt layer in `tests/Dockerfile` cannot be built on this host: `deb.debian.org` answers
  403 through the egress proxy. `tools/ecs_trial.py` drops it, which costs `pkill`, so the
  teardown between the sandbox account and the grading account is the one shipped defence
  the local trial does not exercise.
- The three-agent probe was not run on the new rule this session.
