# Report

## 1. First plan, before running anything

Before I ran anything (but after reading TASK.md) my plan was textbook priority inheritance
with one correction:

- `blocked(w, m, h)`: walk the chain of holders upward from `h` and lift each one to at least
  `eff[w]`.
- `released(t, m)`: **do not** restore `t` to its base. Recompute `t` as
  `max(base[t], max eff of every task still waiting on a mutex t still holds)`.
- `expired(w, m, h)`: the same recompute for `h`, because `w` has stopped waiting.

The `released` clause was the whole point: the fault the brief describes (`[10, 4, 1]` while
task 2 is still queued on mutex 2) is exactly the "restore to base on release" behaviour.

**I kept about two thirds of it and threw away the rest**, before writing any code, while
reading `app/rt/core.py`. Two things in the core changed the design:

- There is **no hook when a waiter acquires a mutex**. `run_one` pops the waiter off `x.w` and
  calls `acquire()` with no call into the policy. So any lift a new owner needs must already be
  in place before it takes the mutex.
- `blocked(w, m, h)` is called with **`h == 0`** whenever the mutex is free but somebody is
  already queued ahead of `w` (`x.h == 0 and x.w[0] != t`). A policy written around the `h`
  parameter does nothing at all in that case.

Together those forced the real rule: a waiter lends its urgency not only to the holder but to
**every task queued ahead of it in the same mutex queue**, because under FIFO handover those
tasks all have to run before it can. Once I had that, "walk the chain from `h`" became "rebuild
the whole table from base at each of the three moments", which is the same answer computed in a
way that cannot drift.

## 2. Where the plan came from

Mostly **prior knowledge**: I already knew the priority inheritance protocol, and I specifically
knew the "simplified priority restore" limitation that FreeRTOS documents — a task holding two
mutexes drops straight back to base when it releases one. The brief's description of
`inversion.json` is a picture of exactly that, so the diagnosis was recall, not derivation.

The parts that were **not** recall came from reading `core.py`: the missing acquire hook, the
`h == 0` call, and the fact that `released` runs after `ms[m].h = 0` while the handed-over
waiter is still sitting in `ms[m].w`. Those are what turned a chain-walk into a queue-aware
closure. The brief contributed the two requirement sentences and one input-space sentence
("A task that is waiting can have a queue of its own behind it, and the sets we grade do that"),
which told me the queue-behind-a-waiter shape is graded.

## 3. Things I had to guess

Nothing in the brief or the code states these. Every one is an inference:

1. **Waiters lend to waiters.** That a task queued behind another waiter must lift that waiter,
   not just the holder. I argued it three ways — the literal reading of "nothing may sit waiting
   behind a task it outranks", the sentence about a waiter having a queue of its own, and the
   structural fact that with no acquire hook there is no other moment at which the incoming owner
   could be lifted. I believe it, but it is an inference.
2. **When the lift starts, inside that window.** Given (1), a lift could plausibly be applied
   either at the moment the newcomer queues (what I do) or deferred to the moment the mutex is
   released. Both give the *same schedule*; they differ only in what a blocked task is *worth*
   during the intervening ticks — which is graded. This is my biggest exposure and I could not
   test my way out of it.
3. **Transitivity.** That the lift propagates through a chain (A holds m1; B holds m2 and waits
   on m1; C waits on m2 → A must reach C's priority). The brief never says "transitive" and the
   shipped policy is not. I chose transitive because requirement 1 demands it.
4. **Effective vs base when lending.** I let a lender contribute its already-lifted value. Under
   a full closure this is the same number as taking the max of base values over the transitive
   set, so it is probably moot, but I picked one.
5. **A task that finishes while still holding a mutex** keeps its lift forever. No hook fires
   there so I could not change it even if I wanted to, but I never confirmed it is intended.
6. **Deadlock.** Two tasks in a mutual wait converge to the cycle maximum under my fixed point.
   Nothing says what should happen.
7. That priorities are compared as plain integers with no ceiling or clamp.

## 4. Where I got confirmation

- **The two shipped cases.** `handover.json` came back **byte-identical** to the shipped
  policy's run (`chg [[4,3,9],[8,3,1]]`, same trace, ev and done) — the brief says that shape
  is already right, so any change there would have been a regression. `inversion.json` lost the
  bad `[10, 4, 1]` and became `[10,4,5]` then `[17,4,1]`; task 2 acquires at 18 instead of 30
  and finishes at 21 instead of 33. This is the only external ground truth I had, and it pins
  the release rule and nothing else.
- **An independent replay check.** I wrote a checker that reconstructs the holder/waiter state
  of every mutex from the **event log** (`acq`/`blk`/`rel`/`exp`) rather than from the live core
  objects, recomputes the required priority table at the end of every tick, and compares it to
  the reported `prio` array. **0 mismatches over 6000 generated task sets** across two
  generators. This validates my hook placement and timing — that I settle at exactly the moments
  the wait graph changes — but not the rule itself, since it restates my own reading.
- **An outcome check on the stated requirement.** Separately I checked the brief's property
  directly on the report: no task may sit blocked while the processor goes to a task that is
  worth less and is not in its dependency chain. My policy: **0 avoidable inversions over 6000
  cases**. Four alternative policies I built as foils (holder-only inheritance; holder-only plus
  a lift at handover; the FreeRTOS-style sticky lift; the shipped policy) scored 292, 97, 427 and
  423 on one generator and 387, 233, 835 and 867 on the other. The 55 ticks my policy is still
  flagged on are all the same unavoidable class — the runner was picked legitimately at a high
  priority and then released its lock in the middle of that same tick, which no policy can
  affect because the pick has already happened.
- **The decisive discriminator was a generated case, not the shipped ones.** Random case 47:
  under holder-only inheritance a base-9 task queues behind a base-6 waiter on a free mutex, no
  lift happens, a base-8 task takes the processor for two ticks, and the base-9 task finishes at
  44 instead of 38 — while a third task's `lock` times out that would otherwise have succeeded.
  My hand-built `queue-behind-waiter` and `three-deep-queue` cases show the same thing more
  starkly (a base-9 task finishing at 21 instead of 51). That is what convinced me guess (1) is
  right rather than merely defensible.
- **Determinism.** The report is identical across five `PYTHONHASHSEED` values, and a digest over
  300 generated runs is identical across four. That matters because half the graded sets are
  built from a seed at verifier start and compared against a recorded run.

What I could **not** confirm against anything: guess (2), the exact tick at which the lift on a
queued waiter begins. My reading and the deferred reading produce identical schedules and differ
only in the graded priority table, so no experiment I can run distinguishes them.

## 5. Intermediate versions that were wrong

**In `prio.py`: no.** The first version I wrote is the final one behaviourally. It went through
two writes and the second only replaced a fixed iteration cap of 64 with `len(ids) + 2`, which
is a provable bound rather than a magic number — no behaviour changed.

But the honest answer needs the rest of it: **the plan I arrived with was wrong and I discarded
it before writing code**, while reading `core.py` (see §1). Plain chain-walking priority
inheritance — my first plan, and the thing I "already knew" — is one of the foils that scores
hundreds of inversions above.

**And I wrote three wrong versions of the checker**, which is where the real errors were:

1. The sleep interval was off by one, so a holder that slept immediately after acquiring looked
   runnable and my own policy showed 12 phantom inversions.
2. Worse: I reconstructed a waiter as "blocked until its `acq` event", but the core makes the
   head of the queue READY at the `rel` that hands it over. That hid exactly the window I needed
   to see, and made holder-only inheritance look as clean as my policy on case 47. If I had
   stopped there I would have had no evidence for guess (1) at all.
3. The inversion test compared base priorities where it should have compared effective ones, so
   a correctly-lifted low-priority holder running was reported as a fault (18 false alarms).

All three were fixed by looking at the specific flagged tick and asking what the core actually
did there.

## 6. Time and edits

Roughly 35-40 minutes end to end. **Two writes to `app/rt/prio.py`**, the second cosmetic. The
bulk of the time went on the harness rather than the solution: two case generators, five policy
variants to differentiate against, ten hand-built cases aimed at one rule each (queue behind a
waiter, timeout drops a lift, timeout drops only part of a lift, a two-deep chain, releasing one
of two held mutexes, a dead holder, a three-deep queue, a case where nothing may be lifted at
all, deadlock, and expiry of a task with its own queue behind it), and three rounds of fixing
the checker.
