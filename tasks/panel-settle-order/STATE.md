# panel-settle-order - working notes

Scratch for the next session. Never ships: `package.py` drops it and no pipeline gate reads
it. What matters between sessions belongs in CLAUDE.md; this is the per-task detail while
the task is alive. The load-bearing half of the verifier contract is in the module docstring
of `tests/test_outputs.py`, which is the copy that ships and the one the run audit reads.

## Current stage

`Stage 7 - gates`. Built 2026-09-03. Never submitted, never probed.

## Assistant's assigned role

You maintain the incremental recomputation layer behind a dashboard product, so most of your
hard bugs are ordering bugs in a dependency graph that changes while it is being walked.

## Source repository

- Repo URL: none - idea-based task, the engine is written here from scratch.
- Upstream-diff check: nothing is vendored, so there is no upstream to diff against.

## Task summary

A small recompute engine under `/app`. Feeds are written from outside, gauges are computed
from expressions over other entries, one expression form is a conditional so the wiring
changes while a round settles, and latches report settled values and write feeds that become
the next round. The shipped engine pushes each change straight out to whatever reads it. The
agent rebuilds the settling decisions by editing `pnl/ord.py`, `pnl/wire.py`, `pnl/trip.py`
and `pnl/same.py`. `pnl/same.py` is already correct and needs no change.

## Why it is hard

- Expert time estimate: 8 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the brief states the order it wants, so implementing it from the panel's declared wiring is execution, and the thing that is not stated is that the wiring is not a property of the panel - a conditional decides what it reads while it runs, so a gauge that starts reading something further out was at the wrong distance when it ran, and the value it just produced has to be discarded and the gauge run again; the natural implementation of the stated order computes the distances once from the declared graph and is wrong only when a conditional swaps arms, which nothing in the tree does.
- Tactics making that true: A1, A2, B2, C1, C2, C4, prong A, prong C.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan was to read the wiring off the declarations, compute a level per gauge, and drive a priority queue keyed by level with declaration index as the tie-break, recomputing each dirty gauge once; that is wrong in one line, because a level computed from the declarations is stale the moment a conditional takes the other arm, and the gauge then runs before the entry it has just started reading has settled.
- Estimated solves out of 8: 2 of 8, designed at 1.
- Difficulty score anchor: not yet anchored.
- Leak audit (docs/DIFFICULTY.md): the engine ships no expected output, no comments and no
  self-describing names; `deadfieldcheck` is clean, so nothing is written and never read;
  `onelinecheck` finds no exact rule at depth <= 2 for any of the three graded decisions;
  the four shipped panels were checked to make sure the natural wrong implementation agrees
  with the reference on every one of them, so the second discovery has no local signal; and
  the graded set is three hundred panels built from a nonce made after the agent stops.
- Expert path, described step by step: read `pnl/lex.py` for the panel language and
  `pnl/loop.py` for the round structure and the frozen interface; drive `panels/hold.txt`
  and see a gauge published before the entry it reads exists and a latch tripped on that
  value; derive that the order has to be by distance from the feeds and that a gauge runs
  once; implement it from the declared wiring; then notice that `pick` decides what it reads
  as it runs, so the distance belongs to the run and not to the panel, and that a gauge which
  turns out to read something at or beyond its own distance has run too early and must be
  discarded and run again; then the wiring half, dropping entries it no longer reads so they
  stop waking it; the latch rules are stated and are execution.
- Originality check: searched for write-ups of ordered recomputation with dependencies that
  change mid-pass. The general technique is documented in several frameworks; the exact
  order this grades, the discard-and-rerun rule, and the latch write-back semantics are not
  written up anywhere found, and the brief names none of the vocabulary that would retrieve
  them.

## Verifier contract - FROZEN after Stage 2

- Artifacts: `/app/pnl/ord.py`, `/app/pnl/wire.py`, `/app/pnl/trip.py`, `/app/pnl/same.py`.
- What is checked: the ordered ledger for every panel and the values it was left holding,
  exactly, all or nothing, over 20 enumerated panels and 300 built inside the verifier from
  a run-time nonce.
- Tolerances: none. Integer arithmetic throughout.
- Ground truth: `tests/gt.json` for the enumerated set, root-only, re-proved at verification
  time by `tests/oracle.py`; the generated set is answered by the model after the run.
- Deliberately not graded: how many times a gauge is evaluated before it commits, whether
  wiring is recorded on a discarded run, caching between rounds, data structures.

## Measured, 2026-09-03

| reading | wrong on 500 generated panels |
|---|---|
| shipped tree | 99.8% |
| tie-break by name | 94.4% |
| latch tripped on reach | 76.2% |
| distance stepped out once | 57.6% |
| stale entry still wakes it | 29.8% |
| **distance settled at build and frozen (the near-miss)** | **25.6%** |
| distance only ever grows | 10.6% |
| wiring recorded only on commit | **0.0% - ships as a variant** |

- reference against the sealed model: 800 panels, 29566 rows, 0 disagreements.
- two independent correct engines agreed on 4000 prototype panels before any code shipped.
- `docker_trial2 --all`: 23/23. `--variants`: 3/3.
- `readingcheck`: all 10 wrong readings separated by an enumerated panel.
- `onelinecheck`: no graded decision has an exact rule at depth <= 2.
- `determinism.py`: identical panels across 4 hash seeds.
- `field_report`: 0 panels where the final values catch what the ledger does not.
- double-commit panels: 1 in 20000, excluded by `oracle.check`.

## Decisions and their reasons

- **Gauges may reference entries declared later.** The first design let a gauge read only
  earlier-declared entries, which makes declaration order a valid topological order and a
  trivial declaration-order sweep correct. That collapses the whole task. Do not re-impose
  it. Acyclicity is kept by the generator building the mention graph from a rank order that
  is independent of declaration order.
- **The order is stated; the maintenance of it is not.** Stating the tie-break and the
  distance definition removes three lotteries that were measured at 94%, 57% and 10%. The
  discard-and-rerun consequence stays underived - it is the task.
- **The four shipped panels must not expose the second discovery.** Each was checked so that
  the frozen-distance near-miss produces the same ledger as the reference on it. If a panel
  is ever added under `environment/app_src/panels`, re-run that check.
- **Panels needing a gauge to run twice in a round are excluded.** Measured at 1 in 20000.
  Excluding them lets the brief state "once in a round" as a plain requirement.
- `pnl/same.py` is declared and needs no change, which is deliberate.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | `docker_trial2 --build` |
| No answer leaked into agent image | pass | sweep cheat finds nothing |
| oracle = 1 | pass | real two-image trial |
| nop = 0 | pass | real two-image trial |
| Cheats all score 0 | pass | 21 of 21, each caught by the layer aimed at it |
| Variants all score 1 | pass | 3 of 3, real verifier |
| `preflight.py` | see handover | |
| `harbor check` rubric | not run | harbor is not installed here |
| three-agent probe | NOT RUN | the user asked for none |

## Open questions and next steps

- The task has never faced the pipeline and has never been probed. The band estimate is a
  design claim, not a measurement.
