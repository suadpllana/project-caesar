`/app` is the rebuild half of a service that copies a table into a new one while writes keep
arriving at the old one. The two are keyed differently. The source keys a row by an integer,
and where that row sits in the rebuild is decided by the first two of its three fields.
`/app/run_reb.py` takes a program file and prints a line for each thing that happens. `cfg C`
opens the file and fixes the chunk size. `set k a b c` puts the source row under key k with the
three field values that follow it, and `del k` takes that row out. `copy` walks the next chunk.
`play n` hands the next n journal entries to the replay. `cut` finishes the rebuild and is the
last line of every program. Each `set` and each `del` appends one entry to the journal, whose
positions run from 1. The cursor starts at 0. A source key is a positive integer below a
hundred thousand, each field is an integer below a hundred, C is between 1 and 5, and n is
never negative. `/app/progs` holds four programs, and a program is graded exactly as it stands.

We rewrote this half last cycle and it has been wrong since. Run `/app/run_reb.py` on
`/app/progs/tiny.txt`. The line for the second chunk comes out `chunk 1 4 4`. It should read
`chunk 1 3 4`: a chunk lands the cursor on the largest key it took, not on the top of the reach
it was given.

The files you may change are `/app/reb/walk.py`, `/app/reb/mark.py`, `/app/reb/sift.py`,
`/app/reb/place.py`, `/app/reb/wait.py` and `/app/reb/tally.py`. Nothing else. The rest of the
tree is replaced by our own copy before a program is run, a new file put beside those six
included.

A chunk takes the C smallest source keys standing above the cursor, as the source stands at
that moment. There may be fewer than C of them. It writes down the reach it covered, which is
every key above where the cursor was and at or below where it now is, against the length the
journal has reached at that moment, which is that reach's mark. A chunk that finds no key at
all leaves the cursor where it was and prints `chunk 0` with the cursor and `none`. Any other
chunk prints `chunk` with the number of keys it took, the cursor after it and its mark. It then
offers those keys to the rebuild in ascending order, by the rules a replayed entry follows.

`play n` takes the next n journal entries in position order, or every entry still waiting if
fewer than n are left, and each one it takes is finished with. An entry whose source key stands
above the cursor is dropped and prints `entry` with its position, its key and `ahead`; the walk
has not reached that key and will read the row itself. An entry at or below the cursor whose
position is at most the mark of the reach covering its key is dropped and prints `seen`,
because the chunk that carried the key was read after the entry was written. Every other entry
prints `done` and is applied.

A `set` entry that is applied names a row by its source key and carries the three fields as
they stood when it was written. If the rebuild already has that row and its first two fields
are unchanged, the third is taken and the row prints `same` with its key and its two fields,
whether the row is holding that key or only set aside for it. Otherwise the row first leaves
where it was: a row that was holding a key prints `off` with its key and the two fields it is
leaving and frees that key, and a row that was only set aside prints `drop` in the same shape
and frees nothing. It then asks for the pair its new fields name. A pair nobody holds is taken,
and the row prints `on` with its key and that pair. A pair already held sets the row aside for
it, printing `aside` in the same shape. When a pair is freed, the smallest source key set aside
for it takes it at once and prints `on`; the rest stay where they are.

A `del` entry that is applied takes the rebuild's row out the same way, printing `off` or
`drop` and freeing the key where it was held, and the rebuild forgets it. A `del` naming a
source key the rebuild is holding no row for prints `miss` with that key and does nothing else.

`cut` walks a chunk and then plays every entry still waiting, and repeats that until a chunk
takes no key. It then prints `end`. Three numbers follow it: the rows holding a pair, then the
rows set aside, then the third field added up over the rows holding a pair only. Nothing else
is printed.

`/app/progs/wide.txt` is a rebuild of seventy-seven thousand instructions whose source keeps
growing under the walk. `/app/progs/deep.txt` is one of a hundred and twenty-seven thousand
whose journal runs far longer than its source. The graded set is three programs of each of
those two shapes. Three hundred and twenty-four smaller ones across nine other shapes come with
them, and thirty-four written by hand. The whole set has to get through inside 60 seconds. Time
both. Then call it done.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
