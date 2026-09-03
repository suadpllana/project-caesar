We run a small clearing house for a handful of members and `/app` is the whole of it. Members
owe each other all through the day, and every obligation names who pays, who is paid, how
much, and the day it falls due. There are 6 members on the book we run against now. The house
keeps a balance for each of them and a line of that member's outstanding obligations in the
order it wrote them down, and at every tick it settles a round.

`/app/run_day.py` takes a day file and prints what the house did, a row at a time, with every
member's holding at the close of each round. Put `/app/days/queue.txt` through it. The first
round comes back `gone q1 1`, `gone q2 1`, `gone q3 1`, and then `hold ax 3`. Three
obligations abandoned in a single round. We are wearing that every day the house runs, in ones
and twos, and its members have started reconciling their own positions by hand.

We need the rounds rebuilt. The four files that decide them are `/app/house/drn.py`,
`/app/house/gvp.py`, `/app/house/rnd.py` and `/app/house/due.py`, and those are yours to
change. Nothing else is. The rest of `/app/house` is the book, and the book does what it is
told: it moves the money, it writes the rows, and it holds no opinion about whether what it
was told was right.

Some ground rules, because several of them are not what you would do elsewhere.

A member's obligations leave from the front of its line, never one before the one in front of
it. The line is the order the house wrote them down, which is not the order they fall due, so
an obligation whose day has not come can be standing at the front of a line with a much older
one waiting behind it, and a round may settle nothing before its day and stops at the first
obligation whose day has not come, whatever sits behind that. Something a round cannot reach
is not something a round has abandoned. It waits. A later round takes it. No member may end a
round holding less than nothing, and a round leaves nothing on the table: when it is over
there must be nothing further it could have moved without taking an obligation out of turn or
leaving somebody short. Both halves are graded. We lose money when a round moves too little,
and we lose the house when a round moves too much. Whatever a round could reach and did not
move has missed its day. The house does not carry it forward. It goes, and the payee never
sees it, and the oldest goes first, where oldest means the order the house wrote them down in
and not the order they fell due. Anything still outstanding when the last round of the day
ends stays outstanding.

Cash paid in from outside lands before the round at that tick. It comes from nowhere else.

Two things about the days the house sees, because a small test file will not show you either
of them. Members owe each other both ways within a single day. And a member can owe more than
one thing falling due on the same day. The days we grade do both. Every obligation is for a
whole number of units, at least one, and no member owes itself. `/app/days` holds four days to
run against. They are ours. They are small. The days the house actually sees are longer, with
more counterparties in them and more falling due at once, so treat those four as a way to
watch the book work and never as a description of what turns up.

What we grade is the record the book keeps and the sheet it ends with. The record is the
ordered rows `/app/run_day.py` prints: which obligation moved, which one the house gave up on,
and what every member was holding at the close of each round, and the sheet is what became of
every obligation and the tick it happened on. Both come out of the book and not out of
anything you write. Both are compared exactly. Days we have never shown you are part of it, so
a round that fits the four days in `/app/days` and nothing else is a round that fails.

The house is quick enough already and nothing here carries a budget. Do not change the book.
Do not change what `/app/run_day.py` prints, and do not change the shape of what the four
files you own hand back to it, because the book calls them and we run other things against the
same interfaces. Python 3.12. No third-party packages, integers throughout.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
