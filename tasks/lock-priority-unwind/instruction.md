`/app` holds the fixed priority scheduler we use to try real time policies out without booting a
board. One processor, one task per tick, larger numbers are more urgent, ties go to whoever
became runnable first, and all of that lives in `/app/rt/core.py`. Tasks take and release
mutexes as they go, and when one blocks on a mutex somebody else is holding, the holder has to
be lent enough urgency to get out of the way, because otherwise everything in between runs first
and the task that was actually urgent waits for all of it. How much to lend, and for how long, is
settled in `/app/rt/prio.py`. We rewrote that file last cycle and it is the only thing here that
is wrong.

The run that sent us back to it has four tasks: one at priority 1 that takes mutex 1, then mutex
2, and holds both for a while; one at 5 that wants mutex 2; one at 9 that wants mutex 1; and one
at 4 that holds nothing, wants nothing, and only ever runs. The urgent pair block at ticks 5 and
7, the holder is lifted to 5 and then to 9, and so far the scheduler is doing exactly what it
should; then it releases mutex 1 at tick 10 and goes straight back to 1, while the task at
priority 5 is still queued on mutex 2, which it is still holding. The task at 4 takes the
processor at tick 14. It keeps it for twelve ticks. The task at priority 5 waits through every one
of them, is granted its mutex at tick 29, and the `done` entry the run prints for it reads 33,
behind a task it outranks by one.

Rewrite `/app/rt/prio.py` so that stops happening.

What a task is worth is graded directly, at every tick, alongside the schedule that falls out
of it. Two requirements hold at once and they pull against each other: nothing may sit waiting
behind a task it outranks, and nothing may be worth more than the priority it started with
unless there is a task waiting on it that accounts for the difference, which stops being true
the moment that task is gone. We grade both directions. Lifting a task higher than it can
account for fails exactly as leaving it too low does, which means handing out urgency nobody is
owed, lifting a task nobody is waiting for, or leaving a task lifted after the last waiter
behind it has gone are all the same failure wearing different clothes, and the set we grade has
cases aimed at each of them. Safe is not a direction here.

Four moments are handed to you and they are the only ones you get. A task blocks on a held
mutex. A mutex is granted to somebody. A mutex is released. A task that was waiting gives up,
because the timeout it asked for ran out. `/app/rt/core.py` calls those four and nothing else,
and it reads what you set when it decides who runs next. The core object you are handed is the
one the scheduler itself uses, and it is the same object at every one of the four.

Some ground rules, because a couple of them are not what you would do elsewhere.

A mutex is handed to whichever waiter has been queued longest. Urgency does not jump the queue.
That is deliberate and it is not yours to change. A task that is waiting can be holding
something of its own, with a queue of its own behind it, and the sets we grade do that.

A wait that times out ends there. The task stops waiting, its attempt on the mutex has failed
and it carries on with whatever comes next in its program, while the mutex itself is untouched
and the holder still holds it.

The schedule is not yours either. Which task runs at a tick, when tasks arrive, how long a
critical section takes and when a job finishes are settled inside `/app/rt/core.py`, and we
compare the whole of it against a recorded run. What you set changes who the scheduler picks.
It has no other effect.

Only `/app/rt/prio.py` is kept. Every other file is restored from an untouched copy before the
graded run, so an edit anywhere else is thrown away and never graded, and the scheduler you are
measured by is the one that shipped. Keep the class name, the constructor and the four method
names exactly as they are. The core calls them by name.

Half the graded run is task sets built at the moment the verifier starts, out of a seed that
does not exist until then. There is no schedule for those that anybody could have worked out in
advance. They come from the same shapes as everything else and we check them the same way, so a
policy that is right about the cases somebody thought to write down and wrong in general will
pass the first half and fail the second.

`/app/run_sched.py` takes a file of task programs and prints the schedule, what every task was
worth at every tick, and a log of what the scheduler did. Build as many as you like. The list of
priority changes it prints is there for you and we do not grade it; what we grade is what the
tasks were worth when each tick was decided.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
