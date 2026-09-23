"""The enumerated launches: one per graded decision, and both sides of every fence.

Each launch is small enough to trace by hand. The name of a case is the rule it pins, so a
failure says which rule broke rather than "a generated launch was wrong".

  plain-apart          ordinary blocks on lines nobody shares: exact cycles, nothing stale
  place-most-free      a freed multiprocessor takes the next block, not block number mod S
  place-spread         at the start blocks go one to each multiprocessor, lower number first
  place-next-cycle     an exit frees its slot the cycle after; the successor issues at once
  turn-after-last      each multiprocessor issues after the slot that issued last, wrapping
  turn-spinner         a spinning block takes its turn and delays its neighbour
  sm-order             a store on multiprocessor 0 is seen by 1 in the same cycle
  work-wake            work of v cycles issued at t makes the block ready at t+v
  fill-whole-line      a fill copies four words as they stand; a neighbour read later is old
  stale-elsewhere      a store on one multiprocessor leaves another's cached copy old
  store-own-copy       a store updates the storer's own cached copy
  store-no-fill        a store that misses does not fill the line
  inherit-line         a block placed later reads the stale line its predecessor fetched
  fifo-drop            the line filled earliest goes, however recently it was hit
  cg-drops-own         a bypassing load drops its own multiprocessor's copy of the line
  cg-leaves-others     a bypassing load leaves other multiprocessors' copies alone
  atom-no-cache        an atomic leaves the issuer's cached copy as it was
  fence-own            a fence empties only the issuer's cache
  fence-refresh        after a fence the next cached load fetches again
  spin-cg-store        a bypassing spin sees a store made on another multiprocessor
  spin-tests           lt is strict and ne means not equal, the loaded value on the left
  spin-evicted         a stale spinner is released when a neighbour's fill pushes its line out
  spin-dropped         a stale spinner is released when a neighbour's bypassing spin drops the line
  spin-fenced          a stale spinner is released when a neighbour fences
  skip-rotation        after a long frozen stretch the rotation is where the stretch left it
  skip-not-frozen      a stretch with a missing spin line is not frozen and is not skipped
  sum-issues           a sum takes one issue per line, sharing the rotation with its neighbours
  sum-start-line       a sum starts at the whole line holding its address
  sum-stale-copy       a cached sum adds a stale copy; a bypassing one reads memory and drops it
  sum-fills            a cached sum fills every line it misses, oldest fill dropped first
  sum-cg-no-fill       a bypassing sum fills nothing, so it pushes no other line out
  sum-releases-spinner a stale spinner is let go at the fill of a neighbour's sum that evicts it
  sum-cg-releases      a stale spinner is let go when a neighbour's bypassing sum drops its line
  sum-race-order       a store lands in a sum only before the sum reaches its line, SM order
                       deciding within a cycle
  sum-trailing         a sum behind another on the same lines reads the leader's copies
  sum-evicts-prefetch  a prefetched stale line survives to the sum on a quiet multiprocessor and
                       is pushed out first on one whose neighbour streams
  sum-interrupted      blocks waking mid-sum join the rotation and stretch it
  sum-not-spin         no hang while a block is still summing
  hang-residency       a grid barrier larger than the device hangs, with blocks never placed
  hang-stale           a cached spin that nothing refreshes hangs
  hang-thrash          spinners that keep pushing each other out, all failing, hang from the start
  hang-after-pass      a spinner released inside an all-spinning stretch moves the hang later
"""

CASES = {
    # --- placement, rotation and timing -----------------------------------------------
    "plain-apart": """
dev 2 2 2
grid 4
show 0 4 8 12
prog
mov r1 %bid
mul r2 r1 4
mul r3 r1 5
add r3 r3 2
work r3
st [r2] r3
ld.ca r4 [r2]
out r4
exit
""",
    "place-most-free": """
dev 2 2 4
grid 6
prog
mov r1 %bid
mod r2 r1 2
brz r2 long
exit
long:
work 40
out r1
exit
""",
    "place-spread": """
dev 3 2 4
grid 5
prog
mov r1 %sm
out r1
exit
""",
    "place-next-cycle": """
dev 1 1 4
grid 3
prog
out %bid
exit
""",
    "turn-after-last": """
dev 1 3 4
grid 3
prog
mov r1 %bid
add r1 r1 1
add r1 r1 1
out r1
exit
""",
    "turn-spinner": """
dev 1 2 4
grid 2
show 40
prog
mov r1 %bid
brnz r1 worker
spin.cg r2 [40] eq 1
out r2
exit
worker:
add r3 r1 1
add r3 r3 1
add r3 r3 1
add r3 r3 1
st [40] 1
exit
""",
    "sm-order": """
dev 2 1 4
grid 2
show 8
prog
mov r1 %bid
brnz r1 reader
st [8] 5
exit
reader:
ld.cg r2 [8]
out r2
exit
""",
    "work-wake": """
dev 1 2 4
grid 2
prog
mov r1 %bid
mul r2 r1 3
add r2 r2 4
work r2
out r2
exit
""",
    # --- the caches -------------------------------------------------------------------------
    "fill-whole-line": """
dev 2 1 4
grid 2
mem 2 3
show 2
prog
mov r1 %bid
brnz r1 writer
ld.ca r2 [1]
work 12
ld.ca r3 [2]
out r3
exit
writer:
work 4
st [2] 7
exit
""",
    "stale-elsewhere": """
dev 2 1 4
grid 2
mem 16 1
show 16
prog
mov r1 %bid
brnz r1 writer
ld.ca r2 [16]
work 12
ld.ca r3 [16]
out r2
out r3
exit
writer:
work 4
st [16] 9
exit
""",
    "store-own-copy": """
dev 1 1 4
grid 1
mem 20 2
show 20
prog
ld.ca r2 [20]
st [20] 6
ld.ca r3 [20]
out r2
out r3
exit
""",
    "store-no-fill": """
dev 2 1 4
grid 2
show 5
prog
mov r1 %bid
brnz r1 writer
st [4] 1
work 12
ld.ca r3 [5]
out r3
exit
writer:
work 5
st [5] 8
exit
""",
    "inherit-line": """
dev 2 1 4
grid 3
mem 0 7
show 0
prog
mov r1 %bid
brz r1 first
sub r2 r1 1
brz r2 second
work 20
ld.ca r3 [0]
out r3
exit
first:
ld.ca r3 [0]
out r3
exit
second:
work 10
st [0] 9
exit
""",
    "fifo-drop": """
dev 2 1 2
grid 2
show 0 4
prog
mov r1 %bid
brnz r1 writer
ld.ca r2 [0]
ld.ca r2 [4]
ld.ca r2 [0]
work 12
ld.ca r2 [8]
ld.ca r3 [0]
ld.ca r4 [4]
out r3
out r4
exit
writer:
work 6
st [0] 5
st [4] 6
exit
""",
    "cg-drops-own": """
dev 2 1 4
grid 2
show 1
prog
mov r1 %bid
brnz r1 writer
ld.ca r2 [0]
work 12
ld.cg r3 [0]
ld.ca r4 [1]
out r4
exit
writer:
work 4
st [1] 9
exit
""",
    "cg-leaves-others": """
dev 2 1 4
grid 2
mem 1 4
show 1
prog
mov r1 %bid
brnz r1 other
ld.ca r2 [1]
work 12
ld.ca r3 [1]
out r3
exit
other:
work 4
ld.cg r2 [0]
st [1] 9
exit
""",
    "atom-no-cache": """
dev 1 1 4
grid 1
mem 12 3
show 12
prog
ld.ca r2 [12]
atom.add r3 [12] 4
ld.ca r4 [12]
out r3
out r4
exit
""",
    "fence-own": """
dev 2 1 4
grid 2
mem 24 1
show 24
prog
mov r1 %bid
brnz r1 other
ld.ca r2 [24]
work 14
ld.ca r3 [24]
out r3
exit
other:
ld.ca r2 [24]
work 4
st [24] 8
fence
ld.ca r3 [24]
out r3
exit
""",
    "fence-refresh": """
dev 2 1 4
grid 2
mem 28 1
show 28
prog
mov r1 %bid
brnz r1 writer
ld.ca r2 [28]
work 12
fence
ld.ca r3 [28]
out r3
exit
writer:
work 4
st [28] 5
exit
""",
    # --- spinning -----------------------------------------------------------------------------
    "spin-cg-store": """
dev 2 1 4
grid 2
show 44
prog
mov r1 %bid
brnz r1 setter
spin.cg r2 [44] ge 3
out r2
exit
setter:
work 9
atom.add r3 [44] 3
exit
""",
    "spin-tests": """
dev 2 1 4
grid 2
mem 8 5
show 8 12
prog
mov r1 %bid
brnz r1 setter
spin.cg r2 [8] lt 3
out r2
spin.cg r3 [12] ne 0
out r3
exit
setter:
work 4
st [8] 3
work 4
st [8] 2
work 4
st [12] 7
exit
""",
    "spin-evicted": """
dev 1 2 1
grid 2
show 0
prog
mov r1 %bid
brnz r1 other
ld.ca r2 [0]
spin.ca r3 [0] eq 1
out r3
exit
other:
work 6
atom.add r4 [0] 1
work 6
ld.ca r5 [8]
out r5
exit
""",
    "spin-dropped": """
dev 1 3 4
grid 3
show 0 1
prog
mov r1 %bid
brz r1 a
sub r2 r1 1
brz r2 b
work 9
atom.add r3 [0] 5
atom.add r3 [1] 1
exit
a:
ld.ca r5 [0]
spin.ca r4 [0] ge 5
out r4
exit
b:
work 4
spin.cg r4 [1] eq 1
out r4
exit
""",
    "spin-fenced": """
dev 1 2 4
grid 2
show 32
prog
mov r1 %bid
brnz r1 other
ld.ca r2 [32]
spin.ca r3 [32] eq 2
out r3
exit
other:
work 5
atom.add r4 [32] 2
work 7
fence
exit
""",
    "skip-rotation": """
dev 1 3 4
grid 3
show 48 52
prog
mov r1 %bid
sub r2 r1 2
brz r2 setter
mul r3 r1 4
spin.cg r4 [r3+48] eq 1
out r1
exit
setter:
work 31
st [48] 1
st [52] 1
exit
""",
    "skip-not-frozen": """
dev 2 2 1
grid 3
mem 56 1
show 56 60
prog
mov r1 %bid
brz r1 a
sub r2 r1 1
brz r2 far
work 3
spin.ca r3 [60] eq 1
out r3
exit
a:
ld.ca r2 [56]
st [56] 0
atom.add r2 [56] 1
spin.ca r3 [56] eq 1
out r3
exit
far:
work 30
st [60] 1
exit
""",
    # --- sums ----------------------------------------------------------------------------------
    "sum-issues": """
dev 1 2 4
grid 2
mem 0 1
mem 5 2
mem 10 3
show 20
prog
mov r1 %bid
brnz r1 other
sum.ca r2 [0] 3
st [20] r2
out r2
exit
other:
mov r3 7
add r3 r3 1
out r3
exit
""",
    "sum-start-line": """
dev 1 1 4
grid 1
mem 3 100
mem 4 1
mem 7 2
mem 11 4
mem 12 8
show 0
prog
sum.ca r1 [6] 2
out r1
exit
""",
    "sum-stale-copy": """
dev 2 2 4
grid 2
mem 8 5
show 8
prog
mov r1 %bid
brnz r1 writer
ld.ca r2 [8]
work 6
sum.ca r3 [8] 1
sum.cg r4 [8] 1
sum.ca r5 [8] 1
out r3
out r4
out r5
exit
writer:
st [8] 9
exit
""",
    "sum-fills": """
dev 2 1 2
grid 2
mem 0 1
show 0 4
prog
mov r1 %bid
brnz r1 writer
sum.ca r2 [0] 3
work 4
ld.ca r3 [4]
ld.ca r4 [0]
out r2
out r3
out r4
exit
writer:
work 3
st [4] 7
st [0] 5
exit
""",
    "sum-cg-no-fill": """
dev 2 1 1
grid 2
mem 20 3
show 20
prog
mov r1 %bid
brnz r1 writer
ld.ca r2 [20]
work 6
sum.cg r3 [0] 4
ld.ca r4 [20]
out r3
out r4
exit
writer:
st [20] 8
st [1] 2
exit
""",
    "sum-releases-spinner": """
dev 2 2 2
grid 3
show 0
prog
mov r1 %bid
sub r2 r1 1
brz r2 setter
brnz r1 streamer
ld.ca r3 [0]
spin.ca r4 [0] eq 1
out r4
exit
setter:
work 12
st [0] 1
exit
streamer:
work 10
sum.ca r5 [40] 5
out r5
exit
""",
    "sum-cg-releases": """
dev 2 2 4
grid 3
show 20
prog
mov r1 %bid
sub r2 r1 1
brz r2 setter
brnz r1 sweeper
ld.ca r3 [20]
spin.ca r4 [20] eq 1
out r4
exit
setter:
work 10
st [20] 1
exit
sweeper:
work 12
sum.cg r5 [12] 4
out r5
exit
""",
    "sum-race-order": """
dev 3 1 4
grid 3
mem 0 1
show 4 8
prog
mov r1 %bid
sub r2 r1 1
brz r2 reducer
brz r1 early
mov r3 0
early:
mul r3 r1 2
st [r3+4] 9
exit
reducer:
mov r5 0
sum.cg r4 [0] 4
out r4
exit
""",
    "sum-trailing": """
dev 2 2 4
grid 3
mem 0 1
mem 5 2
mem 12 4
show 8
prog
mov r1 %bid
sub r2 r1 1
brz r2 writer
brnz r1 trail
sum.ca r3 [0] 4
out r3
exit
trail:
work 3
sum.ca r3 [4] 3
out r3
exit
writer:
work 9
st [8] 5
exit
""",
    "sum-evicts-prefetch": """
dev 3 2 4
grid 4
mem 12 1
show 12
prog
mov r1 %bid
sub r2 r1 2
brz r2 writer
sub r2 r1 3
brz r2 side
ld.ca r4 [12]
work 8
sum.ca r5 [0] 6
out r5
exit
side:
work 4
sum.ca r5 [400] 12
out r5
exit
writer:
work 6
st [12] 7
exit
""",
    "sum-interrupted": """
dev 1 3 4
grid 3
mem 0 1
mem 17 2
show 0
prog
mov r1 %bid
brz r1 summer
mul r2 r1 5
work r2
out r1
exit
summer:
sum.cg r3 [0] 12
out r3
exit
""",
    "sum-not-spin": """
dev 1 2 4
grid 2
mem 64 3
show 0
prog
mov r1 %bid
brnz r1 summer
spin.cg r2 [0] eq 1
out r2
exit
summer:
sum.cg r3 [64] 6
out r3
spin.cg r4 [0] eq 1
exit
""",
    # --- hangs -------------------------------------------------------------------------------
    "hang-residency": """
dev 2 2 4
grid 6
show 100
prog
atom.add r1 [100] 1
spin.cg r2 [100] ge %nb
out r1
exit
""",
    "hang-stale": """
dev 1 2 2
grid 2
show 0
prog
mov r1 %bid
brnz r1 other
ld.ca r2 [0]
spin.ca r3 [0] eq 1
out r3
exit
other:
work 6
atom.add r4 [0] 1
work 6
ld.ca r5 [8]
out r5
exit
""",
    "hang-thrash": """
dev 1 2 1
grid 2
show 64 68
prog
mov r1 %bid
mul r2 r1 4
spin.ca r3 [r2+64] eq 1
out r3
exit
""",
    "hang-after-pass": """
dev 2 2 1
grid 3
show 72 76
prog
mov r1 %bid
sub r2 r1 1
brz r2 setter
brnz r1 b
ld.ca r4 [72]
work 12
spin.ca r5 [72] eq 1
out r5
exit
b:
work 16
spin.ca r5 [76] eq 1
out r5
exit
setter:
work 10
atom.add r6 [72] 1
exit
""",
}

ORDER = list(CASES)


def prog(name):
    return [ln for ln in CASES[name].strip("\n").split("\n")]
