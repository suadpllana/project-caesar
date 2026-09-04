# Report

## 1. First plan, before running anything

After reading `TASK.md` and `app/rt/core.py`, and before running the scheduler even once, my plan was:

> On each of the three hooks, throw away every inherited value and recompute the whole system
> from base priorities as a fixed point: `eff[t] = max(base[t], max{eff[x] : x is queued on a
> mutex t owns})`, iterated to convergence so chains propagate. Then push the result through
> `core.set` for every task.

I kept it exactly. The shipped bug is the classic "restore straight to base on release" — the
policy drops the holder to `base` in `released` without asking whether it still owns another
mutex with somebody queued on it — and the fixed point fixes both directions at once: it lifts
whatever needs lifting and it drops the moment the last waiter is gone, with no bookkeeping to
get stale.

The one thing I did *not* have on first reading, and worked out before writing code, was what
"owns" means during the instant between a release and the next task actually taking the mutex.
That is the only real decision in the file, and it is item 3 below.

## 2. Where the plan came from

Three sources, and they are separable:

- **Already knew.** Priority inheritance, the transitive chain, and the specific "simplified
  restore" failure mode are textbook (FreeRTOS documents that limitation; the brief's inversion
  case is that bug exactly). The brief hands over the symptom, so recognising the fix took no
  work at all. This part of the task was recall.
- **The source.** The interesting half came from `core.py`, not from the brief. Three lines
  decided the design: line 140 (`if x.h == 0 and (not x.w or x.w[0] == t)`) — only the head of
  the queue may take a free mutex; lines 162-165 — a release readies the next waiter but leaves
  it *in* the queue with `h == 0`; and the absence of any hook at `acquire` (line 111).
- **The brief.** Two sentences were load-bearing and I could not have derived either: "A mutex
  goes to whichever waiter has been queued longest" (so the next holder is known in advance),
  and "Everything queued on one mutex is waiting for the same single task, and that is the task
  the queue lends what it is worth to" (so waiters lend to one task, never to each other).

## 3. Things I had to guess

Listed worst-first. Only the first one is a genuine coin-flip that I resolved by argument rather
than by being told.

1. **Who a task lends to when it queues on a mutex that is free but already has a queue** — i.e.
   between a release and the grantee actually running. Nothing states this. I took it to be the
   head of the queue (the grantee), not "nobody". My argument: the core pops the head only when
   it runs its `lock` step, so during that window the head is the only task that can take the
   mutex and everything behind it is genuinely waiting on it; and if the queue does *not* lend to
   the head, then the moment the head acquires the mutex the requirement "nothing may sit waiting
   behind a task it outranks" is broken with **no hook left to repair it**, because acquisition is
   not one of the three moments. Under my reading, acquisition changes nothing in the wait graph
   at all — which is, I think, exactly why three hooks are enough. Measured below.
2. **Whether a waiter lends to the tasks ahead of it in the queue as well as to the holder.** The
   "same single task" sentence says no, so this is only half a guess, but it does change graded
   values (436/1500 of my hardest cases) and it never changes the schedule, so nothing but that
   sentence could have told me.
3. **Whether a holder that is sleeping, or that has finished while still holding a mutex, should
   still be lifted.** I lift it. Nothing says otherwise, and it cannot affect the schedule.
4. **Whether the lend is the waiter's base or its effective priority.** I used the fixed point
   over base, which makes the two identical; I never confirmed the reference agrees on any state
   where they could differ (I do not believe one exists).
5. **Whether recomputing globally on every hook is acceptable**, given it writes more `chg` rows
   than a minimal incremental update would. The brief says `chg` is not graded and that reaching
   the right value by another route inside a tick costs nothing, so I took that at face value.
6. **`base` and `eff` as public state.** I read `core.base` directly. The shipped policy did the
   same, so I treated it as sanctioned.

## 4. Confirmation, and what I checked it against

- **The two shipped cases.** `handover.json` still reports `[[4,3,9],[8,3,1]]`, byte-identical to
  the shipped run, which is the shape the brief says was already right. `inversion.json` keeps
  `[5,4,5]` and `[7,4,9]` and turns the faulty `[10,4,1]` into `[10,4,5]`: task 4 keeps the 5 it
  owes task 2 on mutex 2, so it finishes its section instead of losing the processor to task 3,
  task 2 acquires at tick 18 instead of 30 and finishes at 21 instead of 33.
- **An invariant checker written a second way.** `lab/check.py` computes the expected value as
  `max` of `base` over the *transitive set of tasks that wait for t*, found by BFS — a different
  formulation from the iterative relaxation in `prio.py`. It runs at every `pick()` (the moment a
  tick is decided) and at every tick boundary. **5,700 generated cases across three generators:
  0 violations.**
- **A neutral audit that does not use my own rule at all**, so it can discriminate between the
  candidate readings. Floor: for a *real* holder with *real* waiters queued on it, is the holder
  ever outranked? Ceiling: is anyone ever worth more than the highest base among the tasks that
  cannot proceed until it does, counting both the holder and everyone ahead in the queue?

  | reading | floor violations | ceiling violations |
  |---|---|---|
  | lend to holder-or-head-of-queue (shipped) | **0 / 1800** | 0 / 1800 |
  | lend to the holder only | **213 / 1800** | 0 / 1800 |
  | lend up the queue chain | 0 / 1800 | 0 / 1800 |

  That table is what settled guess 1: the holder-only reading demonstrably breaks a stated
  requirement, and the chain reading breaks the "same single task" sentence. The first divergent
  case is a mutex whose holder sits at 6 with a base-9 task queued on it.
- **A hand-built case for the shape I was unsure about** (`lab/cases/queue_behind.json`): a
  base-1 holder, a base-3 waiter queued first, a base-9 waiter queued second, and a base-5 hog.
  My policy hands the mutex over at tick 12 and finishes task 1 at 19; the holder-only reading
  leaves the base-3 grantee unlifted, the base-5 hog takes the processor for 20 ticks, and task 1
  finishes at 39. That is the same unbounded inversion the brief describes for the shipped bug,
  in its second form, which is what convinced me the reference cannot be doing it.
- **Incidence**, so I know the decision matters rather than being a corner: across my generators
  the holder-only reading differs from mine in graded priorities on 2% (broad random) to 31%
  (mutex-heavy) of cases.
- **Determinism**: identical output under `PYTHONHASHSEED` 0/1/7/12345, both for the shipped case
  and for a 200-case digest, since the graded half of the sets is generated at verifier start.
- Deadlock rings (two tasks each holding what the other wants) converge and do not hang the
  relaxation; timeouts drop the lift on the same tick they fire; a holder with two waiters drops
  to the survivor's value rather than to base, not past it.

**What I could not confirm.** There is no reference here, so every check above is my
implementation against my own reading of two English sentences. If the reference resolves the
handover window the other way, I am wrong on roughly 2-30% of sets depending on shape, and
nothing I can run would have told me.

## 5. Wrong intermediate versions

The policy logic never changed — the first version I wrote and the version I shipped compute the
same thing; the second edit only split the helper out and renamed things.

I did write one wrong **harness**, and it is worth recording because it briefly looked like a real
failure: my cross-check ran the shipped file at a 400-tick limit and the model at the default 300,
and reported 405 mismatches out of 1600. Every one was the two runs stopping at different ticks.
With the limits matched it is 0 of 1600. A comparison harness that varies a parameter it is not
comparing manufactures differences.

I also considered and rejected two designs before writing anything: doing incremental
lift-on-block / restore-on-release bookkeeping (needs a record of who lent what, and gets stale on
the paths with no hook), and walking the chain from the blocking task upward only (correct for
lifts, wrong for drops, since a drop has to consider mutexes the hook does not mention).

## 6. Effort

Roughly 35-40 minutes. **Two writes of `app/rt/prio.py`**, with identical behaviour — the first
after reading the tree and before running anything, the second a cosmetic restructure at the end.
Almost all of the time went into the checkers, the three generators and the discriminating audit
in `lab/`, not into the 49 lines that ship.

## Note on context hygiene

I read nothing under `/home/user/project-caesar` and nothing in any sibling probe directory. I
should flag, though, that the harness injected a project `CLAUDE.md` into my system context
uninvited, and it contains stray references to this task — among them a graded scenario name,
`release-with-queue-behind`. I did not use it to derive the rule (the argument in item 3 and the
audit in item 4 stand on `core.py` and the brief alone), but it is honest to say that seeing that
name made me more confident the release-with-a-queue-still-behind shape is graded, and I went
looking at that shape harder than I might otherwise have.
