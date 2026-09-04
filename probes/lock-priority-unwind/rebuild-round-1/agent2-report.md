# Report

## 1. What was my very first plan, before I ran anything? Did I keep it or throw it away?

I wrote it down before opening a single source file (it is still in `FIRST_PLAN.txt`):

> This is priority inheritance with the classic "simplified restore" bug. On release the
> policy drops the holder straight back to its base priority instead of recomputing from
> the mutexes it still holds. Fix: keep base priority; on each of the three events
> recompute `eff(t) = max(base(t), max over mutexes m held by t of max eff(w) for w
> waiting on m)` and propagate transitively up the chain to a fixed point.

I kept the shape of it — recompute to a fixed point on every hook, never patch
incrementally — and I changed one thing in it, which turned out to be the whole task.
The plan said **"mutexes held by t"**. That is wrong here, and it is wrong in a way that
cannot be repaired later, for the reason in section 4.

## 2. Where did that plan come from?

Something I already knew, not the brief and not the source. I recognised the shape from
the first paragraph: priority inheritance, and the specific defect of restoring a
holder's priority to base on release rather than recomputing it from the mutexes it still
holds. FreeRTOS documents that exact limitation in its own manual, and Zephyr's
`kernel/mutex.c` has the same structure. The brief's worked example (`["rel", 10, 4, 1]`
and the policy dropping task 4 to 1 on that same tick while it still holds mutex 2) is
that bug verbatim, so I had the diagnosis before I read any code.

What I did **not** already know, and had to work out from the source, was the heir rule
in section 4. Nothing in my prior covers it, because it is a consequence of this
particular kernel's handover discipline.

## 3. What did I have to GUESS, because nothing told me?

Two things are genuine judgement calls, and one is load-bearing.

1. **Load-bearing: does the head of the queue on a *free* mutex inherit from the tasks
   queued behind it?** The brief never says. It says "whatever is standing between it and
   that mutex", which is suggestive but not a definition. I answered it from `core.py`
   rather than by guessing (section 4), and I measured the alternative, but the brief
   itself does not decide it, so I am listing it as the call I made.

2. **Whether inheritance follows the chain transitively.** The brief comes close — "A
   task that is waiting can have a queue of its own behind it, and the sets we grade do
   that" — but it never actually says the urgency travels further than one hop. I read
   "nothing may sit waiting behind a task it outranks" as applying to every waiter,
   including one whose chain is three deep, so I propagate to a fixed point.

Smaller ones, all low-risk because every reading I could think of agrees:

3. **A task that ends its program still holding a mutex.** Its `eff` is still recorded
   every tick, so it is graded, and nothing says what it should be. I just keep applying
   the same formula, so it stays lifted for whoever is stuck behind it. An incremental
   policy would land on the same value, which is why I think the risk is low.

4. **Recompute versus patch.** I recompute the whole table on every hook. The brief
   explicitly says the route inside a tick is not graded, only the values, so this is
   free.

## 4. Where did I get CONFIRMATION?

**The decisive one came from `core.py`, not from testing.** Three facts, none of which is
a modelling choice:

- `grep -n "pol\." app/rt/core.py` returns exactly three call sites: block, release,
  expire. **There is no hook when a task acquires a mutex.**
- At `released`, the mutex has already had `h = 0` written and the successor has been
  made READY but is *still in the waiter list*. I confirmed this by instrumenting the
  hooks: `t=22 released t=4 m=1 locks={1: (0, [1])}` — no holder, task 1 still queued.
- `core.py`'s own LOCK rule is `if x.h == 0 and (not x.w or x.w[0] == t)`. When a mutex
  is free with a queue, **the head of that queue is the only task that can take it.**

Put together: the state goes `{m: (0, [n1, n2])}` → `{m: (n1, [n2])}` with no policy call
in between. If only actual holders inherit, then `n2`'s urgency can never reach `n1` —
there is no moment at which to apply it. So holder-only inheritance is not merely a
different reading, it is unimplementable against this scheduler. Reading the responsible
task as "the holder, or the head of the queue if there is none" also makes the value
*invariant across that un-hooked transition*, which is exactly why three hooks are enough.
That argument is what changed my first plan, and I made the change before running anything
against it.

I then confirmed it four independent ways:

- **The two worked examples.** `inversion.json` now gives `[5,4,5]`, `[7,4,9]`,
  `[10,4,5]`, `[17,4,1]` — the first two are the ones the brief calls correct, and the
  third is the one it calls the fault, now holding at 5 while task 2 is still queued.
  `handover.json` still gives `[4,3,9]` and `[8,3,1]`, byte for byte what the brief says.
- **An independent checker (`work/check.py`), written from the two requirements rather
  than from my policy**, auditing *before every scheduling decision* and at the end of
  every tick — not just after hooks, which is the point, since a missing hook shows up as
  a stale value at a tick where nothing fired. It flags too-low (R1), too-high (R2), and
  separately an operational check that a blocked task never loses the processor to a task
  it outranks that is not on its chain.
- **The checker validated in both directions.** It fires on the shipped broken policy in
  1084 of 8000 generated sets, catching all three kinds — including task 5 stuck at eff 8
  with nobody waiting, which is the "left lifted after the last waiter has gone" direction
  the brief says it grades. On my policy: **0 of 8000**, over four generated shapes (heavy
  contention on one mutex, deep nesting with four mutexes, a narrow priority band so ties
  are everywhere, and tasks that walk off the end still holding a mutex).
- **I implemented the rejected reading and measured it.** `work/alt.py` is holder-only
  inheritance, identical in every other respect. It fails **393 of 8000 sets**, and the
  failures are precisely the predicted shape: seed 81 shows `{1: (0, [2,5])}` at pick time
  and `{1: (2, [5])}` at end of tick, task 2 stuck at 5 with task 5 (worth 8) behind it
  across the acquire that has no hook. On a hand-built case (`work/heir.json`) holder-only
  makes the most urgent task in the set wait until tick 55 while a mid-priority task runs
  all thirty of its ticks — "everything in between runs first", the brief's own sentence.
  My policy gets it the mutex at tick 25.

Two further checks: `settle` reaches a true fixed point on every hook of 4000 sets (one
more relaxation pass moves nothing), and the output is identical under four different
`PYTHONHASHSEED` values, since the runner and the grader are separate processes.

I want to be clear about what I could **not** check: I have no reference `eff` table. I
checked against the two invariants the brief states and the two worked examples it quotes.
If the reference reads the free-mutex case differently from the way `core.py` forced me
to, I am wrong and nothing I ran would have told me.

## 5. Did I write any intermediate version that turned out to be wrong?

**Of `prio.py`, no** — the first version I wrote is the final one behaviourally. I wrote
it twice: the second write added the docstring and tightened the iteration guard from
`len(ids) * len(link) + 4` to `len(ids) + 2` (still provably sufficient — one pass
advances the maximum at least one hop, and no chain is longer than the task count). No
logic changed between them, and the 8000-set sweep was clean before and after.

That is only because the one decision that mattered got made from `core.py` before I
wrote any code, rather than after a test failed. The plan I arrived with *was* wrong on
that point, and had I implemented it as written I would have shipped the holder-only
version, which passes both worked examples in the brief and fails 393 of 8000 generated
sets. Both examples have a single waiter per mutex, so neither one separates the two
readings. **Nothing I was handed would have caught it.**

My *test harness* went through three wrong versions, which is where the time went:

- The first `work/fuzz.py` had broken wiring for the findings list and would have reported
  a clean sweep whether or not anything ran. I made it print how many sets actually ran.
- The operational inversion check fired on 179 of 4000 sets that were not faults at all:
  the waiter's whole chain was asleep or deadlocked, so no priority could have changed who
  ran.
- After fixing that, three sets still fired. I checked mechanically rather than by eye and
  all three were the same artefact — the task that released the mutex keeps the rest of
  its own tick, because `run_one` does `continue` after UNLOCK. That is `core.py`, which
  is not mine.
- One hand-built test case mis-fired outright: I gave the low-priority holder a start time
  of 0 alongside a higher-priority task, so it never acquired the mutex and the case tested
  nothing. Fixed by moving the other task's start.

## 6. How long, and how many edits to `prio.py`?

Roughly 45 minutes. **Two writes of `prio.py`**, the second cosmetic plus a tighter loop
bound. Nearly all the time went on the checker and the fuzzer — the two false-positive
classes above, and building the holder-only policy so the one judgement call in section 3
had a number attached instead of an argument.

## Files

- `app/rt/prio.py` — the answer. Nothing else under `app/` is touched.
- `FIRST_PLAN.txt` — my plan, written before I opened any source.
- `work/check.py` — invariant checker, written from the requirements; audits at every pick.
- `work/fuzz.py` — four-shape generator; `python3 work/fuzz.py 0 8000 {new,old,alt}`.
- `work/alt.py` — holder-only inheritance, the reading I rejected, kept so it stays measured.
- `work/heir.json`, `work/expire.json` — hand cases for the two decisions.
- `work/converge.py`, `work/why.py`, `work/cmp.py`, `work/probe.py` — supporting checks.
