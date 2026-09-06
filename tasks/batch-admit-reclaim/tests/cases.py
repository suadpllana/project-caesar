"""The enumerated half of the graded set.

Each name says which reading of the rules the trace exists to fail, or which
ordinary behaviour it exists to protect. Nothing here was written by hand: the
separators were searched for in a large generated pool and then shrunk while the
separation survived, and the corner traces were searched the same way against the
property each one names. The three traces that ship in the tree are included
verbatim, so a submission that only ever tried those is graded on them too.

Knowing which traces run gives away none of their timelines. The answers live in
gt.json, which is root-only, and three hundred further traces are built from a
nonce drawn after the agent has stopped.
"""

TRACES = {
    "the-pool-is-asked-how-much-it-has-not-played-out": """\
pool 9
block 3
batch 12
req r2 6
req r3 1
req r4 8
prompt r2 2 2
emit r2 0 0 2 0 3 0 0
prompt r3 2 0 0
emit r3 0 1 1 3 2 0 3 3 1 3 2 2
prompt r4 2 2
emit r4 1 0 3
""",
    "the-block-a-filling-tail-gives-back-is-missed": """\
pool 7
block 3
batch 12
req r2 3
req r3 3
req r4 4
prompt r2 1 2 0 0 0 2 0 1
emit r2 1
prompt r3 1 2 0 0 0 2 0 1 1 1 2 2 1
emit r3 1
prompt r4 1 0 1 1
emit r4 0
""",
    "what-this-step-finishes-is-counted-as-room": """\
pool 7
block 5
batch 10
req r0 0
req r1 0
req r3 3
prompt r0 0 0 4 4 1
emit r0 2 4 3
prompt r1 2
emit r1 2 1 0 0
prompt r3 0 0 4 4 1 0 4 2 1
emit r3 1
""",
    "the-newcomer-s-part-block-is-forgotten": """\
pool 9
block 3
batch 12
req r1 8
req r2 6
req r3 1
req r4 8
prompt r1 3 2 1 0
emit r1 1
prompt r2 2 2 2 0 2
emit r2 0 0 2
prompt r3 2 0 0
emit r3 0 1 1 3 2 0 3 3
prompt r4 2
emit r4 1
""",
    "only-the-newcomer-is-asked-about": """\
pool 9
block 3
batch 12
req r2 6
req r3 1
req r4 8
prompt r2 2 2
emit r2 0 0 2 0 3 0 0
prompt r3 2 0 0
emit r3 0 1 1 3 2 0 3 3 1 3 2
prompt r4 2 2
emit r4 1 0 3
""",
    "the-pool-gives-up-what-came-free-last": """\
pool 7
block 3
batch 10
req r1 7
req r3 1
req r4 7
prompt r1 0
emit r1 0 1 0 1 1 0
prompt r3 0 1 1
emit r3 0
prompt r4 0 1 1 0 1 1 0 1 1 0 1
emit r4 0 1 1 1 0
""",
    "the-pool-gives-up-the-oldest-block-it-made": """\
pool 11
block 3
batch 16
req r0 0
req r1 1
req r3 7
req r4 5
prompt r0 4 0 0 4 0 1 3 3 4 2 2 4
emit r0 3 1 0 4 0 0 2
prompt r1 4 3 4 1 2 3
emit r1 1 0 1 3 2 1
prompt r3 3 4 0
emit r3 3
prompt r4 4 0 0
emit r4 4 0
""",
    "a-request-keeps-the-blocks-it-had": """\
pool 13
block 3
batch 20
req r3 5
req r4 3
prompt r3 0 0 1
emit r3 0
prompt r4 0 0
emit r4 1
""",
    "a-hole-in-the-middle-is-stepped-over": """\
pool 7
block 3
batch 10
req r1 7
req r3 1
req r4 7
prompt r1 0
emit r1 0 1 0 1 1 0
prompt r3 0 1 1
emit r3 0
prompt r4 0 1 1 0 1 1 0 1 1 0 1
emit r4 0 1 1 1 0
""",
    "a-request-starts-over-from-nothing": """\
pool 13
block 3
batch 20
req r3 5
req r4 3
prompt r3 0 0 1
emit r3 0
prompt r4 0 0
emit r4 1
""",
    "only-a-first-time-request-shares-what-is-there": """\
pool 9
block 3
batch 12
req r1 8
req r2 6
req r3 1
prompt r1 3 2 1 0 0 0
emit r1 1
prompt r2 2 2 2 0
emit r2 0 0 2
prompt r3 2 0
emit r3 0 1 1 3 2 0 3 3
""",
    "the-first-to-arrive-is-put-out": """\
pool 9
block 3
batch 12
req r1 8
req r2 6
req r3 1
req r4 8
prompt r1 3
emit r1 1
prompt r2 2 2 2 0
emit r2 0 0 2
prompt r3 2 0
emit r3 0 1 1 3 2 0 3 3
prompt r4 2 2 1
emit r4 1
""",
    "the-shortest-waiting-request-goes-first": """\
pool 7
block 4
batch 13
req r0 0
req r2 0
req r4 1
prompt r0 0
emit r0 0
prompt r2 0 1 0 1 0 1 1 0 0 0 1 0 0
emit r2 1
prompt r4 0
emit r4 0
""",
    "nothing-is-ever-put-out": """\
pool 7
block 3
batch 10
req r1 5
req r2 3
req r3 6
req r4 6
prompt r1 1
emit r1 2
prompt r2 2
emit r2 1
prompt r3 2
emit r3 1
prompt r4 2
emit r4 2
""",
    "two-newcomers-take-what-is-already-there": """\
pool 12
block 3
batch 15
req r0 0
req r1 5
req r2 9
req r3 0
prompt r0 0 1 1
emit r0 3
prompt r1 2 3 3
emit r1 2
prompt r2 0 1 1
emit r2 3
prompt r3 2 3 3
emit r3 2
""",
    "three-requests-are-put-out": """\
pool 7
block 3
batch 12
req r2 4
req r3 1
req r4 1
prompt r2 1 3 0 2 1 2 1 2
emit r2 0 2 0 1
prompt r3 1 0 3 3 1
emit r3 1 2 2 3 0
prompt r4 1 3 0
emit r4 2 1 2 3 1
""",
    "a-request-comes-back-part-way-through": """\
pool 9
block 3
batch 11
req r1 4
req r2 9
req r3 2
req r4 9
prompt r1 2
emit r1 1 1 0 0 2 0
prompt r2 1 1 1
emit r2 1
prompt r3 0 1 2
emit r3 1 2 1 2 0 2 1 0
prompt r4 0 1 2
emit r4 1
""",
    "a-request-comes-back-with-nothing-kept": """\
pool 7
block 3
batch 8
req r0 0
req r1 5
req r2 2
req r4 4
prompt r0 0
emit r0 4 2 2 1 2
prompt r1 1 0 2 1 2 2 0 3 1 3 3 4
emit r1 3
prompt r2 4 1 2 2
emit r2 0 0 1
prompt r4 4 1 3 2 2 4
emit r4 0
""",
    "one-finishes-on-the-step-another-comes-in": """\
pool 7
block 3
batch 10
req r1 5
req r4 6
prompt r1 1
emit r1 2
prompt r4 2
emit r4 2
""",
    "a-request-is-put-out-on-the-step-it-would-have-finished": """\
pool 7
block 3
batch 8
req r0 0
req r2 2
req r4 4
prompt r0 0
emit r0 4 2 2 1 2
prompt r2 4 1 2 2
emit r2 0 0 1
prompt r4 4 1 3 2 2 4
emit r4 0
""",
    "a-request-is-put-out-twice": """\
pool 9
block 3
batch 17
req r0 0
req r1 0
req r3 4
prompt r0 0 0 1
emit r0 0 1 0 1 1 0 0
prompt r1 0 0 0 0 0
emit r1 1 0 1 1 0 0 1
prompt r3 0 0 0 0 0 1 1 0 1 1 0 0
emit r3 1
""",
    "one-request-on-its-own": """\
pool 9
block 3
batch 10
req r0 0
prompt r0 1 2 0 1 2
emit r0 0 1 2 0
""",
    "a-request-larger-than-a-whole-step-comes-in-on-its-own": """\
pool 9
block 3
batch 4
req r0 0
prompt r0 1 2 0 1 2 0 1 2 0 1
emit r0 2 0 1
req r1 0
prompt r1 2 2 2
emit r1 1 1
""",
    "two-requests-fill-the-same-block-on-the-same-step": """\
pool 8
block 3
batch 12
req r0 0
prompt r0 1 2 0 1
emit r0 2 0 1 2 0
req r1 0
prompt r1 1 2 0 1
emit r1 2 0 1 2 0
""",
    "a-prompt-that-ends-on-a-block-edge": """\
pool 8
block 3
batch 12
req r0 0
prompt r0 1 2 0 1 2 0
emit r0 1 1 1
req r1 1
prompt r1 1 2 0 1 2 0
emit r1 2 2
""",
    "a-prompt-shorter-than-one-block": """\
pool 7
block 4
batch 10
req r0 0
prompt r0 3
emit r0 1 2 3 1 2
req r1 0
prompt r1 3 1
emit r1 2 3 1 2 0
""",
    "shipped-steady": """\
pool 12
block 4
batch 16
req r0 0
req r1 2
req r2 5
prompt r0 2 1 3 0 2 1 3
emit r0 0 2 1 3 0
prompt r1 2 1 3 0 1 1
emit r1 3 0 2
prompt r2 0 0 1 2
emit r2 3 3 1 0 2
""",
    "shipped-twin": """\
pool 8
block 3
batch 12
req r0 0
req r1 0
req r2 4
prompt r0 1 2 0 1 2 0
emit r0 1 0 2 1 0
prompt r1 1 2 0 1 2 0
emit r1 2 1 0
prompt r2 3 3 1 2
emit r2 0 1 3
""",
    "shipped-press": """\
pool 7
block 3
batch 10
req r0 0
req r1 1
req r2 2
req r3 3
prompt r0 1 1 2 0 1 1 2 0
emit r0 1 2 0 1 1
prompt r1 1 1 2 0 2 2
emit r1 0 1 2 0
prompt r2 2 0 1 1 2
emit r2 1 1 0 2 1
prompt r3 1 1 2 0 1 1 2 0 2
emit r3 1 0
""",
}
