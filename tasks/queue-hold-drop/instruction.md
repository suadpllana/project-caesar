`/app` is the write path of our offline-capable client for a shared record store, cut down to the
part that decides what the user sees and what goes to the server. A record has a parent and a set
of fields, and a field holds a whole number. A program is a text file of ops and `/app/progs`
holds four of them. `new t p` has the user make a record `t` under the parent `p`, where `p` is
`-` for the top; `set r f v` puts `v` in field `f` of record `r`; `add r f n` adds `n` to that
field; `mov r p` puts `r` under `p`; `cut r` removes `r`. Those five go on a queue in the order
the user makes them, and nothing else goes on it. Then `snd` sends what can be sent, `ok` and `no`
carry the server's answers back, an `oth` line followed by any of the five is a change another
client made, and of the two questions `ask r` prints one record as the user sees it while `all`
prints them all. `/app/run_edit.py` takes a program and prints a line for each thing that happens.

We rewrote this half last cycle and it has been wrong since. Run `/app/run_edit.py` on
`/app/progs/tiny.txt`. The first line comes out `rec q3 - k=22 w=-9` and it should read `none`,
since another client took that record away before the question was asked and a queued change to a
record the user can no longer see does nothing. The files you may change are `/app/pend/line.py`,
`/app/pend/fold.py`, `/app/pend/hold.py`, `/app/pend/view.py`, `/app/pend/lay.py` and
`/app/pend/reach.py`. Nothing else.

What the user sees is the confirmed records with the queue laid over them, each change in the
order it was made. The confirmed records move two ways. A change from another client lands in them
as it arrives, and an accepted change goes into them when its answer comes back. Laying a change
over a set of records means the same thing everywhere it is done. A creation makes its record
under the parent it names, and does nothing when those records already hold that name or do not
hold the parent. A field change sets its field, or adds to what that field holds at that moment. A
field nothing has set holds zero. A move puts its record under the parent it names, and does
nothing when the new parent is the record itself or lies under it. A removal takes its record and
every record under it, as the records stand at the moment that change is laid over and not as they
stood when the user made it. Any change naming a record that is not there at that moment does
nothing at all.

A change is about one record and may name a second. A creation is about the record it makes and
names its parent. A move is about the record it moves and names its new parent. The other three
name only the record they are about, and a creation or a move written against the top names only
its own record. A record another client made arrives already carrying the id the server gave it,
and those ids are the ones the program writes. A record the user made carries none until the
server answers its creation.

`snd` walks the queue from the front and sends every change it can. A change can go out once every
record it names carries an id, except that a creation does not wait for the record it makes. One
that cannot go out yet is held back. Holding spreads: a change held back puts the record it is
about beyond reach. Every later change naming a record beyond reach is held back too, and each of
those puts its own record beyond reach in turn. Changes that have already gone out are left alone.
A change held at one send goes out at a later one once the ids it was waiting on have arrived.

`ok` and `no` each answer the oldest change that has gone out and is still on the queue. An `ok`
takes its change off the queue and lays it over the confirmed records, and a creation answered
that way takes the next server id. The ids run `s1`, `s2` and upward, in the order the answers
hand them out. A `no` takes its change off the queue and lays it over nothing. Every later change
on the queue that names the record the refused change is about goes with it, and each of those
puts its own record in the same position for the changes after it. A change earlier on the queue
is never touched. An answer that finds no change to answer does nothing.

A removal the user makes against a record that carries no id, and whose creation is still on the
queue, does not join the queue at all. It takes that creation off instead. What goes with the
creation is worked out exactly as it is for a refusal, starting from the record that was to be
removed.

Every line is printed when it happens. A change going out prints `out <kind> <record>` in the
order the changes go, an `ok` prints `ack <kind> <record>`, a `no` prints `gone <count>` counting
the change refused as well, an answer with nothing to answer prints `idle`, `<kind>` is always the
word the change was written with, and a record is printed under the id the server gave it or under
the name the program made it with while it has none, which makes the `ack` of an accepted creation
the line that first shows the id that creation has just taken. `ask` prints `rec <record> <parent>
<field>=<value> ...` with the fields in name order, or `none` when the user cannot see that
record. The parent of a record at the top prints as `-`. `all` prints `row` lines of the same
shape for every record the user can see: the confirmed ones first, in the order they entered the
confirmed records, then the ones the server has not confirmed, in the order the user made them.
Nothing else is printed.

`/app/progs/pair.txt` is a second small program. `/app/progs/wide.txt` queues twenty thousand
changes with a question after each of them, and `/app/progs/deep.txt` stands a removal and a move
over a tree of twelve thousand records and then asks eight thousand questions against it. The
graded set is three programs of each of those two sizes and four hundred and ninety-one small
ones, and all of it has to get through inside 60 seconds. Time both. Then call it done.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
