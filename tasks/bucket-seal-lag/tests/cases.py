"""The enumerated plans, one per rule, each named for the reading it exists to fail.

The run may read this file. Knowing which plans execute produces none of their
traces, and it is the generated set behind them that carries the weight anyway:
those plans are built from a nonce made after the submission was written.

Every fence has both halves here. Where a plan exists to catch something sealed
too early there is another where the same shape must still seal on time, because
a reading that never seals anything passes the first kind and fails nothing.
"""

PLANS = {}


def add(name, text):
    PLANS[name] = text.strip("\n") + "\n"


add("near-source", """
hz 60
node s0 src
node g0 gather 10
node k0 sink
wire s0 g0 1
wire g0 k0 0
put 1 s0 4
put 2 s0 21
low 3 s0 20
put 5 s0 25
low 6 s0 40
shut 8 s0
""")

add("two-hop", """
hz 60
node s0 src
node r0 relay
node g0 gather 10
node k0 sink
wire s0 r0 0
wire r0 g0 1
wire g0 k0 0
put 1 s0 4
put 2 s0 21
low 3 s0 20
put 5 s0 25
low 6 s0 40
shut 8 s0
""")

add("three-hop", """
hz 70
node s0 src
node r0 relay
node r1 relay
node g0 gather 10
node k0 sink
wire s0 r0 0
wire r0 r1 2
wire r1 g0 1
wire g0 k0 0
put 1 s0 6
put 3 s0 17
low 4 s0 12
low 9 s0 34
low 14 s0 48
shut 18 s0
""")

add("lift-on-route", """
hz 70
node s0 src
node f0 lift 30
node g0 gather 10
node k0 sink
wire s0 f0 0
wire f0 g0 0
wire g0 k0 0
put 1 s0 5
put 2 s0 34
low 6 s0 20
low 11 s0 45
shut 14 s0
""")

add("lift-holds", """
hz 70
node s0 src
node r0 relay
node f0 lift 40
node g0 gather 10
node k0 sink
wire s0 r0 0
wire r0 f0 0
wire r0 g0 3
wire f0 g0 0
put 1 s0 8
put 2 s0 12
low 5 s0 44
shut 7 s0
wire g0 k0 0
""")

add("two-routes", """
hz 70
node s0 src
node r0 relay
node q0 relay
node f0 lift 30
node g0 gather 5
node k0 sink
wire s0 r0 0
wire r0 f0 0
wire r0 q0 0
wire f0 g0 0
wire q0 g0 25
wire g0 k0 0
put 1 s0 2
low 4 s0 10
low 9 s0 26
shut 13 s0
""")

add("gather-onward", """
hz 60
node s0 src
node r0 relay
node g0 gather 6
node g1 gather 10
node k0 sink
wire s0 r0 0
wire r0 g0 0
wire g0 g1 1
wire g1 k0 0
put 1 s0 3
put 2 s0 14
low 4 s0 12
low 9 s0 30
shut 12 s0
""")

add("gather-sealed-skip", """
hz 60
node s0 src
node r0 relay
node g0 gather 6
node g1 gather 8
node k0 sink
wire s0 r0 0
wire r0 g0 0
wire r0 g1 20
wire g0 g1 1
wire g1 k0 0
put 1 s0 2
low 3 s0 8
put 4 s0 9
low 7 s0 26
low 12 s0 40
shut 15 s0
""")

add("own-bucket-holds-next", """
hz 60
node s0 src
node r0 relay
node g0 gather 10
node k0 sink
wire s0 r0 0
wire r0 g0 0
wire g0 r0 4
wire g0 k0 0
put 1 s0 3
put 2 s0 12
low 4 s0 30
shut 6 s0
""")

add("bucket-high-edge", """
hz 60
node s0 src
node r0 relay
node g0 gather 10
node k0 sink
wire s0 r0 0
wire r0 g0 0
wire g0 r0 6
wire g0 k0 0
put 1 s0 1
put 2 s0 11
low 4 s0 26
shut 6 s0
""")

add("inbox-counts", """
hz 60
node s0 src
node r0 relay
node g0 gather 8
node g1 gather 8
node k0 sink
wire s0 r0 0
wire r0 g0 0
wire g0 g1 0
wire g1 k0 0
put 1 s0 2
put 1 s0 5
put 2 s0 9
low 3 s0 30
shut 4 s0
""")

add("inbox-sealed-skip", """
hz 60
node s0 src
node r0 relay
node g0 gather 6
node g1 gather 6
node k0 sink
wire s0 r0 0
wire r0 g0 0
wire g0 g1 2
wire g0 r0 7
wire g1 k0 0
put 1 s0 1
put 1 s0 3
put 2 s0 8
low 3 s0 22
shut 5 s0
""")

add("shut-releases", """
hz 50
node s0 src
node r0 relay
node g0 gather 10
node k0 sink
wire s0 r0 0
wire r0 g0 0
wire g0 k0 0
put 1 s0 3
put 2 s0 13
shut 9 s0
""")

add("loop-lap", """
hz 84
node s0 src
node r0 relay
node r1 relay
node f0 lift 20
node g0 gather 12
node k0 sink
wire s0 r0 0
wire r0 r1 0
wire r1 f0 0
wire f0 g0 0
wire g0 r0 5
wire r1 g0 9
wire g0 k0 0
put 1 s0 4
low 5 s0 22
low 10 s0 58
shut 13 s0
""")

add("arrival-not-emission", """
hz 60
node s0 src
node r0 relay
node g0 gather 12
node g1 gather 4
node k0 sink
wire s0 r0 0
wire r0 g0 0
wire g0 g1 0
wire g1 k0 0
put 1 s0 1
low 3 s0 6
low 8 s0 26
shut 11 s0
""")

add("edge-exact", """
hz 60
node s0 src
node r0 relay
node g0 gather 10
node k0 sink
wire s0 r0 0
wire r0 g0 9
wire g0 k0 0
put 1 s0 0
low 3 s0 10
low 8 s0 21
shut 11 s0
""")

add("below-comes-back", """
hz 70
node s0 src
node r0 relay
node g0 gather 6
node k0 sink
wire s0 r0 0
wire r0 g0 0
wire g0 r0 7
wire g0 k0 0
put 1 s0 2
put 2 s0 20
low 4 s0 40
shut 6 s0
""")

add("box-direct", """
hz 60
node s0 src
node r0 relay
node g0 gather 10
node k0 sink
wire s0 r0 0
wire r0 g0 0
wire r0 g0 3
wire g0 k0 0
put 1 s0 4
put 1 s0 5
low 3 s0 40
shut 4 s0
""")

add("two-seals-one-tick", """
hz 60
node s0 src
node r0 relay
node g0 gather 10
node g1 gather 10
node k0 sink
wire s0 r0 0
wire r0 g0 0
wire r0 g1 0
wire g0 k0 0
wire g1 k0 0
put 1 s0 4
low 3 s0 40
shut 4 s0
""")

add("horizon-cut", """
hz 40
node s0 src
node r0 relay
node g0 gather 8
node k0 sink
wire s0 r0 0
wire r0 g0 30
wire g0 k0 0
put 1 s0 2
low 4 s0 9
low 9 s0 12
shut 12 s0
""")

add("plain-pipe", """
hz 60
node s0 src
node r0 relay
node r1 relay
node g0 gather 10
node k0 sink
wire s0 r0 0
wire r0 r1 0
wire r1 g0 0
wire g0 k0 0
put 1 s0 5
put 2 s0 15
put 3 s0 25
low 6 s0 30
shut 9 s0
""")

add("all-drained", """
hz 50
node s0 src
node r0 relay
node g0 gather 5
node k0 sink
wire s0 r0 0
wire r0 g0 1
wire g0 k0 0
put 1 s0 0
put 1 s0 6
put 1 s0 13
shut 2 s0
""")

add("gathers-apart", """
hz 60
node s0 src
node r0 relay
node g0 gather 10
node g1 gather 10
node k0 sink
wire s0 r0 0
wire r0 g0 0
wire r0 g1 12
wire g0 k0 0
wire g1 k0 0
put 1 s0 3
low 4 s0 18
low 9 s0 33
shut 12 s0
""")

add("lift-below-all", """
hz 60
node s0 src
node f0 lift 3
node r0 relay
node g0 gather 10
node k0 sink
wire s0 f0 0
wire f0 r0 0
wire r0 g0 0
wire g0 k0 0
put 1 s0 11
put 2 s0 22
low 4 s0 20
low 8 s0 34
shut 11 s0
""")

add("two-sources", """
hz 70
node s0 src
node s1 src
node r0 relay
node f0 lift 25
node g0 gather 10
node k0 sink
wire s0 r0 0
wire s1 f0 0
wire r0 g0 0
wire f0 g0 2
wire g0 k0 0
put 1 s0 4
put 2 s1 8
low 3 s0 14
low 5 s1 20
low 8 s0 33
shut 9 s1
low 12 s0 47
shut 15 s0
""")

add("lift-holds-stale", """
hz 80
node a0 gather 10
node k0 sink
node m0 lift 40
node s0 src
wire s0 m0 0
wire s0 a0 0
wire m0 a0 0
wire a0 k0 0
put 1 s0 3
low 1 s0 30
low 5 s0 60
shut 7 s0
""")

add("inbox-onward", """
hz 60
node a0 gather 8
node b0 gather 8
node k0 sink
node r0 relay
node s0 src
wire s0 r0 0
wire r0 a0 0
wire a0 b0 0
wire b0 k0 0
put 1 s0 1
put 1 s0 2
put 1 s0 3
low 2 s0 40
shut 3 s0
""")

add("inbox-holds-downstream", """
hz 60
node aa gather 8
node k0 sink
node s0 src
node zz gather 8
wire s0 zz 0
wire s0 aa 20
wire zz aa 0
wire aa k0 0
put 1 s0 1
put 1 s0 2
put 1 s0 3
low 2 s0 40
shut 3 s0
""")


add("direct", """
hz 60
node s0 src
node g gather 10
node k sink
wire s0 g 1
wire g k 0
put 1 s0 4
put 2 s0 21
low 3 s0 20
put 5 s0 25
low 6 s0 40
shut 8 s0
""")

add("relay", """
hz 60
node s0 src
node b relay
node g gather 10
node k sink
wire s0 b 0
wire b g 1
wire g k 0
put 1 s0 4
put 2 s0 21
low 3 s0 20
put 5 s0 25
low 6 s0 40
shut 8 s0
""")

add("redrive", """
hz 70
node s0 src
node a relay
node f lift 40
node g gather 10
node k sink
wire s0 a 0
wire a f 2
wire f g 0
wire g a 3
wire g k 0
put 1 s0 12
put 2 s0 35
low 4 s0 40
shut 9 s0
""")
