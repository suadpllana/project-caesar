The tree under `/app` is the filing end of our code review tool. Reviewers hang
notes off lines. A note is written against one line of one revision, and when
the author pushes the next revision the note has to still be against the line
it was written about, or against nothing at all if that line is gone. That is
the whole promise. `/app/rev/store.py` keeps the revisions a branch has had,
`/app/scr/pin.py` settles the one change script we use between any two of them,
`/app/scr/grp.py` reads the changes out of a script, and `/app/note/board.py`
is meant to work out where every note stands once the store is asked.

We rewrote the board last month. Reviewers have stopped trusting it. Run
`/app/run_review.py` on `/app/streams/guard.txt`. That stream opens a note on
line 2 of the first revision, which is `    if not job:`, and then the second
revision deletes that line and the third types a different guard in somewhere
below it. The board answers `note 0 3` and `raise 0`. The note is alive. It is
sitting on line 3 of the head, and the author is being asked about a line
nobody wrote it about. The line it was written about went two revisions ago.
`/app/streams/rework.txt` and `/app/streams/repeat.txt` are two more streams to
drive it with.

Fix `/app/note/board.py` and `/app/note/rule.py`. Those two are yours and
nothing else is; every other file is compared against the shipped copy after
your work runs, one of the two may already be right, and the interfaces are
frozen, so keep each function and method that is there with the arguments it
has. `/app/run_review.py` is a driver for your own use. It is not graded.

The board holds nothing between requests. It is handed a store and the notes
that were opened against it, and it works the answer out from those and nothing
else, every time it is asked. There is no cache to warm and no state to keep.

Some ground rules, and a few of them are not what you would reach for.

A note follows the line it was written about, one revision at a time, as each
revision lands: we settle the change script between the new revision and the
one before it, a note whose line that script keeps moves to wherever the
script keeps it, and a note whose line that script does not keep retires there
and then, which is the end of it, because nothing later brings a retired note
back whatever turns up in the file afterwards. Which lines a script keeps is
the script's own business. It is not always what matching the text would give
you, because the files we review repeat themselves constantly and several
scripts of the same length exist for almost any pair of revisions of one of
them. `/app/scr/pin.py` settles that. What it settles is what the board
carries notes through.

A note that comes to rest inside one of the changes of that script is raised,
because the code around it moved and the reviewer has to look again. A change
is not only the lines a script added. It reaches across the kept lines that sit
between its runs, so a line can come through a revision untouched and still be
part of the change somebody has to read, and `/app/scr/grp.py` is what says
where one change stops and the next begins. Both halves are graded. Raising a
note the changes never reached is wrong, and leaving one unraised is wrong
too. Where two notes come to rest on the same line they become one: the older
takes the line and the newer is absorbed into it. Notes opened at a revision
join the board once that revision has landed and its carrying is done, and they
settle against whatever is already there.

We grade the log as well as the table, so the order events come out in is part
of the answer, and inside one revision that order is fixed: everything the
carrying retired comes first, then everything it raised, then the absorbing,
each of the three in ascending note order. Nothing else enters into it.

The streams we grade run to several revisions, and notes are opened partway
through as often as at the start. The files in them repeat their lines the way
real ones do. A line that looks like the line a note was written about is a
thing you should expect to see. A revision sitting between the one a note was
opened at and the head is the ordinary shape here.

Thirteen streams are written out by hand, one for each rule and one for each corner
where two of them meet, and three hundred more are built inside the verifier
from a seed drawn after your work is finished and settled there by a second
model of the same rule, one that shares no code with anything in your tree, so
a board that happens to fit the three streams sitting in front of you will not
carry. Every stream has to match exactly, in the table at the head and in the
log. There is no partial credit. There is no expected output anywhere in your tree and none is
coming. The tool in front of you is the only thing that will tell you what your
board does.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
