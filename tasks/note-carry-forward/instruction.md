`/app` is our code review tool. Reviewers leave notes on lines, and a note has
to stay with the line it was written about as the branch moves on.
`/app/rev/store.py` holds the revisions a branch has had, `/app/scr/pin.py`
settles the one change script we use between two of them, `/app/scr/grp.py`
reads the changes out of a script, and `/app/note/board.py` with
`/app/note/rule.py` work out where the notes stand.

They are wrong. Run `/app/run_review.py` on `/app/streams/guard.txt`: that
stream opens a note on line 2 of the first revision, which is
`    if not job:`, the second revision deletes that line, the third types a
different guard in below it, and the board answers `note 0 3` and `raise 0`,
so the note is alive on a line nobody wrote it about two revisions after the
line it was written about went. `/app/streams/rework.txt` and
`/app/streams/repeat.txt` are two more streams to drive it with.

Fix `/app/note/board.py` and `/app/note/rule.py`. Nothing else is yours. Every
other file is compared against the shipped copy after your work runs, and the
interfaces are frozen, so keep each function and method that is there with the
arguments it has. `/app/run_review.py` is a driver for your own use. It is not
graded. The board keeps nothing between requests, so it is handed a store and
the notes that were opened against it and works the answer out from those and
nothing else, every time it is asked.

Some ground rules.

A note is against a line, it stays against that line for as long as the line
survives, and a line survives a revision when the change script for that
revision keeps it. When the line goes the note retires. A retired note is
finished, and nothing later brings it back whatever turns up in the file
afterwards. The files we review repeat themselves constantly, and for almost
any pair of revisions of one of them more than one change script of the same
length exists.

A note is raised when its line becomes part of the change a revision made,
because the code around it moved and the reviewer has to look at it again.
While it stays part of one we have already asked, so it is not raised again
until a revision leaves it outside a change. Both halves are graded. Raising a
note the change never reached is wrong, and leaving one unraised is wrong too.
Where two notes come to rest on the same line they
become one: the older takes the line, the newer is absorbed into it, and notes
opened at a revision join the board once that revision has landed and its
carrying is done, settling against whatever is already there.

We grade the note table at the head and the log of what happened on the way.
The log is a sequence, so inside one revision the retirements come first, then
the raises, then the absorbing, each of the three in ascending note order. The
streams we grade run to several revisions, notes are opened partway through as
often as at the start, and a line that looks like the line a note was written
about is a thing you should expect to see. Fifteen of them are written out by
hand and three hundred more are generated, and every one has to match exactly
in the table and in the log. There is no partial credit. There is no expected
output anywhere in your tree and none is coming. The tool in front of you is
the only thing that will tell you what your board does.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
