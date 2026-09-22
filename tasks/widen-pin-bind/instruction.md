`/app` is the binding stage of our front end, cut down to the part that decides which
declaration each call means. A program file declares the kinds, the entries a call can bind to
and the values it can be handed, and then the expressions to bind. `/app/run_bind.py` takes one
and prints a line for each thing it settles. `/app/progs` holds four of them.

`kind K` declares a kind. `rise A B` puts a step from A up to B, and no chain of steps comes
back to where it started. `entry f R P1 P2` declares an entry named f giving back R and taking
the slots P1 and P2. `open f B R P1 P2` declares one whose open slots are written `*`, where B is
its bound and `*` may stand in R and among the slots. `val x K` hands a value the kind K. An
`ask` line carries an expression, written `f(x,g(y))`. Entries are numbered from 0 in the order
they are declared. The calls inside one expression are numbered from 0 too, the outermost first
and then the arguments of each call left to right. Everything is declared before the first `ask`, every expression is
a call, and every call has at least one argument, so a name standing on its own is a value.

We rewrote this stage last cycle. It has been wrong since. Run `/app/run_bind.py` on
`/app/progs/tiny.txt`. Four lines should come out: `bind 0 0 1`, then `bind 0 1 0`, then
`res 0 c`, then `tally 2`. It prints the two bind lines the other way round. The tally comes out 1.
None of the other programs comes out right either.

The files you may change are `/app/res/kind.py`, `/app/res/pick.py`, `/app/res/pin.py`,
`/app/res/cost.py`, `/app/res/best.py` and `/app/res/walk.py`. Nothing else. The rest of the
tree is replaced by our own copy before a program is run, a new file put beside those six
included.

A kind rises to another when a chain of steps leads it there. Where it does, the number
of steps between them is the length of the shortest such chain. A kind rises to itself in no
steps. The candidates of a call are the entries carrying its name that take exactly as many
slots as the call has arguments. Every candidate is tried on its own, against the pins standing
when the call was reached. A trial that cannot take the call is put aside.

A call is bound asking for one kind, or asking for nothing. An expression on an `ask` line is
asked for nothing. A trial of an entry with an open slot that is not pinned binds those slots
first, in slot order, each asking for nothing. Then it settles the entry, at the kind every open
slot rises to that itself rises to every other kind they all rise to. Where there is no such
kind, or the settled kind does not rise to the entry's bound, the trial is put aside. An open
entry with no open slot is never taken. An entry that is already pinned is not settled again and
its open slots ask for the kind it holds. The remaining slots are bound after that, in slot
order, each asking for the kind it is declared with. What a slot asks for is what a call sitting
in it is bound asking for.

A slot costs the steps from the kind its argument stands at to the kind the slot asks for. A
value stands at its declared kind. A call stands at the kind its entry gives back. An
argument that does not rise to what its slot asks for puts the trial aside, and so does a call in
a slot that comes back ambiguous or with no binding. After the slots comes one more cost: the
steps from the kind the entry gives back to the kind the call was asked for. That is nothing when
the call was asked for nothing, and it puts the trial aside when it does not rise there. Those numbers
in slot order, with that last one after them, are what the trial is judged on.

The winner is the candidate that is no worse than every other surviving candidate at every one of
those numbers and better than it at one of them. A candidate left on its own survives and wins,
having nothing to beat. Where no candidate beats all the others the call is ambiguous, and where
none survives the call has no binding.

An entry with an open slot keeps the kind the first trial that was kept settled it at, and every
later call that binds to it is bound against that kind. A pin made while one slot was being bound
stands for the slots bound after it in the same trial. A trial that is put aside or beaten leaves
none of its pins behind. The winner hands its own back, in the order they were made, with the
pin of the winning entry itself last. Expressions are bound in the order they are written. Each
keeps what its winning trial pinned before the next one starts.

An expression that is bound prints `bind <ask> <call> <entry>` for every call it bound, the
outermost first and then the arguments of each call left to right. After those come
`pin <entry> <kind>` for every pin it kept, in the order they were made, and then
`res <ask> <kind>` with the kind its outermost entry gives back. An expression that is ambiguous prints `res <ask> amb` and one with no
binding prints `res <ask> none`, and nothing else. Expressions are numbered from 0 in the order
they are written. After the last one comes `tally <n>`, where n adds up every number that every
call of every winning trial that was kept was judged on. Nothing else is printed.

`/app/progs/deep.txt` is one expression nesting sixteen calls with three entries fitting at every
one of them. `/app/progs/wide.txt` is three hundred expressions over one declaration set. The
graded set is three programs of each of those two shapes, three hundred and twenty more spread
over eight smaller shapes, and thirty-two written by hand. All of it has to get through inside
60 seconds. Time both. Then call it done.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
