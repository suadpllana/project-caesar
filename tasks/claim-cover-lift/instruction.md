The store under `/app` hands out claims. It has two levels: boxes, named b1 and up, and slots
inside them, named b1:s1 and up. Jobs are named j1 and up. A job claims a box or a slot in mode
r or w. A program is one operation per line, and the service prints the events it decides. Run
one with `python hbctl.py tapes/small.txt` from `/app`.

The operations are `take <job> <node> <mode>`, `drop <job> <node>`, `end <job>`,
`show <node>`, and `fill <job> <box> <count> <mode>`, which takes slots s1 to s<count> of that
box one at a time. The events are `grant <job> <node> <mode>`, `wait <job> <node> <mode>`,
`lift <job> <box> <mode>`, `free <job> <node>`, `stop <job>`, `done <job>`, and
`at <node>` followed by a job and its modes for each holder.

The service ships deciding some of these wrongly. Make it decide them as below.

Nodes are put in order by box number first, a box before its own slots, then by slot number, and
the numbers compare as numbers, so b10 comes after b2 and s12 after s2. Jobs are put in order by
number the same way.

Two modes conflict when at least one of them is w. A claim on a box conflicts with the claims
of another job on that box and on every slot of it. A claim on a slot conflicts with the claims
of another job on that slot and on its box. Two different slots are unrelated. Nothing a job
holds ever blocks its own request.

A claim granted to a job adds one acquire, so what a job holds on a node is the list of acquires
granted to it there. A drop gives back the one added most recently and prints free; a drop
naming a node the job does not hold prints nothing. A show prints at and the node. After that
comes every job holding that node, in job order, each followed by its acquires as mode letters
sorted together, so a job holding two in r and one in w prints rrw. A node nobody holds prints
the node and nothing else.

A request is granted at once, ahead of anything that would otherwise block it, when the asking
job already holds a claim on that node or on its box in a mode that covers it. A claim in w
covers a request in either mode. A claim in r covers a request in r. A claim on a slot covers
nothing on its box.

Any other request is granted when nothing blocks it. Two things block it: a granted claim of
another job that conflicts with it, and a waiting request of another job that conflicts with it
and holds a smaller sequence number. A blocked request prints wait and takes the next sequence
number. The numbers come from one counter for the whole store, not one per node.

A request for a slot is lifted when the asking job holds no claim covering it on that slot's box
and already holds granted claims on four or more distinct slots of that box. The request becomes
a request for the box, in mode w if it or any of those claims is in w and in r otherwise; it
prints lift and is then granted or made to wait by the two rules above. A lifted request that
waits keeps the job's slot claims until it is granted. When it is granted, the job's acquires on
every slot of that box are given back in slot order, each printing free, and then the request
that caused the lift is granted and prints grant, naming the slot and the mode it asked for.

After anything a job holds changes, the waiting request with the smallest sequence number that
can now be granted is granted, and that repeats until no waiting request can be granted.

One job waits for another when that other blocks its waiting request, whether by a granted claim
or by an older waiting request. Once no waiting request can be granted and some job lies on a
cycle of that relation, one job is stopped. The one stopped is the job on any cycle holding the
fewest acquires, counted with repetition. A tie goes to the largest job number. Stopping
prints stop, takes that job's waiting request out of the line, and gives back every acquire it
holds in node order, each printing free. Granting then resumes and the check is made again, until
no job lies on a cycle.

A job ignores every line naming it while its own request is waiting. So does one that has ended.
So does one that has been stopped. An end gives back every acquire the job holds in node order,
each printing free, prints done, and then granting resumes.

The program in `/app/tapes/show.txt` shows the shape of a trace. In it j1 takes `b1:s1` in w,
j2 takes `b1:s2` in r, j3 asks for `b1:s1` in r, j1 drops `b1:s1`, the node is shown, and j2
ends, and it prints
`grant j1 b1:s1 w`, `grant j2 b1:s2 r`, `wait j3 b1:s1 r`, `free j1 b1:s1`,
`grant j3 b1:s1 r`, `at b1:s1 j3 r`, `free j2 b1:s2`, `done j2`, one to a line and in that
order.

Six files are taken from your container: `/app/hb/book.py`, `/app/hb/fit.py`,
`/app/hb/line.py`, `/app/hb/lift.py`, `/app/hb/snarl.py` and `/app/hb/door.py`. Nothing else you
write is read.

Every other file under `/app` is replaced by an unmodified copy of the tree as it ships, so
`/app/step.py`, `/app/hbctl.py`, `/app/hb/desk.py` and `/app/hb/tell.py` cannot be changed and a
new file you add under `/app` is not used. How those six divide the work between them is yours to
decide, as long as `step.py` still finds `door.take`, `door.drop`, `door.end` and `book.who` where
it calls them, with the arguments it passes now.

The programs under `/app/progs` are examples. The graded programs are generated after your
container is gone, so none of them can be answered from a table. Each is run and every line it
prints is compared with the line expected, in order, and one wrong line anywhere fails the task.
The whole graded set runs in one process, on 1 CPU with 2048 MB. It must finish within 60
seconds. A graded program can be forty thousand lines long, can name five hundred boxes, and can
leave one box holding forty thousand slot claims while other jobs are still asking for it.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
