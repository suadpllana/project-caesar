`/app` is our code review tool. A reviewer opens a thread on a stretch of
lines, the author replies, someone resolves it, and the thread has to stay with
the code it was opened on while the branch moves under it.
`/app/rev/store.py` holds the revisions a branch has had, `/app/scr/pin.py`
settles the one change script we use between two of them, `/app/scr/grp.py`
reads the changes out of a script, and `/app/note/board.py` with
`/app/note/rule.py` work out where the threads stand.

They are wrong. Run `/app/run_review.py` on `/app/streams/guard.txt`, where a
thread is opened on the two lines of a guard and a later revision takes both
away. The board prints `outdated 0` and then nothing. The thread is gone off
the table altogether, so the reviewer who asked the question cannot find it and
neither can the author. `/app/streams/repeat.txt` is worse in a quieter way. A
thread opened on lines 2 to 4 of a file that repeats itself comes back sitting
on lines 2 and 3 of the head, and those are not the lines it was opened on.
`/app/streams/rework.txt` is a third stream to drive it with.

Fix `/app/note/board.py` and `/app/note/rule.py`. Nothing else is yours. Every
other file is compared against the shipped copy after your work runs, and the
interfaces are frozen, so keep each function and method that is there with the
arguments it has. `/app/run_review.py` is a driver for your own use. It is not
graded. The board keeps nothing between requests, so it is handed a store and
everything the reviewers did and works the answer out from those and nothing
else, every time it is asked.

Some ground rules.

A thread covers a span of lines, and when a revision lands every line of that
span which the change script for that revision keeps moves with it while the
rest fall out, so the span shrinks as the code under it goes. A thread whose
span empties is outdated. That is where a thread stops. It stays on the board
with the empty span it ended on, and nothing after that carries it, raises it
or merges it. The files we review repeat themselves constantly, and for almost
any pair of revisions of one of them more than one change script of the same
length exists.

A thread is raised when the change first reaches any line of its span, and not
again while it stays reached; a revision has to let it go before it can be
raised a second time. Both halves are graded. Raising a thread the change
never reached is wrong, and leaving one unraised is wrong too. A resolved
thread is never raised. An answered one is. The reply it was carrying was about
code that has since moved, so being raised puts it back to open. Two threads
whose spans share a line are looking at the same code and become
one: the older keeps the thread and takes the union of the two spans, and the
newer is absorbed into it. Carrying does this more often than opening does,
because two spans that started apart get squeezed together by the deletions
between them, and a union can reach a thread that neither span reached on its
own. If either of the two was open the survivor is open, because the question
is unanswered whichever thread was carrying it. Threads opened at a revision
join once that revision's carrying and raising are done, and replies and
resolutions land after them.

We grade the thread table at the head, each thread with its state and its span,
and the log of what happened on the way, and because the log is a sequence the
order inside one revision is part of the answer: the outdatings come first,
then the raises, then the absorbings, each of the three in ascending thread
order, with a reopening written directly after the raise that caused it and an
absorbing naming the thread that ends up holding the span, whichever one
reached it first. The streams run to several revisions. Threads are opened
partway through as often as at the start, and a line that looks like the line a
thread was opened on is a thing you should expect to see. Seventeen streams are
written out by hand and three hundred more are generated, and every one has to
match exactly. There is no partial credit. There is no expected output anywhere
in your tree and none is coming. The tool in front of you is the only thing
that will tell you what your board does.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
