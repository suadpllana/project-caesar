# repair-orderbook-engine easiness probe, 2026-09-09: 3 of 3

The three trajectories beside this file are the agents' own words with the pasted brief
stripped (lines 1-25 of each upload), so `tools/leakcheck.py` can be run against them
without being circular. Commentary lives here and not in those files.

This probe ran on the bundle as it stood after the run-audit repair of the same day, which
added the output-channel contract (`out.row`, never `out.sink`) to the brief and to
`run_book.py`. Before that repair the task had passed the easiness probe and failed the run
audit on `task specification` (5 of 8) and `difficulty crux` (5 of 8): five agents solved
the semantics and were failed by the undocumented sink rule, three solved it outright.
So eight of eight audit agents and three of three probe agents formed the correct plan.
The sink trap was the only thing the task was failing anyone on.

## Runtimes

| trial | tool calls | outcome | what it built |
|---|---|---|---|
| 1 | 15 | reward 1 | journal undo, heap-indexed parked set, own deep-copy reference, 3,400 fuzzed sessions |
| 2 | 7 | reward 1 | journal undo, two heaps, restoration invariant over 300 random sessions |
| 3 | 9 | reward 1 | snapshot undo, heaps with lazy deletion, three hand-built nested sessions |

Budget 14400 s. Nobody explored anything that changed a plan.

## The signature, identical in all three

1. One or two tool calls: `find`, `wc -l eng/*.py`, `cat` everything. The whole engine
   is 132 lines under `eng/` plus 150 under `mkt/`.
2. A "found the bugs" summary naming every decision the task grades: `avail` returns the
   remainder, the band is pinned to the walk's first price, refill does not requeue, `check`
   sorts by trip price, `whole` has no undo, fill pace is not implemented.
3. **One write of all five files, correct.** Trial 1 revised `hold.py` once for style and
   once after its own fuzzer found dead levels treated as band barriers and a missing
   journal merge; trials 2 and 3 never revised.
4. A self-built reference or invariant check, then a timing table, then done.

## Where the plan came from

The brief. Every graded rule is stated in one sentence and none of the sentences interact
in a way the default plan gets wrong: the restoration list ("the book, last price,
quantities, shown amounts, queue positions, parked orders and waiting work") is a
checklist of what to snapshot, and every agent snapshotted or journaled exactly that.
The environment adds nothing the brief withholds. The self-written reference is the tell:
it can only catch implementation bugs, because it encodes the same reading of the spec as
the engine it checks, and there was no reading to get wrong.

Order-pace admission is the one place the environment nudges: all three kept a read-only
precheck there, because the shipped `room()` suggests it and under the old rules it was
correct. That is the plan the repair turns against.

## What the repair does about it

`tasks/repair-orderbook-engine/STATE.md`, "Easiness recovery 2026-09-09": a firing is never
taken back. The precheck plan fires nothing on a walk that would have failed; the
transaction plan fires and then re-parks; both pass every session where nothing parked
sits in the failed walk's path.
