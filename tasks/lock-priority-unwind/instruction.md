We write firmware for boards where a handful of tasks share one processor and a few mutexes,
and the kernel in `/app` has started letting an urgent task sit behind a task it outranks. The
scheduler is fixed priority and preemptive. One task per tick, larger numbers are more urgent,
ties go to whoever became runnable first, and all of that lives in `/app/rt/core.py`. Tasks take
and release mutexes as they go, and when one blocks on a mutex somebody else is holding, the
holder has to be lent enough urgency to get out of the way, because otherwise everything in
between runs first and the task that was actually urgent waits for all of it. How much to lend,
and for how long, is decided in `/app/rt/prio.py`. That file is the only thing here we have got
wrong.

This is the run in front of us. Four tasks. Task 4 starts at priority 1, takes mutex 1 and then
mutex 2, runs for eight ticks, releases mutex 1, runs for four more and releases mutex 2, while
task 2 at priority 5 arrives at tick 5 and wants mutex 2, task 1 at priority 9 arrives at tick 7
and wants mutex 1, and task 3 at priority 4 arrives at tick 3, holds nothing and only ever runs.
Put that through `/app/run_sched.py` and the priority changes come back `[5, 4, 5]`,
`[7, 4, 9]`, `[10, 4, 1]`, and the first two of those are exactly right: task 4 is lifted to 5
when task 2 blocks behind it and to 9 when task 1 does. Then it releases mutex 1 at tick 10 and
goes straight back to 1, while task 2 is still queued on mutex 2, which task 4 is still holding.
Task 3 takes the processor at tick 14 and keeps it to 25, and task 2 is granted its mutex at
tick 29, twenty-four ticks after it asked for it, and finishes at 33. It outranks task 3 by one.

Rewrite `/app/rt/prio.py` so that stops happening.

What a task is worth is graded directly, at every tick, alongside the schedule that falls out of
it. A task is worth its own priority, or the highest priority among the tasks that are waiting,
however far back, for something it is holding, whichever of those two is greater. Nothing else.
We grade both directions. Lifting a task higher than that fails exactly as leaving it too low
does, so handing out urgency you cannot account for, lifting a task nobody is waiting for, and
leaving a task lifted after the last waiter behind it has gone all cost you the same, and we
have cases aimed at each of them. Being generous is not the safe way out of this one.

Four moments are handed to you and they are the only ones you get. A task blocks on a held
mutex. A mutex is granted to somebody. A mutex is released. A task that was waiting gives up,
because the timeout it asked for ran out. `/app/rt/core.py` calls those four and nothing else,
and it reads what you set when it decides who runs next. Everything the decision needs is
reachable from the core object you are handed: who holds what, who is queued on what, what each
task started as, and what it is worth at this moment.

Some ground rules, because a couple of them are not what you would do elsewhere.

A mutex is handed to whichever waiter has been queued longest. Urgency does not jump the queue.
That is deliberate and it is not yours to change. It is also why the moment a mutex changes
hands is one of the four we give you at all.

A wait that times out ends there. The task stops waiting, its attempt on the mutex has failed
and it carries on with whatever comes next in its program, while the mutex itself is untouched,
the holder still holds it, and the queue behind it is one shorter than it was a tick ago.

The schedule is not yours either. Which task runs at a tick, when tasks arrive, how long a
critical section takes and when a job finishes are settled inside `/app/rt/core.py`, and we
compare the whole of it against a recorded run. What you set changes who the scheduler picks. It
has no other effect.

Only `/app/rt/prio.py` comes out of your container. Every other file is restored from an
untouched copy before the graded run, so an edit anywhere else is thrown away and never graded,
and the scheduler we measure you with is the one that shipped. Keep the class name, the
constructor and the four method names exactly as they are. The core calls them by name.

Half of what we run you on is task sets built at the moment the verifier starts, out of a seed
that does not exist until then. There is no schedule for those that anybody could have worked
out in advance. They come from the same shapes as everything else and we check them the same
way, so a policy that is right about the cases somebody thought to write down and wrong in
general will pass the first half and fail the second.

The runner at `/app/run_sched.py` takes a file of task programs and prints the schedule, what
every task was worth at every tick, and a log of what the scheduler did, and the list of
priority changes at the end of that report is yours to read and is not something we grade, so a
policy that reaches the right value by a different route at a different moment inside a tick
loses nothing for it: what we grade is what the tasks were worth when each tick was decided.
Build as many as you like.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
