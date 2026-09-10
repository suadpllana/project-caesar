`/app` is the claim service we try changes on before they go near the store. A program is a text
file of steps and `/app/progs` holds a few. A `take` line names a transaction, an item, and a mark
it wants on that item. A `drop` line gives one claim back. An `end` line finishes a transaction.
That is the whole step set. Transactions are named `t` and a number, and `/app/run.py` takes a
program and prints what happened to stdout, a line per event.

There are five marks. `/app/hold/tab.py` says which two of them may stand together on one item,
held by different transactions, and nothing else about them is written down anywhere. The mark
that covers a set of marks is the least mark in that table excluding everything all of them
exclude. For these five there is always exactly one.

Run `/app/run.py` on `/app/progs/turn.txt`. It prints `wait t3 k2 edit`. That is wrong. t3 already
holds k2, the only other claim on it is t6's pin, and pin stands beside edit, so the line should
be `give t3 k2 edit`.

The files you may change are `/app/hold/mark.py`, `/app/hold/item.py`, `/app/hold/wait.py`,
`/app/hold/cyc.py` and `/app/hold/txn.py`. Nothing else: the rest of the tree is replaced by our
copy before any of this is graded.

A take by a transaction that already holds the item is a raise. The mark it is tested in covers
everything it holds there and the mark it asked for, so a raise never gives up what it had, while
a take by a transaction holding nothing there is tested in the mark it asked for and nothing more.
Either way it stands when its mark stands beside the mark every other transaction holds on the
item, the one covering that transaction's whole stack there, never the claims under it. Its own
claims never count.

An item is swept whenever its claims or its requests change. Raises go first. They are taken in
the order their transactions came to hold the item, each one that stands is granted, and one that
does not is passed over while the raise after it is still tried. Then, if no raise was passed
over, the first-time claims are taken in the order they were asked, granted while they stand, and
the walk stops at the first that does not stand. While a raise is outstanding, no first-time claim
is granted on that item at all, whatever it asked for and whatever is held there.

A transaction keeps a stack of claims per item. A grant puts the asked mark on top of it and the
mark held there is the one covering the whole stack. A drop takes the top one off and the mark
falls back to what covers the rest. When the stack empties the transaction no longer holds the
item. Every drop in a program names an item its transaction holds at that point.

Waiting is defined this way. A transaction with a request that has not been granted waits for
another transaction if the sweep of its item would grant that request once the other one is taken
out of the service, with every claim it holds and the request it has made. Nothing else counts as
waiting.

After every step of the program, once everything the step granted has run as far as it can, the
service looks for a ring in that relation, and while there is one it cuts a transaction: the one
on a ring holding claims on the fewest items, and if two are level, the one whose request was made
later, and if still level, the one with the larger number. A cut takes the victim's request and
all of its claims out. Then it sweeps the items it held, in the order it came to hold them, and
after those the item its request was on if it held no claim there. Then it looks again. A cut can
leave another ring standing.

Once a take is not granted its transaction is stopped, and that transaction's later steps in the
program wait until the request goes through. A transaction whose request is granted joins the back
of one line. The line runs once the step that filled it is over, every sweep of that step included:
from the front, one transaction at a time, each running the steps it was holding until it is
stopped again, ends, or runs out, and never interrupted while it runs. Whatever its steps grant
joins the back of the same line, behind everything granted before it, and waits its turn. The line
is empty before the service looks for a ring, after a program step and after a cut alike. An end
finishes a transaction and sweeps the items it held in the order it came to hold them. A
transaction that has been cut or has ended is finished. Its remaining steps in the program do
nothing at all.

Every event is one line, printed when it happens. Nothing is sorted. `give` names the transaction,
the item, and the mark it now holds there. `wait` names the transaction, the item, and the mark the
request is tested in, and is printed once, when the request is made and the sweep that follows
does not grant it. `free` names the transaction, the item, and the mark left on it, or `-` when
the stack has emptied. `cut` and `done` name a transaction and nothing else. Nothing else is
printed.

`/app/run.py` makes one `Svc` from `/app/hold/txn.py` for the program, hands it a `Trace` from
`/app/hold/out.py`, and calls `step` once for each line. The graded run does the same and imports
the service fresh for every program, so nothing may be carried from one program to the next. Two
of the big ones are in `/app/progs`. The graded ones are larger than those samples: one item held
by six thousand transactions with a raise stuck across it and a queue of claims behind it, and a
thousand items each carrying a request that never goes through while several thousand steps of
work happen on other items entirely. Four hundred and thirty-nine programs are graded and the
whole set has to get through inside 60 seconds. Time yourself on both.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
