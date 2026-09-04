# Report

## 1. What was my very first plan, before I ran anything? Did I keep it?

Before running anything I read all 527 lines of the tree, and the plan I wrote down
(`notes/plan0.md`, written before I touched `prio.py`) was:

> Make effective priority a **derived** quantity rather than an incrementally patched one:
> `eff(t) = max(base(t), max eff(x) for every x standing behind t)`, least fixpoint,
> recomputed from the core's own state on each of the three calls.

I kept it. The shipped file's three faults were visible on sight — one-level inheritance with
no transitivity, an unconditional restore to base on release, and an `expired` that does
nothing — and "recompute the whole thing from state" fixes all three at once and cannot rot.

What that plan did **not** settle, and what almost all of my time went on, is what
"standing behind" means. I listed four candidate readings in the same note before writing any
code:

- (a) **holder only** — classic priority inheritance,
- (b) **prospective owner** — the holder, or the head of the queue when the mutex is free,
- (c) **queue-ahead** — the holder *plus* everybody queued ahead of you,
- (d) (c) but a freed-but-not-yet-run head of queue does not count as waiting.

## 2. Where did that plan come from?

The *shape* (a least fixpoint over a wait-for relation) is something I already knew: this is
priority inheritance, the release bug is the "simplified priority restoration" limitation
that FreeRTOS documents about its own mutexes, and the transitive chain case is textbook. So
I did not derive that from the brief; I recognised it.

What I did **not** already know, and what the source decided, is that the standard answer is
wrong here. I got that from `core.py`, not from the brief:

- `run_one` acquires a mutex (`x.w.pop(0)`; `self.acquire(t, m)`) with **no call to the
  policy**, and the brief confirms it: "Three moments are handed to you and they are the only
  ones you get."
- So under reading (a), the moment a task pops itself off the head of the queue and becomes
  the holder while somebody is still queued behind it, it must gain that waiter's urgency,
  and **nothing is called**. Reading (a) cannot maintain its own invariant on this interface.

I ran that as an experiment rather than trusting the argument: I implemented all four
readings as policies and audited each against *its own* definition at every scheduling
decision and every tick, over 1500 random task sets.

    cases where the reading cannot hold its own invariant with only the three calls
       holder       18 / 1500
       blockonly    18 / 1500
       owner         0
       queue         0

Two of the four readings are ruled out by the interface itself. That is the one real piece of
derivation in this task, and the environment - not the brief - is what supplied it.

## 3. What did I have to GUESS?

**(i) The big one: queue-ahead (c) versus prospective-owner (b).** Nothing decides this
mechanically. Both are self-consistent under the three calls. Measured over 3000 random sets:

    (b) vs (c) differ on the graded per-tick priority table : 45 / 3000  (1.5%)
    (b) vs (c) differ on the schedule                       :  0 / 3000

They never differ on the schedule, because the extra lift (c) hands a queued-ahead task is
only ever carried while that task is *blocked*; the instant it becomes runnable both readings
agree. So the entire difference lands on the quantity the brief says is graded directly, and I
could not test my way to it. I chose (c) on wording alone:

- "nothing may sit **waiting behind** a task it outranks" — in a strictly first-in-first-out
  queue a task literally sits behind the ones ahead of it. On my hand case `queue-ahead`,
  reading (b) leaves a base-9 task sitting behind an eff-2 task for 5 consecutive ticks,
  which is that sentence violated as written. Reading (c) does not.
- "**whatever** is standing between it and that mutex has to be lent enough urgency to get out
  of the way, because otherwise **everything in between** runs first" — plural, and under
  strict FIFO the tasks queued ahead of you are as much in the way as the holder is.
- The brief spends three sentences insisting that urgency does not jump the queue and that
  this is deliberate and not mine to change, which only needs saying if the remedy for an
  urgent task stuck behind a slow one is to **lift the one in front** rather than reorder.

If the reference means (b), I lose, and I would lose on about 1.5% of random sets — enough to
be caught. This is the single place I am not certain.

**(ii) A task that ends while still holding a mutex.** Nothing addresses it. I let it be
treated like any other holder: it keeps a lift while somebody waits behind it, and loses the
lift when that waiter times out — even though it is finished. That follows requirement 2 read
literally ("stops being true the moment that task is gone"), but a policy that skipped
finished tasks would record a different number and nothing told me which.

**(iii) Whether a freed head of queue still counts.** After `unlock`, the core makes the head
waiter runnable but leaves it in `m.w`. I treat it as still in the queue, so it keeps
receiving from the tasks behind it. This is nearly forced — reading (d), which drops it, is
one of the two the interface rules out — but I did have to decide it.

**(iv) That a global recompute is acceptable.** It produces different `chg` entries than an
incremental policy would. The brief says `chg` is not graded, so I relied on that sentence.

**(v) That I should never try to influence ordering.** `set` does not touch queue-entry
order, so ties still go to whoever became runnable first. I assumed the schedule is entirely
the core's, as stated.

## 4. Where did I get CONFIRMATION?

- **The only externally supplied answer in the whole task**: the brief states that
  `handover.json` is a shape the policy already gets right and its changes are `[4, 3, 9]` and
  `[8, 3, 1]`. My policy reproduces both exactly. That is real confirmation, and it is thin —
  it is one mutex with one waiter, which every one of my four candidate readings gets right.
- `inversion.json` is *consistent with* the brief's diagnosis but is not confirmation: the
  brief says `[10, 4, 1]` is the fault and never says what the right value is. I now get
  `[10, 4, 5]` (task 4 keeps what mutex 2 still earns it), task 2 acquires at tick 18 instead
  of 30 and finishes at 21 instead of 33. That matches the complaint but I inferred it.
- **An independently written checker**, deliberately not the same algorithm: `prio.py` relaxes
  effective values to a fixpoint; `harness/chk.py` recomputes the answer as a reachability
  question over *base* values ("who is transitively stuck behind t") and takes a max. It also
  asserts both stated requirements separately. It runs at **every** scheduling decision and at
  **every** tick, not just at the end. Final sweep: **8010 task sets, 0 violations** — the two
  shipped cases, 8 hand-built ones (transitive chain, timeout dropping a lift, timeout out of
  the middle of a queue, a forced hold-and-wait cycle, a task dying while holding), and 8000
  generated ones. Shape coverage: 277k tick-observations with a queue two deep, 97k three
  deep, 147k with a blocked task that itself holds a contended mutex.
- **Hook sufficiency, stated as strongly as I could**: calling `settle()` three extra times at
  every scheduling decision changed a value **zero** times across 400 contention-heavy sets.
  The state is always already at the fixpoint when the scheduler looks at it — which is the
  property the missing acquire call put in doubt.
- Determinism: identical output digest under `PYTHONHASHSEED` 0, 1, 12345 and 999.
- The relaxation always settles in at most 3 sweeps and never exhausted its budget.

What I have **no** confirmation of is item (3)(i). No oracle I can build distinguishes it,
because the disagreement is confined to a quantity only the verifier holds.

## 5. Did I write an intermediate version that turned out to be wrong?

**No — the first version of `prio.py` was the final one.** There were two writes of the file
and the second only added the comment header explaining the invariant; the logic never
changed. That is not because I was careful, it is because "derive the value from the state"
has no incremental cases to get wrong, and because I did the four-way comparison before
committing to a reading rather than after.

Two things I did get wrong, both outside `prio.py`:

- Two of my hand-built test cases were **degenerate and I nearly believed them**. In
  `timeout-drops-lift` and `chain` I gave the middling CPU hog `start: 0` and a higher base
  than the lock holder, so the holder never got to take the lock at all, no task ever blocked,
  and the priority-change log came back **empty**. An empty log looks like a policy that is
  behaving quietly. I only caught it because I was printing the event list beside it and there
  were no `blk` events. Moving the hog's start to tick 3 fixed both.
- My first generator crashed (`rng.choice` on an empty list) when a task already held every
  mutex.

## 6. How long, and how many edits?

Roughly 40 minutes. **Two** edits to `app/rt/prio.py`: one that wrote the policy, one that
added the explanatory comment. Everything else — perhaps 80% of the time — went on the
harness that ruled out two of the four readings and on the checker, not on the policy, which
is 65 lines of which 17 are comment.

Scratch lives in `harness/` and `notes/`; `app/rt/prio.py` is the only file under `app/` I
touched, and `notes/prio.orig.py` is the shipped original for reference.
