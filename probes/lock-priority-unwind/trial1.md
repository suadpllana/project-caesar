I'll start by reading the kernel and the current policy, then run the failing case.

Bash(find . -type f | grep -v __pycache__ | head -50 && cat rt/core.py && echo ===== && cat rt/prio.py && echo ====…)

./run_sched.py
./rt/core.py
./rt/task.py
… +214 lines (click to expand)
Bash(cat rt/lock.py rt/task.py rt/boot.py conf/sched.json && python3 run_sched.py cases/inversion.json | grep -A5 '…)

class Mx:
    __slots__ = ("id", "h", "w")
… +140 lines (click to expand)
Thinking… (click to expand)
Bash(cat > rt/prio.py <<'EOF' """Transitive priority inheritance. A task is worth its base priority, or the worth o…)

"chg": [
  [5, 4, 5],
  [7, 4, 9],
… +48 lines (click to expand)
Bash(cat > /tmp/fuzz.py <<'EOF' import random, sys sys.path.insert(0, '/app') from rt import boot, prio, core as C …)

ok

[stdout]
… +2 lines (click to expand)
Done. I rewrote `/app/rt/prio.py` so a task's worth is re-derived from the core's mutex state at each of the four hooks, instead of being reset to base on any release.

**What was wrong:** the old policy dropped the holder to its base priority on every release. In the inversion case task 4 released mutex 1 at tick 10 while still holding mutex 2 with task 2 queued behind it, so it fell to 1 and task 3 ran ahead of it for twelve ticks.

**What the new policy does:**
- Each task is worth its base, or the worth of the most urgent waiter on any mutex it still holds, whichever is larger.
- That is computed as a fixpoint over all mutexes, so a waiter that is itself holding a mutex with waiters passes its lifted worth up the chain.
- Nothing is cached. The core's holder and waiter lists are already consistent when each hook fires, so a lift vanishes exactly when the last accounting waiter is granted, times out, or the mutex is released.
- The class name, constructor and four method names are unchanged.

**Results:**

| Case | Priority changes | Task 2 done |
|---|---|---|
| inversion.json before | [5,4,5] [7,4,9] [10,4,1] | tick 33 |
| inversion.json after | [5,4,5] [7,4,9] [10,4,5] [17,4,1] | tick 21 |
| handover.json | [4,3,9] [8,3,1], unchanged | |

Task 4 now stays at 5 after releasing mutex 1, hands mutex 2 to task 2 at tick 17, and drops to 1 only then.

I also fuzzed 3000 random task sets with nested holds, timeouts, sleeps and wait chains, checking after every tick that every task's worth matched the base-or-max-waiter rule derived from the live mutex state. All passed. Only `rt/prio.py` was changed; the fuzz script lives in `/tmp`.
