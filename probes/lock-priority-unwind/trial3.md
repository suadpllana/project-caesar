I'll start by reading the scheduler core, the current policy, and the two cases.

Bash(ls -R . | head -50 && cat rt/core.py && cat rt/prio.py && cat run_sched.py && cat cases/*.json)

.:
cases
conf
… +224 lines (click to expand)
Bash(cat rt/lock.py rt/task.py rt/boot.py conf/sched.json)

class Mx:
    __slots__ = ("id", "h", "w")
… +92 lines (click to expand)
Thinking… (click to expand)
Bash(cat > rt/prio.py <<'EOF' """Priority inheritance policy. Every task is worth the larger of its own base priori…)

"chg": [
  [5, 4, 5],
  [7, 4, 9],
… +102 lines (click to expand)
Thinking… (click to expand)
Bash(cd /tmp && cat > chain.json <<'EOF' {"tasks":[ {"id":1,"base":9,"start":6,"prog":[["lock",2,-1],["run",1],["un…)

"chg": [],
 "done": [
  [1, 7],
… +46 lines (click to expand)
The test case was mis-built (task 5 grabbed mutex 1 first and never released it). I'll fix the arrival order so task 4 holds mutex 1 before the others arrive.

Bash(cd /tmp && cat > chain.json <<'EOF' {"tasks":[ {"id":1,"base":9,"start":6,"prog":[["lock",2,-1],["run",1],["un…)

"chg": [
  [1, 4, 8],
  [4, 4, 1],
… +100 lines (click to expand)
Bash(cd /tmp && cat > trans.json <<'EOF' {"tasks":[ {"id":1,"base":9,"start":4,"prog":[["lock",2,-1],["run",1],["un…)

"chg": [
  [1, 4, 3],
  [4, 2, 9],
… +58 lines (click to expand)
`/app/rt/prio.py` is rewritten and the fault is gone. The same class name, constructor and four method names are kept.

**What was wrong.** The old policy handled `released` by resetting the releasing task straight to its base priority, ignoring that it might still hold other mutexes with waiters queued behind them. In the inversion case, task 4 released mutex 1 at tick 10 while still holding mutex 2 with task 2 waiting on it, so it fell to 1 and task 3 ran for twelve ticks in front of the task that was actually urgent.

**What the new policy does.** All four hooks call one routine that rederives every task's worth from the mutex state the core has already updated before calling in. A task is worth the larger of its base priority and the worth of any task queued on a mutex it currently holds. This is computed to a fixed point so inheritance is transitive through a waiter that is itself a holder, and the iteration is bounded so a deadlocked cycle cannot spin. Because the value is derived fresh each time rather than patched, a lift exists only while some waiter accounts for it and disappears on grant, release or timeout of the last one. Nothing is ever lifted without a waiter behind it.

**Results.**

- Inversion: changes are now `[5,4,5]`, `[7,4,9]`, `[10,4,5]`, `[17,4,1]`. Task 4 stays at 5 after releasing mutex 1 and drops to 1 when it releases mutex 2. Task 2 finishes at tick 21 instead of 33.
- Handover: unchanged, still `[4,3,9]` and `[8,3,1]`.
- Transitive chain I built (task 1 waits on task 2, which waits on task 4): both intermediate and root holders are lifted to 9 while the chain stands, and each drops the moment its own waiter is gone.
- Timeout case: the holder is lifted when the waiter blocks and dropped on the same tick the waiter's wait expires, with the mutex untouched.
- A 300-scenario random fuzz over runs, locks with and without timeouts, unlocks and sleeps ran without any errors.

No files other than `rt/prio.py` were changed under `/app`. Scratch cases live in `/tmp` only.
