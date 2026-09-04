I'll start by reading the scheduler core and the current policy, then run the failing case.

Bash(ls -R . | head -50 && cat rt/core.py rt/prio.py run_sched.py && cat cases/inversion.json cases/handover.json)

.:
cases
conf
… +224 lines (click to expand)
Bash(cat rt/lock.py rt/task.py rt/boot.py conf/sched.json; cat > rt/prio.py <<'EOF' class Prio: """Transitive prior…)

class Mx:
    __slots__ = ("id", "h", "w")
… +178 lines (click to expand)
The fix works on both shipped cases. Now I'll check a chained-inheritance case and a timeout case.

Bash(cd /tmp && cat > chain.json <<'EOF' {"tasks":[ {"id":1,"base":9,"start":4,"prog":[["lock",1,-1],["run",1],["un…)

"chg": [
  [1, 4, 3],
  [3, 4, 7],
… +66 lines (click to expand)
`/app/rt/prio.py` is rewritten and the inversion is gone.

**What was wrong.** The old policy reset a task to its base priority on any release, ignoring that the task could still hold another mutex with a waiter behind it. In the inversion case task 4 dropped to 1 at tick 10 while still holding mutex 2 with task 2 queued on it, so task 3 ran for eleven ticks ahead of a higher-priority waiter.

**What the new policy does.** At each of the four events it recomputes every task's worth from the core's mutex state. A task is worth its base, or the worth of the most urgent task queued on any mutex it holds, whichever is larger. The computation iterates to a fixpoint so urgency flows along chains where a holder is itself waiting on someone else. Because it is a full recomputation rather than an incremental adjustment, a lift appears only while a waiter exists and disappears the moment the last waiter is granted, times out, or the mutex is released. Nothing is ever lifted above what its waiters account for.

**Results.**

| Case | Priority changes | Task 2 acquires / finishes |
|---|---|---|
| inversion (before) | `[5,4,5] [7,4,9] [10,4,1]` | tick 29 / 33 |
| inversion (after) | `[5,4,5] [7,4,9] [10,4,5] [17,4,1]` | tick 17 / 21 |
| handover | `[4,3,9] [8,3,1]` unchanged | |

I also ran a hand-built case with a two-level chain plus a timed-out waiter. The holder at the bottom inherited 9 through the intermediate task, the timed-out task's contribution vanished at expiry without disturbing the chain, and each holder dropped exactly at the release that freed its last waiter.
