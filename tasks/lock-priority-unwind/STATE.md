# lock-priority-unwind - working notes

Scratch for the next session. Never ships. What was not runnable here is listed under "What was
run".

## Why this task was rebuilt, 2026-09-04

It failed the **easiness probe 3 of 3**. Three trajectories were supplied and are kept at
`probes/lock-priority-unwind/` with the diagnosis in `notes.md` beside them. Read that first.

The short version: `leakcheck` was quiet on all three, so the brief did not hand the plan over,
and the cause was that **the memorised answer was the reference**. The old difficulty argument
claimed prong A - "the memorised answer is one paragraph long and it is correct for exactly one
shape" - and that was false. What the shipped tree does (raise on block, restore to base on
release) is the FreeRTOS simplification, which is the *bug*; the answer a frontier agent recalls
is Linux `rtmutex`-style transitive inheritance, which was the reference. All three agents wrote
it in their first message, in four to five tool calls, and confirmed it with a fuzz harness whose
oracle was the same rule their policy implemented. That policy is `ok-full-solve` almost line for
line.

No leak patch applies to that. The repair was to change what is computed.

## What changed

`rt/core.py` no longer hands a mutex over at a release. It leaves it free, wakes the task at the
head of its queue, and the lock path lets a task take a free mutex only when the queue is empty
or that task is at the front of it. The engine therefore spends real ticks with a queue waiting
on a task that holds nothing.

The graded quantity follows: a task is worth its own priority, or the most urgent task waiting
for it, where the tasks waiting for it are those queued on a mutex it holds **together with**
those queued behind it on a mutex that is free and its to take. A policy that reads holders is
blind to the second half, and so is the oracle such a policy's author would write, which is what
restores prong C.

The `granted` hook is gone. With the handoff it had no work left to do - a task that takes a
mutex it was already at the head of is worth the same before and after - and a hook that cannot
change anything is a false affordance. Three hooks now: `blocked`, `released`, `expired`.

Two statements in the brief became false with the change and were repaired, because a false
transition rule is an unfair task: "a task blocks on a held mutex" (it can block on a free one)
and "the holder still holds it" after a timeout (there may be no holder).

## Measured

| policy | written scenarios failed | drawn sets differing |
|---|---|---|
| reference | 0 of 21 | 0 of 300 |
| four `ok-*` variants | 0 of 21 | 0 of 200 |
| the policy the probe wrote, verbatim | **6 of 21** | **16.7%** |
| shipped tree | 13 of 21 | 24.3% |

`authoring/separation.py` and `authoring/written.py` are the two measurement tools; `hunt.py`
searches drawn shapes for a case that separates a reading the written set is blind to. Two of
the twenty-one scenarios exist because of it.

## The difficulty argument

- Why a frontier agent cannot one-shot the plan: the recalled answer is transitive priority
  inheritance keyed on the owner of a mutex, and this kernel spends real ticks with no owner.
  The recalled answer is now specifically wrong and it is wrong in a way the solver's own
  differential test cannot show them, because they would write the same definition twice.
- Tactics making that true: prong A (A1 the memorised policy is wrong here, A2 the mechanism is
  never named), prong B (B1 the handoff, the queue discipline and what the three hooks are
  called at live in `rt/core.py` and have to be read; B3 the argument the engine passes for the
  task being waited on is zero while a mutex is between owners), prong C (C1 the fence runs both
  ways - four scenarios fail an implementation that raises when it should not; C2 a holder-shaped
  self-check agrees with a holder-shaped policy; C4 the graded artifact is the exact tick-by-tick
  schedule).
- My own attack on the plan: my first plan is the fixed point over holders, and it is what the
  probe wrote. I would not have looked at the release path at all until a scenario failed.
- Estimated solves out of 8: 2 to 4.

## What is graded (contract, frozen)

No work counters anywhere. The graded artifacts are the tick-by-tick schedule, the effective
priority of every task at every tick, the event log, and the completion tick of every task.
Effective priority is pinned exactly by the rule, so it is a state rather than an implementation
choice, which is what keeps this out of the run audit. Editable artifact: `/app/rt/prio.py` and
nothing else.

## What was run

- `authoring/trial.py --all`: 31 targets, 0 unexpected. Reference 1, shipped 0, four `ok-*`
  variants 1, twenty-five cheats 0.
- `tools/docker_trial2.py --all`: the real two-image trial, on this Linux sandbox with the
  daemon up. This covers the privilege drop, the root-owned reward channel, the root-only model
  and ground truth, and the process sweep, none of which the host emulation reaches.
- `tools/readingcheck.py`: all fourteen readings separated by a written scenario.
- `authoring/fuzz.py 800`: reference against the sealed model on 800 drawn sets, 49519 ticks
  simulated, zero mismatches.
- Deadlocking drawn sets, which are about 4% of them and are the one place an incremental walk
  could disagree with a global fixed point: 21 of them collected across eight seeds, and the
  reference plus all four `ok-*` variants agree with the sealed model on every one. A cycle has
  a well defined least fixed point - everything in it converges to the highest priority in the
  cycle - and the walk's iteration cap is above any reachable chain length.
- `preflight` no errors; `textcheck` clean against four briefs that cleared the AI screen;
  `structcheck`, `hintcheck`, `deadfieldcheck`, `catcheck`, `solvecheck`, `forgecheck`,
  `determinism`, `zipcheck` clean.
- The local three-agent probe, on the rebuilt task: **1 of 3**, at 28, 36 and 31 tool calls
  against 4 to 5 on the design that failed. All three derived the handoff from `rt/core.py`. The
  two that failed did so on `prio` alone - identical schedule, event log and finish times - on a
  reading they both named as a guess, which is now settled by one sentence of the brief and ships
  verbatim as `cheat-lends-to-everyone-ahead`. Evidence in `probes/lock-priority-unwind/`.
- A second three-agent probe on the brief with that sentence in it.

## Still outstanding

The **AI-text screen**. This instruction has been refused three times, and CLAUDE.md's verdict
after six refusals across two tasks is that rewriting a brief the screen has already refused,
with the same author, is close to a coin flip with bad odds. The brief had to change here
because the mechanism changed and two of its sentences had become false. The variable that has
never been tried on this bundle is who writes the prose.

## Traps already hit here, do not re-hit them

- `core.holder()` and `core.waiters()` must be total: a KeyError for "not blocked on anything"
  pushes a special case into the policy that has nothing to do with the task.
- A chain scenario needs the middle task to hold one mutex and be blocked on another.
- For a scenario to exercise the handoff at all, something has to outrank the *correctly boosted*
  task at the head of the queue, or the gap closes in one tick and nothing is graded. That means
  a task above the whole chain, arriving on the tick after the release - if it arrives on the
  release tick the holder never gets to release.
- Scenario task ids must be contiguous from 1. `Core.step` indexes `self.ts[t - 1]` first.
