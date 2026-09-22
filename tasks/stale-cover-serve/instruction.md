`/app` is the read path of a key-value service: a cache of key ranges sitting in front of a
store whose rows are versioned. Run a program through it with `python /app/run_rng.py <file>`,
which replays the program and prints one line per commit and one or more lines per read. Four
sample programs are in `/app/progs`.

A program is plain lines. The first line is `h H G F` and fixes three numbers for the run: the
retention horizon H, the slack G the service will tolerate when it combines fetches, and the cap
F on how many fetches one read may issue. `w k v` stages a write of value v at key k, `x k`
stages a delete of key k, and `c` commits everything staged since the last commit as one new
version. `r lo hi s` is a client read of the closed key range lo to hi that will accept an answer
up to s versions old. Keys and values are non-negative integers, lo is never above hi, and F is
never below 1.

The store starts empty at version 0 and every `c` raises the version by one, whether or not
anything was staged; a commit that stages nothing writes no key. A staged write or delete writes
its key whether or not it changes what is there, and two staged operations on one key leave the
later one and count as a single write of that key. Writing back the value a key already holds is
a write.

Everything the cache knows it learned from a fetch, and it knows it for a run of versions, not
for an instant. A fetch of a key range returns the store's content over that range as it stands.
The store also reports the newest version at which it wrote any key in that range, or version 0
when it has never written one of them. From that version up to the present, the
content just fetched was the store's content over that range at every version in between. A
later commit that writes a key inside that range ends the run: the fetched content was the
store's up to the version before that commit and no further. A commit that writes nothing inside
a range leaves its run open, and an open run keeps extending as new versions arrive.

A read is answered as of a single version, and every part of the answer must be content the
cache still accounts for at that same version. Call the current version N. The version a read is
answered at is at most N and at least N - s, and never below 0. When some version in that band
has every key of lo to hi inside content the cache accounts for at that version, the read is
answered from the cache at the largest such version and no fetch is issued. When no version in
the band does, the read goes to the store instead and is answered at N. Nothing in between: a
read either takes one version whole or takes the present one.

That trip is shaped before any of it is sent. Start from the maximal runs of keys within lo to
hi that no content the cache accounts for at N covers, in increasing key order.
Working up from the lowest, a run that begins no more than G keys after the previous one ends is
taken together with it as a single run spanning both and the ground between them. If more than F
runs are left after that, all of them are dropped and the whole of lo to hi is fetched as one run
instead. Each remaining run is one fetch, issued in increasing key order, and what comes back is
kept as the run it was fetched in: a combined or capped run is one piece of knowledge, correct
from the newest version at which the store wrote any key across the whole of it, and it is not
folded into anything the cache already holds even where it covers the same keys.

Retention runs after each commit. Content whose last correct version is below N - H is discarded
and can answer nothing further. Content whose run is still open is never discarded, however long
ago it was fetched.

The trace is exactly this. A commit prints `v N` with the version it created. Each fetch prints
`f lo hi` with the first and last key of the run fetched.

Each read then prints one line: the letter `a`, the version the read was answered at, and the
live rows of lo to hi as of that version in increasing key order, each written `k=v`, all
separated by single spaces. A read whose range holds no rows at that version prints `a` and the
version followed by a single `-`. Every key appears at most once on an answer line.

The graded artifact is these seven files and nothing else: `/app/rng/seg.py`,
`/app/rng/pick.py`, `/app/rng/hole.py`, `/app/rng/mend.py`, `/app/rng/knit.py`,
`/app/rng/age.py` and `/app/rng/ask.py`. They are laid over a pristine copy of the rest of the
tree before anything is run, so edits to `/app/run_rng.py`, `/app/rng/spec.py`,
`/app/rng/store.py`, `/app/rng/out.py` or `/app/rng/__init__.py` are discarded, and a new file
anywhere is never collected. `/app/run_rng.py` calls `seg.Table()`, then
`ask.settle(table, touched, now, tune)` after each commit and
`ask.read(table, store, lo, hi, s, tune)` for each read, so those three names and their
arguments have to stay as they are.

Grading replays every graded program in one process and gives that stage 60 seconds of wall
clock for the whole set. Programs run to the scale of `/app/progs/wide.txt` and
`/app/progs/deep.txt`. Those two are about 38000 and 29000 lines, with keys up to 2047, twelve
thousand versions in a run, and reads whose allowance reaches back across the whole history. A
cache that answers every program correctly and does not get through the set inside the limit
scores the same as one that answers them wrongly.

For the shape of it, the sample `/app/progs/tiny.txt` writes two keys, commits, then reads
`0 4` and `1 3` with no allowance on either. It prints `v 1`, then `f 0 4`, then
`a 1 1=10 3=30` twice: the first read has nothing cached and takes the range, the second is
already inside what the first fetched.

Every graded program is compared line for line against the answer it should give, and one wrong
line anywhere fails the whole run.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
