# Report

## 1. First plan, before running anything

Recompute the effective priority from scratch instead of restoring it. Concretely:

    eff[t] = max(base[t], max{ eff[w] : w is queued on some mutex t holds })

as a fixed point, so a boost propagates along chains. The shipped `released()` does
`set(t, base[t])` — it drops the holder straight back to its starting priority without
asking whether it still holds anything else that somebody is queued on. That is the whole
of the reported fault.

I kept the plan. It survived intact. But it was **incomplete**, and reading `core.py`
added a piece I had not planned for (see 2).

## 2. Where the plan came from

The "drop to base on release" shape came from prior knowledge — it is the documented
simplified-restore limitation of priority inheritance in small kernels, and the brief's
symptom (`["rel", 10, 4, 1]` with task 2 still queued on mutex 2, which task 4 still holds)
is exactly its signature. So the diagnosis was recall, and the brief confirmed it before I
ran anything.

The part that was **not** recall, and that I got from reading `core.py`:

- `run_one`'s UNLOCK branch sets `h = 0`, makes the head waiter READY, and leaves it in
  `x.w`. So there is a window where a mutex has no holder but still has a queue.
- The LOCK branch lets a task take a free mutex **only if it is the head** of that queue.
  Everybody else appends and blocks — and `pol.blocked(t, m, x.h)` is then called with
  `h == 0`. The shipped `blocked()` does `if h and ...`, so it ignores that call entirely.
- **There is no callback at acquisition.** The core calls `blocked`, `released`, `expired`
  and nothing else.

That last point is what forced the design. If a mutex with no holder lends to nobody, then
when the head finally takes it with somebody still queued behind, the head needs a boost at
that instant and there is no callback to apply one. The boost has to already be there. So
the lending target is the holder if there is one, and otherwise the head of the queue —
the task that is going to take it, since the core permits nobody else. That is a fact about
`core.py`, not a taste.

## 3. What I had to guess

Listing everything, including the ones I later got evidence for:

1. **The free-mutex head is the lending target.** Not stated anywhere in the brief. I
   derived it from the missing acquisition callback (above) and then confirmed it
   behaviourally, but the brief never says it. This was the main judgement call.
2. **A task that finishes while still holding a contended mutex.** `h` stays set to a DONE
   task forever and its waiters are stuck. I leave the boost on it. Nothing decides this.
   It cannot affect the schedule (DONE tasks are never picked) but it *is* in the graded
   per-tick priority row, so if the grader wants such a task back at its base priority I am
   wrong there. Unresolved.
3. **Deadlock cycles.** Two tasks each holding what the other wants. My fixed point gives
   every task in the cycle the highest base in the closure. Nothing runs either way, so it
   only shows up in the graded priority row. Guessed.
4. **A waiter that times out while itself holding a contended mutex keeps its own boost.**
   Follows from the rule but is not stated.
5. **Whether the free-queue head also lends to itself.** Moot — including it changes
   nothing, since its own base is already the floor. I did not have to decide.
6. **Recomputing the whole table on every callback**, rather than touching only the tasks
   involved in the event. No behavioural difference (`core.set` no-ops on an unchanged
   value, and `chg` is not graded), but it is a choice.

Things I did **not** have to guess, because the brief states them: that the boost must come
off the moment the last waiter is gone; that over-lifting fails exactly as under-lifting
does; that FIFO handover is not mine to change; that everything on one queue lends to one
task; that a waiting task can have a queue of its own (which is what says chains are
graded); and that an expired wait leaves the mutex untouched.

## 4. Where I got confirmation

Five sources, in increasing order of how much I trust them.

**a. The two shipped cases.** `handover.json` comes back **byte-identical** to the shipped
policy's whole report — that is the must-still-work fence and it is untouched. On
`inversion.json` the third change becomes `[10, 4, 5]` instead of `[10, 4, 1]`, task 2 gets
mutex 2 at tick 18 instead of 30, and finishes at 21 instead of 33.

**b. An independent value model.** I hooked the exact `self.prio.append(...)` the graded row
comes from, snapshotted the core's own mutex state at that instant, and recomputed the
required priority a *different* way — walk each blocked task's chain to closure and take the
maximum starting priority over everything that transitively depends on you — then compared
against the recorded `eff`. Validated in both directions before trusting it: it fires on the
shipped policy (197 of 2500 sets on one generator, 642 of 2500 on another) and reports **0**
on mine.

**c. A behavioural check that uses none of my priority arithmetic.** At the instant the
scheduler decides, flag any tick where the processor went to a task that nothing urgent
needs while a higher-starting-priority task sat blocked with a runnable chain. **0** on
mine; non-zero on the shipped policy and on all three wrong readings.

**d. Differential testing against wrong readings.** I built the three plausible alternatives
and ran everything over 11 hand cases and 9000+ generated sets:

| reading | value faults | inversions |
|---|---|---|
| mine | **0** | **0** |
| shipped | 642 / 2500 | 140 / 2500 |
| free mutex lends to nobody | 132 / 2500 | 29 / 2500 |
| direct waiters only, no chains | 216 / 2500 | 47 / 2500 |
| never lower a priority | 1672 / 2500 | 210 / 2500 |

Every one of the four is separated by at least one hand case as well, so the failures are
legible and not just statistical.

**e. Model-free.** Completion tick of the highest-priority task, mine versus "free mutex
lends to nobody": 17 vs 46, 15 vs 35, 33 vs 72; versus "no chains": 39 vs 77. That is the
starvation the brief describes, and it is visible without any priority model at all.

Also checked: identical output under four `PYTHONHASHSEED` values (the generated half of the
grading needs the run to be reproducible across processes, and my policy only iterates
sorted keys); no crash on empty programs, relocking a held mutex, unlocking an unheld one,
zero-length runs, zero timeouts, or a single task; 600 sets of 14 tasks and 6 mutexes clean
in 3.3s.

## 5. Intermediate versions that were wrong

`prio.py` itself was right on the first write — the value model never changed. The second
write only renamed two helpers, sorted the relaxation order for cross-process determinism,
and raised the convergence cap. So no wrong policy shipped even briefly.

**My test harness was wrong three times, and the third one is the one worth reporting.**

1. The first inversion detector flagged 42 of 300 sets on my own (correct) policy. False
   positives: the blocking task was asleep, so no policy could have done anything. Fixed by
   requiring that somebody on the blocked task's chain was actually runnable.
2. It still flagged one set. I was comparing the end-of-tick snapshot against who ran
   *during* that tick — the flagged task had been the holder when the tick was decided and
   released the mutex while running. Fixed by snapshotting at the moment `pick()` decides.
3. **My first eight hand-built edge cases reached almost none of the states they were
   written for.** Coverage instrumentation said `chain2 = 0`, `cycle = 0`,
   `free_head_with_queue = 1` across the whole suite — no transitive chain ever formed and
   the deadlock case never deadlocked. Cause: I gave the CPU hog `start = 0` and a priority
   above the low-priority mutex holder, so the holder never got the processor to take its
   mutex in the first place and nothing ever contended. The cases all *passed*, and they
   were testing nothing. I only found it because I wrote a coverage counter rather than
   trusting a green result. After fixing the arrival times the same suite separates all
   four wrong readings.

That third one is the reason I do not treat "my tests pass" as evidence on its own.

## 6. Time and edits

Roughly 45 minutes. **Two** writes to `app/rt/prio.py`, and the second was cosmetic —
identical behaviour, sorted iteration and a slightly larger convergence bound. Almost all of
the time went on the harness, the generators and the coverage check, not on the policy.

## The policy, in one paragraph

For each mutex, the task that owes the queue is its holder, or if it has none, the head of
its queue — the only task the core will let take it. Everyone else on that queue lends what
they are currently worth to that task. A task is worth the greater of its own starting
priority and the most any of its lenders is worth, taken to a fixed point so a chain carries
through. That table is recomputed from the core's own state on each of the three callbacks,
which is every moment the shape can change, so a boost appears the tick a waiter arrives and
is gone the tick the last waiter behind it stops waiting — whether it stopped by being
handed the mutex or by giving up on its timeout.
