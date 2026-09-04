# lock-priority-unwind, easiness probe: 3 of 3 (trajectories supplied)

`trial1.md`, `trial2.md`, `trial3.md` are the agents' own words only. The brief was stripped
out of each before they were written here, because `leakcheck.py` is circular against a file
that quotes the instruction back.

## Attribution, mechanically

| check | result | rules out |
|---|---|---|
| `leakcheck` on all three | nothing above the floor | **mode A** - the brief did not supply the wording |
| `onelinecheck` | no `authoring/decisions.py`, unmeasured | - |
| `deadfieldcheck` | clean | the false-affordance class |
| one-shot write, then a self-built fuzz goes green | **all three** | **mode C** |

Tool calls to a finished policy: 4, 3 and 5. No intermediate wrong version in any of the three.

## The cause is not a leak - the memorised answer IS the reference

The difficulty argument in `task.toml` claims prong A: "the memorised answer to this is one
paragraph long and it is correct for exactly one shape". That is **false**, and this is the
falsification. The memorised answer for a *correct* kernel is Linux `rtmutex`-style transitive
inheritance, and that is exactly the reference. What the shipped tree does (raise on block,
restore to base on release) is the FreeRTOS simplification - it is the *bug*, not the recalled
plan. Nobody recalled it.

All three agents wrote, in their first substantive message and before running anything:

- trial1: "A task is worth the larger of its base priority and the worth of any task queued on
  a mutex it currently holds", to a fixed point.
- trial2: "A task is worth its base, or the worth of the most urgent task queued on any mutex
  it holds, whichever is larger", to a fixed point.
- trial3: same, plus "checking after every tick that every task's worth matched the
  base-or-max-waiter rule derived from the live mutex state. All passed."

That is `authoring/variants/ok-full-solve/prio.py` almost line for line, and it scores 1.

## Why no leak patch applies

Trial 3's fuzz is the whole problem in one sentence. Its oracle was "recompute worth from the
live mutex graph and compare" - which is the definition the reference is an optimisation of, so
the check is **circular and it still passes**. The graded quantity was a pure function of the
live lock graph, the graph is exposed through `core.held`, `core.waiters`, `core.holder` and
`core.blocking`, and a complete statement of the rule is therefore a brute-force oracle. Same
shape as `alias-settle-report`, arrived at from the other side: there the transition table was
the oracle, here the state function is.

Deleting sentences cannot move this. `leakcheck` is quiet, so there is nothing to delete, and
the rule has to stay stated for the task to be fair.

## The repair

Change what is computed, per "A pure function at its ceiling" in CLAUDE.md. The graded value
must stop being a function of *who holds what*, so that the recalled engine answers the wrong
question. See the handoff entry in CLAUDE.md.

---

# The rebuild, probed: 1 of 3, and the two losses were a coin flip (2026-09-04)

`rebuild-round-1/` holds the three agents' own reports and the policy each of them submitted,
graded through the real verifier rather than believed.

| agent | tool calls | wall clock | reward |
|---|---|---|---|
| 1 | 28 | ~15 min | **0** |
| 2 | 36 | ~15 min | **1** |
| 3 | 31 | ~15 min | **0** |

Against 4 to 5 tool calls and about two minutes on the design that came back 3 of 3, so the
mechanism change did real work. All three found the handoff by reading `rt/core.py` - agent 1
from "there is no hook when a waiter acquires a mutex", agent 3 from the same fact, agent 2 from
that plus the `h == 0` argument at `blocked`. None of them recalled it; every one of them derived
it, which is the property the rebuild was for.

**But the two losses were not the difficulty.** Both failed on `prio` alone: identical schedule,
identical event log, identical finish times, and eight scenarios where one blocked task carries a
different number. Both had written the same reading - a task queued ahead of you is in your way
exactly as the holder is, so lend to it too - and **both flagged it, unprompted, as the one thing
they had to guess**:

> agent 1: "the exact tick at which the lift begins ... produces an identical schedule and differs
> only in the graded per-tick priority values, so no experiment available to me distinguishes the
> two. That is the one place I am exposed."

> agent 3: "Between the two surviving readings nothing is decisive: they differ on the graded
> per-tick priority table in 1.5% of random sets and on the schedule in 0%. ... That is the one
> place I can be wrong, and no oracle I can build would tell me."

That is the `guard-mark-unwind` defect exactly, and it is also a run-audit exposure: a graded
number that two behaviourally identical implementations disagree on. It was decided in the brief
- one sentence, "Everything queued on one mutex is waiting for the same single task, and that is
the task the queue lends what it is worth to" - and agent 3's policy now ships verbatim as
`cheat-lends-to-everyone-ahead`, separated by eight written scenarios and 19.3% of drawn sets.

**The lesson that generalises: when a probe agent volunteers a guess, that is the finding, and it
outranks the score.** Both losing agents named the rule before anybody graded them. Reading the
score alone would have said "1 of 3, in the band, ship it", and what shipped would have been a
lottery on a convention with no behavioural consequence.
