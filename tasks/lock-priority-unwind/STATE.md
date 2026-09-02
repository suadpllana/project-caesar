# lock-priority-unwind - working notes

Scratch for the next session. Never ships. The bundle is complete and gated locally; what was
not runnable on this host is listed under "What was run".

## Why this task exists

`segment-merge-horizon` was rejected by the **similarity screen** on 2026-08-15. The diagnosis
is in CLAUDE.md under "The similarity rejection": the brief was not the problem (0.249 token
overlap, lower than two pairs that both passed), but the bundle shipped near-identical verifier
plumbing AND graded the same thing four earlier submissions grade - work counters against an
unpublished budget. This task deliberately grades **nothing of the kind**. There is no work
counter anywhere in it.

## Seed

Zephyr RTOS `kernel/mutex.c` and FreeRTOS, whose documentation states the limitation outright:
priority inheritance is implemented in a simplified form, and a task holding more than one
mutex may not have its priority restored until it releases all of them. Linux `rtmutex.c`
solves the same problem properly with a waiter tree. The simplified version is what every
textbook and nearly every hobby kernel writes down, which is Prong A: the memorised answer is
specifically wrong, and it is wrong in a way that only shows up in shapes the write-ups do not
cover.

Not vendored. The simulator is written here from scratch in integer arithmetic.

## The difficulty argument

- Why a frontier agent cannot one-shot the plan: the retrieved answer is raise-on-block and
  restore-on-release, which is correct for one holder and one waiter and wrong for every other
  shape, so the better the source the more confidently wrong the plan built on it.

Three findings, and the naive policy misses all three:

1. **Release is a recompute, not a restore.** A holder of two mutexes that releases one must
   fall to what the tasks still waiting on the others are worth, not to its own priority.
2. **Blocking is not one deep.** A waiter blocks on a holder that is itself blocked; the
   urgency has to travel the chain or it stops at the first link and never reaches the task
   actually holding the processor.
3. **A timeout lowers a boost.** A waiter that gives up stops being a reason for anybody to be
   urgent. This is the one measured solutions miss, because a timeout looks like a change to
   the waiter and is in fact a change to the holder.

- Tactics making that true: prong A (A1, A2), prong B (B1), prong C (C1, C4).
  A1 the memorised policy is wrong here and A2 the mechanism is never named; B1 the schedule,
  the queue discipline and the handover order live in `rt/core.py` and have to be read; C1 the
  fence runs both ways - three scenarios fail an implementation that raises when it should not,
  and C4 the graded artifact is the exact tick-by-tick schedule.

- My own attack on the plan: my first plan is raise-on-block, restore-to-base-on-release, and
  it is correct on `one-mutex-one-waiter` and wrong on eight of the fourteen scenarios. I would
  not have thought about the timeout at all until I saw a scenario where a waiter gives up.
- Estimated solves out of 8: 2 to 3. This shape - many interacting lifecycle rules, exact
  assertions, no work counters - is the shape `typeahead-query-controller` used, and that one
  cleared the difficulty probe.

## What is graded (contract, frozen)

Not values plus work counters. The graded artifacts are:

- the **tick-by-tick schedule**: which task ran at each tick, or nothing;
- the **effective priority of every task at every tick**, which the spec pins exactly, so it is
  a state rather than an implementation choice;
- the **event log** the core produces: acquire, block, release, timeout, sleep, done;
- the completion tick of every task.

Effective priority is defined so there is no freedom, which is what keeps this out of the run
audit: a task is worth its own priority, or the highest effective priority among the tasks
blocked, directly or transitively, on mutexes it holds - whichever is greater. Over-raising is
therefore wrong, not merely wasteful, and three scenarios exist to catch it.

That definition is the contract and it stays here. **It is no longer written in the brief**,
which is the whole of the easiness repair of 2026-09-02: the probe solved this task 3 of 3 by
transcribing that sentence out of `instruction.md`. The brief now states the two requirements
the definition satisfies and leaves the definition to be derived. See CLAUDE.md, "The easiness
rejection on a task whose rule was printed in the brief".

Editable artifact: `/app/rt/prio.py` and nothing else.

## What exists and is proven

- `environment/app_src/` - the whole engine. `rt/core.py` is the tick loop, the ready queue,
  the FIFO handover and the trace; `rt/prio.py` is the shipped naive policy; `rt/boot.py`,
  `rt/task.py`, `rt/lock.py`, `run_sched.py`, `conf/sched.json`.
- `solution/prio.py` - the reference. One recomputation walked up the chain, called from all
  four hooks. About sixty lines. It sits beside `solve.sh`, which copies it in rather than
  inlining it; moved out of `solution/ref/` on 2026-09-02, see the solve.sh note below.
- `tests/scen.py` - fourteen scenarios.
- Measured: the reference and the shipped policy produce **different schedules on 8 of the 14**.
  The three that agree deliberately do so - they are the must-still-work fences. Verified with
  a scratch comparison harness.

Grounded symptom for the brief, from a real run of `release-with-queue-behind`: the shipped
policy drops task 4 to its own priority at tick 10 while task 2 is still waiting on the other
mutex it holds, so task 2 - the second most urgent thing in the system - does not get the mutex
until tick 29 and finishes at 33. The reference hands the mutex over at tick 17 and task 2 finishes at 21.

## What was run

- `authoring/trial.py --all`: 23 targets, 0 unexpected. Reference 1, shipped 0, four `ok-*`
  variants 1, seventeen cheats 0.
- `authoring/cheat_report.py`: every cheat fails on the axis it was aimed at. The one to read is
  `hand-back-the-schedule`, which carries the recorded schedules, and fails the drawn scenarios.
- `authoring/fuzz.py 300`: reference against the sealed model on 300 drawn task sets, 8887 ticks,
  zero mismatches.
- `textcheck` clean against `rollout-cache-coherence` and `checkpoint-resume-drift`;
  `structcheck` and `hintcheck` clean; `preflight` clean; `tools/simcheck.py` clean on both axes.
- **`tools/docker_trial2.py --all`: 19/19, and `--variants`: 4/4, on 2026-09-02.** The real
  two-image trial, run for the first time on this task. Oracle 1 (47 passed), nop 0, every
  cheat 0, all four correct variants 1. This is what previously said "not run": the privilege
  drop, the locked reward channel, the root-only model and ground truth and `tests/sweep.py`
  are now exercised for real rather than emulated. The built agent image was inspected file by
  file and carries eight files and no bytecode.
- **Still not run:** `harbor` is not installed here, so `harbor check` has never been run
  against this bundle. Everything above is docker directly, which is what `docker_trial2.py`
  reproduces.

## Traps already hit here, do not re-hit them

- `core.holder()` and `core.waiters()` must be total: returning a KeyError for "not blocked on
  anything" pushes a special case into the policy that has nothing to do with the task.
- The handover is **FIFO**, not by priority. With priority-ordered handover the acquire-side
  hook is dead code, because the task the mutex goes to always already outranks everyone left
  in the queue. FIFO is what makes it load-bearing, and it is a real design.
- A chain scenario needs the middle task to **hold one mutex and be blocked on another**. Three
  of my first drafts did not form a chain at all and the naive policy passed them.
