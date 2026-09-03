# Brief kit: lock-priority-unwind

For the task owner, to write `tasks/lock-priority-unwind/instruction.md` in their own words.

Why this file exists: the AI-text screen has rejected five model-written versions of this brief
and accepted one, and that one only as exact bytes. The repo's own conclusion after the same
pattern on `typeahead-query-controller` was that the variable left to change is who writes the
prose. Everything below is a fact list. Nothing in it is a sentence to paste; do not copy
wording from this file or from any earlier brief.

## What the reader has in the container

- `/app` is a small fixed-priority kernel simulator, Python 3, no dependencies.
- `/app/rt/core.py`: the clock, the ready queue, the mutex table, and the choice of who runs.
  Not editable. No comments in it. It has no helper for what a task holds, who is queued on a
  mutex, or what a task is blocked on; the mutex table (`ms[m].h` holder, `ms[m].w` queue) is
  read directly.
- `/app/rt/prio.py`: the policy. The ONLY file taken from the container. Class `Prio`,
  `__init__(self, core)`, methods `blocked(self, w, m, h)`, `granted(self, t, m)`,
  `released(self, t, m)`, `expired(self, w, m, h)`. Names must stay. It sets a task's current
  priority with `core.set(t, p)`; `core.base[t]` is the starting priority, `core.eff[t]` the
  current one.
- `/app/rt/boot.py`, `/app/rt/task.py`, `/app/rt/lock.py`, `/app/conf/sched.json` (tick
  limit 200), `/app/run_sched.py`, `/app/cases/inversion.json`, `/app/cases/handover.json`.
- A case file is a list of tasks: `id`, `base` (starting priority), `start` (arrival tick),
  `prog`. Program steps: `["run", n]`, `["lock", m, timeout]` with `-1` for no timeout,
  `["unlock", m]`, `["sleep", n]`.
- One processor. One task per tick. Bigger number is more urgent. Ties go to whoever became
  runnable first.
- `/app/run_sched.py <case>` prints one record per line: `trace` (tick, task that ran; 0 for
  idle), `prio` (tick, then the current priority of every task in id order), `ev` (acq, blk,
  rel, exp, slp, done, each with tick, task, mutex), `chg` (tick, task, new priority: every
  change the policy made), `done` (task, finish tick), `ids`, `ticks`.

## The symptom to quote, from a real run of the shipped tree

`python /app/run_sched.py /app/cases/inversion.json`, verbatim:

    chg   [5, 4, 5]  [7, 4, 9]  [10, 4, 1]
    ev    ["acq", 0, 4, 1] ["acq", 0, 4, 2] ["blk", 5, 2, 2] ["blk", 7, 1, 1]
          ["rel", 10, 4, 1] ["acq", 10, 1, 1] ["rel", 13, 1, 1] ["done", 14, 1, 0]
          ["done", 26, 3, 0] ["rel", 29, 4, 2] ["acq", 29, 2, 2] ["rel", 32, 2, 2]
          ["done", 33, 2, 0] ["done", 33, 4, 0]
    trace task 4 ticks 0-2, task 3 ticks 3-4, task 4 ticks 5-10, task 1 ticks 11-13,
          task 3 ticks 14-25, task 4 ticks 26-29, task 2 ticks 30-32, idle at 33
    done  [1, 14] [2, 33] [3, 26] [4, 33]

What the numbers mean, for your own understanding (do not explain the mechanism in the brief):
task 4 (base 1) takes mutex 1 and mutex 2 at tick 0. Task 3 (base 4) arrives at 3 and only ever
runs. Task 2 (base 5) arrives at 5 and blocks on mutex 2. Task 1 (base 9) arrives at 7 and
blocks on mutex 1. The first two priority changes lift task 4 to 5 and then 9; both are right.
At tick 10 task 4 releases mutex 1 and the policy drops it to 1 while task 2 is still queued on
mutex 2, which task 4 still holds. Task 3 then holds the processor from 14 to 25 ahead of task
2, which outranks it by one. Task 2 gets mutex 2 at 29, twenty-four ticks after asking, and
finishes at 33.

`/app/cases/handover.json` is a shape the shipped policy gets right: `chg` is `[4, 3, 9]` and
`[8, 3, 1]`, task 1 finishes at 12, tasks 2 and 3 at 18.

Quote only the broken run. Never write down what a correct policy produces for any case.

## What the verifier grades, all-or-nothing

- The current priority of every task at every tick, exactly, on every scenario.
- The trace, the event log in order, and the finish tick of every task. All of these come out
  of `core.py`, so the priority table is what the policy controls and the rest follows.
- Both directions. Too low fails. Too high fails. Scenarios exist for: a task lifted when
  nothing waits on it; a task lifted above what any waiter is worth; a task left lifted after
  its last waiter has gone.
- `chg` is not graded. The route inside one tick is free.
- Fourteen written scenarios plus twelve generated at verification time from a seed minted
  then, same shapes.
- Only `/app/rt/prio.py` is copied out. Every other file is restored from an untouched copy
  before grading.

## The requirement the brief has to state

State both halves, as requirements, once each:

- Floor: a task may not sit waiting behind a task it outranks.
- Ceiling: a task may not be worth more than its own priority unless something waiting on it,
  directly or through a chain, accounts for the difference; that ends the moment the waiter is
  gone.

## The input space the brief has to say occurs and is graded

- A waiting task can itself hold a mutex with a queue behind it (chains).
- A wait with a timeout can run out while the holder still holds the mutex.
- A task can hold more than one mutex at once.

## Engine facts you may state or leave to `core.py`

The previous brief stated all four and the concision reviewer objected; they are readable from
`core.py` either way. If you state any, one plain sentence each, no explanation of why.

- A released mutex goes to the waiter queued longest, not the most urgent one.
- A wait that runs out simply ends; the task moves to its next step; the mutex is untouched.
- The policy is called at exactly four moments: a task blocks, a mutex is granted, a mutex is
  released, a wait times out.
- The scheduler reads the priority the policy set when it picks who runs.

## Never write

Each of these has cost a rejection somewhere in this repo.

- The name of the technique or any of its vocabulary: inheritance, inherit, boost, fixed
  point, recompute, walk, chain propagation, transitive.
- That a release must recompute rather than restore; that urgency must travel along a chain;
  that a timeout must lower the holder. These three are what the solver has to find.
- How many things are wrong, or that anything is "one bug" or "three bugs".
- A wrong rule followed by why it is wrong.
- Which part is the hard part, or what "the whole task comes down to".
- The correct output of any case.
- The words "hint", "trick", or "the key is".

## Format

- Plain ASCII, LF line endings, no blank first line.
- Every path and filename in backticks.
- Prose paragraphs only. No headings, no bullets, no numbered lists, no code blocks, no tables.
- Roughly 800 to 1000 words.
- The last paragraph, alone, exactly:

    You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.

## What happens when you send it back

The session runs `tools/textcheck.py` against three briefs that passed, `tools/structcheck.py`,
`tools/hintcheck.py`, and walks every graded assertion against your sentences in both
directions. It reports what is missing or what leaks. It does not rewrite your sentences.
