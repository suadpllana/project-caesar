The tree under `/app` is a small fixed priority kernel we use to try scheduling policies out
without flashing a board. A task set is a list of task programs in a JSON file, `/app/cases` holds
two of them, and a program is a list of steps: run for so many ticks, take a mutex with a timeout
or without one, release a mutex, sleep. One processor, one task per tick, larger numbers are more
urgent, and ties go to whoever became runnable first. `/app/run_sched.py` takes a case file and
prints the whole run: which task held the processor at each tick, what every task was worth at
each of those ticks, every acquisition, every block, every release and every completion in the
order it happened, the tick each task finished on, and the priority changes the policy made.

When a task blocks on a mutex somebody else is holding, the holder has to be lent enough urgency
to get out of the way, because otherwise everything in between runs first and the task that was
actually urgent waits for all of it. `/app/rt/core.py` owns the clock, the run queue and the
mutexes and decides who runs, while how much to lend and for how long is decided in
`/app/rt/prio.py`, which we rewrote last cycle. It is the only thing here that is wrong.

Run `/app/run_sched.py` on `/app/cases/inversion.json`. Task 4 starts at priority 1 and takes
mutex 1 and then mutex 2 before anybody else is up; task 2 at priority 5 arrives at tick 5 and
wants mutex 2; task 1 at priority 9 arrives at tick 7 and wants mutex 1; task 3 at priority 4
arrives at tick 3, holds nothing and only ever runs. The priority changes come back `[5, 4, 5]`,
`[7, 4, 9]`, `[10, 4, 1]`, and the first two of those are right: task 4 is lifted to 5 when task 2
blocks behind it, and to 9 when task 1 does. The third is the fault. The log shows
`["rel", 10, 4, 1]` and the policy drops task 4 to 1 on that same tick, while task 2 is still
queued on mutex 2 and task 4 is still holding it. Task 3 has the processor from tick 14 to tick
25. Task 2 is granted its mutex at `["acq", 29, 2, 2]`, twenty-four ticks after it asked for it,
and lands on `["done", 33, 2, 0]`. It outranks task 3 by one. `/app/cases/handover.json` is a
shape the policy still gets right, and its changes come back `[4, 3, 9]` and `[8, 3, 1]`.

Rewrite `/app/rt/prio.py` so that stops happening.

What a task is worth is graded directly, at every tick, alongside the schedule that falls out of
it. Two requirements hold at once and they pull against each other: nothing may sit waiting
behind a task it outranks, and nothing may be worth more than the priority it started with unless
there is a task waiting on it that accounts for the difference, which stops being true the moment
that task is gone. We grade both directions. Lifting a task higher than it can account for fails
exactly as leaving it too low does, so handing out urgency nobody is owed, lifting a task nobody
is waiting for, or leaving a task lifted after the last waiter behind it has gone all cost you
the same, and we have cases aimed at each. Being generous is not the safe way out.

Four moments are handed to you and they are the only ones you get. A task blocks on a held mutex.
A mutex is granted to somebody. A mutex is released. A task that was waiting gives up, because
the timeout it asked for ran out. `/app/rt/core.py` calls those four and nothing else, and it
reads what you set when it decides who runs next. The core object you are handed is the one the
scheduler itself uses, and it is the same object at every one of the four.

Some ground rules, because a couple of them are not what you would do elsewhere.

A mutex is handed to whichever waiter has been queued longest. Urgency does not jump the queue.
That is deliberate and it is not yours to change. A task that is waiting can be holding something
of its own, with a queue of its own behind it, and the sets we grade do that.

A wait that times out ends there. The task stops waiting, its attempt on the mutex has failed and
it carries on with whatever comes next in its program, while the mutex itself is untouched and
the holder still holds it.

The schedule is not yours either. Which task runs at a tick, when tasks arrive, how long a
critical section takes and when a job finishes are settled inside `/app/rt/core.py`, and we
compare the whole of it against a recorded run. What you set changes who the scheduler picks. It
has no other effect.

Only `/app/rt/prio.py` comes out of your container. Every other file is restored from an
untouched copy before the graded run, so an edit anywhere else is thrown away and never graded,
and the scheduler we measure you with is the one that shipped. Keep the class name, the
constructor and the four method names exactly as they are. The core calls them by name.

Half of what we run you on is task sets built at the moment the verifier starts, out of a seed
that does not exist until then. There is no schedule for those that anybody could have worked out
in advance. They come from the same shapes as everything else and we check them the same way, so
a policy that is right about the cases somebody thought to write down and wrong in general will
pass the first half and fail the second.

The priority changes at the end of the report are there for you to read and we do not grade them,
so a policy that reaches the right value by a different route inside a tick loses nothing for it.
What we grade is what the tasks were worth when each tick was decided. Build as many cases as you
like.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
