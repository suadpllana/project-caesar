`/app` is the space accounting of a block store, the copy we try changes on before they go near the shipped one. A program is a text file of ops and `/app/progs` holds five. A `vol` line makes an empty volume. `set` gives a slot of a volume a fresh block, `clr` leaves a slot holding nothing, and `dup` gives one slot whatever another slot of the same volume is holding. `peg` makes a peg over a volume, `shed` takes a peg away, `fork` makes a volume that starts out holding exactly what a peg holds, and `back` gives a slot whatever a peg holds at a slot of its own. `trim` gives back everything nothing keeps and `tally` asks what one peg alone keeps. That is the whole op set. Blocks are named `b1`, `b2` and so on in the order they are allocated, so the first `set` in a program makes `b1`.

`/app/run_store.py` takes a program and prints `gone` and the block for every block a trim gives back, and `tally`, the peg and a number for every tally. A trim with nothing to give back prints nothing. Nothing else is printed at all.

We rewrote the accounting last cycle and it has been wrong since. Run `/app/run_store.py` on `/app/progs/tiny.txt`. The first line comes out `tally p1 2`. It should be `tally p1 1`: v1 is still holding b2, and a block a volume is holding is not a block one peg alone keeps. The files you may change are `/app/keep/live.py`, `/app/keep/cover.py`, `/app/keep/edge.py`, `/app/keep/gone.py` and `/app/keep/sole.py`. Nothing else.

A peg keeps whatever its volume holds at the moment it is made, and that never changes afterwards. Write a block into that volume later and the peg does not keep it; give one up later and the peg keeps it still. A volume holds a block while any of its slots holds it. Several slots may hold one block, and the volume gives it up only when the last of them does. Giving a slot the block it is already holding changes nothing.

A `back` can give a volume a block it had already given up. Pegs that volume made while the block was away keep nothing of it, and pegs made on either side of that absence each keep it. Any peg can be read this way, so a block can arrive in a volume that never held it before.

A `fork` gives the new volume its own hold on every block the peg holds, whichever volume wrote them, and pegs made over the new volume keep those blocks like any other. What happens to a volume after a fork happens to that volume alone. Shedding a peg ends that peg's keeping and nothing else: a volume forked from it goes on holding what it holds, and every other peg goes on keeping what it keeps.

A block that no volume is holding and no peg keeps is given back, but not at the moment it stops being kept: it waits for the next trim. The list one trim prints is in the order the blocks stopped being kept, and blocks that stopped during the same op are printed in the order they were allocated. A block that has been given back is never printed again.

`tally p` is how many blocks p keeps that nothing else keeps. Another peg keeping the block takes it out of that number, and so does a volume that is still holding it.

Programs are well formed. A volume is made before it is used and no name is used twice, a peg is not named again once it has been shed, and no op names a volume or a peg that does not exist. A slot holding nothing may still be named: clearing it changes nothing, and a `dup` or a `back` that reads it leaves the slot it writes holding nothing.

The three big ones are in `/app/progs`. `wide.txt` fills twenty-four thousand slots of one volume and then works over them for ninety thousand ops with about thirteen hundred pegs standing. `crop.txt` runs two volumes and makes twenty thousand pegs, shedding the oldest as each new one arrives. `fan.txt` fills five thousand slots and forks that volume thirty times, every fork going its own way afterwards. We grade three programs of each of those three sizes and about four hundred and fifty small ones, and all of it has to get through inside 120 seconds. Time it before you call it done.

Every line printed for every program is graded, exactly, on the programs in the tree and on programs you have not seen. Nothing outside the five files is read. `/app/store` and `/app/run_store.py` stay as they are.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
