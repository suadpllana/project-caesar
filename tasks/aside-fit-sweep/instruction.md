`/app` is the allocator we try arena changes on before they go near the shipped one. A program is a text file of operations and `/app/progs` holds a few. Its first two lines are the geometry: `span` is how many bytes the arena has, `part` is the size of the equal pieces it is divided into, and every byte of it starts free. `span` is a multiple of `part` and both are multiples of 8. After those, `get` asks for a range under an id, `put` gives one back, `fit` asks for the range an id holds to be a different size, and `sweep` returns everything that has been set aside. That is the whole operation set. An id is any token.

`/app/run_pool.py` takes a program and prints what happened, a line per event.

We rewrote the placement half last cycle and it has been wrong since. Run `/app/run_pool.py` on `/app/progs/tiny.txt`. The last line comes out `at d 400 264`. That is wrong. It should be `at d 512 264`, because no range may straddle the boundary between two parts, and the 264 free bytes standing at 400 do not all lie in one of them. The files you may change are `/app/pool/find.py`, `/app/pool/cut.py`, `/app/pool/side.py`, `/app/pool/back.py` and `/app/pool/edge.py`. Nothing else.

A request is rounded up to the next multiple of 8. One that rounds to nothing, or to more than a part holds, is refused. A range is placed at the lowest address whose rounded bytes are all in the free map and all lie inside one part. If the free bytes standing immediately after it, up to the end of that part, number fewer than 16, they are given to the range too and it is that much larger than what was asked for.

A range of 256 bytes or less that is given back is set aside whole instead of going back to the free map. It joins no neighbour while it is there. Nothing is placed in it and nothing grows into it. What it is good for is a request of exactly its own size, which takes the one set aside most recently and takes it whole, with nothing left over and nothing added. A range over that size goes back to the map at once, where it joins the free bytes on either side of it but never a neighbour that is aside. At most 32 ranges are aside. Setting one aside past that returns the one set aside earliest to the map, joined there like any other, and a range that was set aside and then taken and set aside once more is as young as the last time it went there.

A request looks in the aside list first, by exact size, and at the free map second. One that neither can serve returns everything aside to the map and looks a second time. The aside list stays empty whether or not that second look finds anything.

`sweep` returns everything aside to the map and does nothing else.

`fit` rounds and refuses a size the same way. Asked for less than the range holds, it gives back the bytes past its new end exactly as `put` gives back a range, and it does nothing at all when there would be fewer than 16 of them. Asked for more, it grows where it stands only when the bytes it needs are in the free map and the whole of it still lies inside one part, and the rule about leftover bytes then applies at its new end; failing that, the new range is placed before the old one is given back, and if there is nowhere to place it the range is left exactly where it was.

An id is live from the moment a range is placed for it until that range is given back. A `get` for an id that is live is not an event. Neither is a `put` or a `fit` for an id that is not, and none of the three changes anything.

Every event is one line. It is printed when it happens and never sorted, and it prints `at <id> <address> <size>` when a range is placed for an id, `no <id>` when a request cannot be served, and `same <id> <size>` when a `fit` is answered where the range already stands. Giving a range back prints nothing, and neither does `sweep`. That is every event. Nothing else is printed.

Two of the big ones are in `/app/progs`. There `wide.txt` fills about two thirds of a four megabyte arena with small live ranges and small holes and then asks for sizes none of those holes can take, about 150 thousand operations in all; `churn.txt` drives the aside list past its bound tens of thousands of times over an arena of the same size. The graded set is three programs of each of those sizes and about four hundred small ones, and all of it has to get through inside 60 seconds. Time both. Then call it done.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
