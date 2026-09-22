`/app` is the lock service of a storage engine, cut down to the part that decides who holds
what. Resources form three levels: a store `s0`, blocks `s0.b3` under it, keys `s0.b3.k7` under
those. A program is one statement per line and `/app/run_lk.py` replays one and prints a line
for each thing that happens. `lim 4` comes first and sets the widen threshold. `open t4` starts
a transaction; transactions are aged by the order of their `open` lines and the first opened is
the oldest. `take t4 s0.b3.k7 X` requests a mode, `drop t4 s0.b3` releases, and `shut t4`
finishes. `/app/runs` holds seven programs.

The service runs today and its answers are wrong. The files you may change are
`/app/lk/mode.py`, `/app/lk/hold.py`, `/app/lk/give.py`, `/app/lk/keep.py`, `/app/lk/wide.py`
and `/app/lk/step.py`. Nothing else. The rest of the tree is replaced by our own copy before a
program is run, a new file put beside those six included. `run_lk.run(text)` must return the
trace followed by the closing report, as a list of strings; it calls `step.run(text)`, which
returns the trace and then the hold table, the claims and the ages, and afterwards it calls
`book.held(t)`, `book.eff(t, res)`, `due.held(t)` and `due.owed(t, res)`. Keep those five.

Five modes: IS, IX, S, SIX, X. IS is compatible with every mode but X, IX with IS and IX, S
with IS and S, SIX with IS alone, X with nothing. Their supremum is the weakest mode at least
as strong as both, over IS below IX below SIX below X and IS below S below SIX below X, and the
supremum of IX and S is SIX. A transaction's mode at a resource is the supremum of two things:
the mode the program asked for there, if it ever asked, and the cover its own live grants below
that resource require. A grant at IS or S requires IS above it; a grant at IX, SIX or X
requires IX. The second half moves both ways, so a mode falls when the grants beneath it go and
rises when they come back. That supremum is the effective mode. It is what compatibility is
decided against and the only mode ever printed. A take that raises only what a transaction has
asked for, leaving the effective mode where it was, prints nothing at all.

A take is settled one level at a time from the store inward, and the service does not look
ahead. At each level it works out the effective mode that level must reach, and compares it
with every other transaction's effective mode there. Holders compatible with it are left alone.
If any incompatible holder is older than the requester, the take is refused: nothing the
requester asked for is granted, at any level, and the give-ups already forced at outer levels
stand, and the requester keeps whatever it held there already. A refused take leaves a claim on
the resource it named, at the mode it asked for. If every incompatible holder is younger, each
gives way, oldest of them first, and the take carries on to the next level. When the last level
passes, the requested mode joins whatever the transaction had already asked for there, the
effective modes of the chain follow from that, and any claim it had on that resource is gone.

A holder that gives way loses that resource and every grant it holds below it. Only a resource
the program asked for leaves a claim, at the asked mode, not at the effective mode that was
printed. A grant that existed only to cover something beneath it leaves nothing, because
retaking what is beneath will produce it again.

A claim is due when it is made, and again whenever the service moves what is held at the level
that last refused it. Nothing else wakes one. A sweep runs after every line over the claims
that are due when it starts, oldest transaction first, and within a transaction outermost
resource first, then by resource name. Each is tried once, as an ordinary take that can make
younger holders give way and can be refused by an older one, except that a refused retake
prints nothing. Whatever the sweep itself disturbs, including the claims its own give-ups
create, falls due for the next line, not tried again inside this one.

After the sweep, a transaction holding grants on more than `lim` children of one resource has
them replaced by a grant at that resource, asked for at the supremum of those children's
effective modes and of anything it had already asked for there. Whatever it held under those
children goes as well. Claims are not grants and do not count. The rule never makes anyone give
way: where the mode it needs is incompatible with another transaction's mode at that resource,
nothing happens and the children stay. It is applied to keys before blocks, in transaction age
order and then by resource name, and repeated until a full pass changes nothing. It does not
run again after the changes it makes.

`drop t4 s0.b3` removes every grant and every claim that transaction has at that resource or
below it, and then lets the levels above fall to what is left. Dropping something it neither
holds nor claims does nothing at all. `shut t4` removes everything that transaction holds or
claims. The trace prints seven things. `hold t4 s0.b3 IX` when a grant appears or rises to that
mode, `thin t4 s0.b3 IS` when one falls to it, `give t4 s0.b3 IX` when one is given up and IX
is the mode it had, `free t4 s0.b3` when one is released or when a cover with nothing left to
cover disappears, `wait t4 s0.b3.k7 X` when a take from the program is refused, `wide t4 s0.b3
X 5` when the widen rule replaces 5 children with a grant at X, and `shut t4`. The grants of a
successful take are printed outermost first. Giving way prints the deepest resource first, then
equal depths in resource order, and then the levels above as they fall; a release prints the
same way. `wide` comes after the `free` lines for what it replaced and before any change it
causes above. The report comes after the last line, transactions in age order, and for each one
`own t4 s0.b3 IX` per grant and then `due t4 s0.b3 X` per claim, each set in resource order: a
store before its blocks, a block before its keys, and lower numbers first.

Run `/app/run_lk.py` on `/app/runs/one.txt`. It opens `hold t0 s0 IX`, `hold t0 s0.b0 IX`,
`hold t0 s0.b0.k1 X`, and t1 then comes in under a shared cover with `hold t1 s0 IS`. Its
seventh line is `wait t1 s0.b0.k1 S`. When t0 drops that key the run prints `free t0 s0.b0.k1`,
`free t0 s0.b0` and `thin t0 s0 IS` in that order, and the sweep on the same line brings t1's
claim back as `hold t1 s0.b0.k1 S`. The last two lines are `own t0 s0 IS` and `own t0 s0.b1
IS`.

Your service is graded on programs you have not seen, and it has 60 seconds of wall clock for
the whole graded set. Some of them are large. `/app/runs/long.txt` is around twenty thousand
lines in which three transactions hold up to nine thousand keys each under a single block, and
`/app/runs/many.txt` is around twenty-five thousand lines across nearly four hundred
transactions where ten blocks nobody can enter carry eleven thousand standing claims while the
traffic runs elsewhere. The graded set is five programs of each of those two sizes, three
hundred and sixty smaller ones, and forty-four written by hand. `/app/runs/part.txt` and
`/app/runs/few.txt` are cut-down versions of the two big shapes. Time all of it.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
