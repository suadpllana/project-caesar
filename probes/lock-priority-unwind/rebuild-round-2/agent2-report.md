# Report

## What I shipped

`app/rt/prio.py` keeps no state of its own. All three hooks call one routine that recomputes
every task's worth from the core's current state:

```
eff[t] = max( base[t], max{ eff[w] : w is queued on a mutex whose owner is t } )
```

taken to a fixpoint, so a lift travels the whole chain. "Owner" of a mutex is its holder, or,
when the mutex is free but still has a queue, the task at the head of that queue - the one that
is about to take it, and the only one that can.

## 1. What was your very first plan, before you ran anything? Did you keep it or throw it away?

Before running anything, after reading only `TASK.md`: transitive priority inheritance. On a
block, push the waiter's priority up the chain of holders; on a release, recompute the releasing
task as `max(base, best waiter across the mutexes it still holds)` instead of slamming it back to
base; on a timeout, drop the departed waiter's contribution the same way.

I kept the substance of it. Two things changed after reading `core.py`:

- I dropped incremental push/pull in favour of recomputing the whole table at every hook. Same
  model, but there is no way for stale bookkeeping to survive, and the brief says explicitly that
  the route to a value inside a tick is not graded.
- I added the part I did not have at the start, which is the one interesting decision in the task:
  when a mutex is let go with a queue still on it, the head of that queue inherits from the rest of
  the queue. My first plan would have left the new holder at its base priority and re-created the
  inversion one link down the chain.

## 2. Where did that plan come from?

The inheritance idea is textbook and I already knew it; the brief's opening paragraph describes it
in words ("whatever is standing between it and that mutex has to be lent enough urgency to get out
of the way"). The brief also settled one thing I would otherwise have had to guess: "Everything
queued on one mutex is waiting for the same single task" - so a queue does not chain within itself,
it lends to one task.

The prospective-owner rule came from the source, not the brief. Three things in `core.py` pointed
at it:

- The three hooks are the only calls, and there is **no hook at acquire**. `run_one` does
  `x.w.pop(0)` and `acquire(t, m)` with the policy never told. So if the new holder is not lifted
  at the release, it can never be lifted at all.
- On unlock the core wakes the next waiter (`nxt = self.top(m); ready(nxt)`) *before* calling
  `released`, so the policy is deliberately shown who is next.
- The woken task stays in `x.w` until it runs, so "free mutex with a queue" is a real, readable
  state rather than something I had to infer.

That also makes the model closed: the only state change with no hook is head-of-queue becoming
holder, which under this reading changes nothing, so three hooks are exactly sufficient. That
closure is what convinced me the reading is the intended one.

## 3. Which things did I have to GUESS?

1. **The big one: whether the head waiter of a just-released mutex inherits from the rest of the
   queue.** Nothing states it. Argued from the absence of an acquire hook, from the core waking
   `nxt` before calling `released`, and from the fact that the alternative reproduces exactly the
   inversion the brief opens by forbidding. Measured to matter on 69 of 1500 generated cases. If
   my submission is wrong anywhere, it is here.
2. **That inheritance is transitive up a chain.** The brief says a waiting task can have a queue
   of its own behind it and that the graded sets do that, but never says the lift travels the whole
   way. I assumed it does.
3. **Whether a waiter lends its base or its already-inherited worth.** These are equal under
   transitive max propagation, so the guess is free, but I did have to notice that.
4. **That a task is never worth less than the priority it started with.** The brief only bounds
   worth from above.
5. **A task that finishes while still holding a mutex** (possible in a deadlock). I let its
   waiters go on lending to it. It is never picked, so nothing observable turns on it.
6. **Adding helper methods to `Prio`.** The brief pins the class name, the constructor and the
   three method names; I kept all of those exactly and added two helpers alongside.
7. **Ordering inside `settle`.** I re-set every task each time, so `chg` carries entries the
   shipped policy would not have emitted. The brief says the change list is not graded.

## 4. Where did I get CONFIRMATION?

- **Against the brief's own numbers.** `inversion.json` keeps `[5, 4, 5]` and `[7, 4, 9]`, and the
  third change becomes `[10, 4, 5]` - task 4 held down to the 5 that task 2 still accounts for on
  mutex 2 - then `[17, 4, 1]` when it finally lets mutex 2 go. Task 2 now acquires at tick 18 and
  finishes at 21 instead of 33. `handover.json` reproduces `[4, 3, 9]` and `[8, 3, 1]` exactly, as
  required.
- **Against an independently written model.** `lab/model.py` restates the two graded requirements
  directly as `eff[t] == max(base[t], max base over the tasks that transitively wait on t)`, and
  computes it by walking chains *upward* from each waiter - a different shape of computation from
  the downward fixpoint in `prio.py`.
- **Against the core itself, at every point it reads a priority.** `lab/check.py` subclasses `Core`
  and checks that identity on every `pick`, every `acquire`, after every step, after every expiry,
  and on every `ids()` read - which includes the end-of-tick snapshot that is the graded quantity.
  **1500 generated cases, 0 drift.** This is the check that actually matters, because it tests
  whether three hooks are *enough*: any state change that slipped through unhooked would show up
  as the table lagging reality.
- **Against a count of what the suite contains**, so the clean result means something:
  80 releases with someone still queued behind the head, 941 lifts that travel two hops,
  72 timeouts, 27 mutual deadlocks, longest queue 4.
- **By falsifying the alternative.** I implemented the other reading (`lab/alt_b.py`, a queue lends
  only to a real holder) and ran it on a case built to separate them: the priority-9 task lands at
  tick 17 under my policy and at tick 37 under the alternative, because a priority-5 task runs its
  whole 20 ticks while the urgent one sits behind an unlifted priority-3 task. That is the
  unbounded inversion the brief's first paragraph exists to forbid.
- **Differentially against the shipped policy**: it disagrees with mine on the per-tick worth in
  146 of 1500 generated cases, so the fault is not confined to the shape in `inversion.json`.

## 5. Did I write an intermediate version that turned out to be wrong?

`prio.py` itself: no. One write, no revisions, correct on both shipped cases first time.

**My checker was wrong, and it lied convincingly.** The first version verified the invariant on
every `ids()` call - including the `ids()` call on the first line of `settle()` itself. It reported
356 of 1200 cases drifting, which looked exactly like a real bug in my policy. It was the
instrumentation observing a half-finished update. Fixed by wrapping the policy so the invariant is
only tested between hook calls, after which the same suite came back clean. I nearly spent the
afternoon "fixing" a correct file against a broken gate; what saved it was dumping a stack trace at
the first disagreement instead of reasoning about which of my rules was wrong.

The earlier, smaller version of the same lesson: my first generator produced only 50 releases with
a queue behind the head across 400 cases, so the decision the whole task turns on was barely
exercised. I counted the shapes rather than trusting the case count.

## 6. Roughly how long, and how many edits to `prio.py`?

About 30 minutes end to end. **One** write of `prio.py` and no subsequent edits. Most of the time
went on the harness: the generator, the independent model, the instrumented core, and the
falsification of the alternative reading.
