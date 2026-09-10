"""The enumerated programs: one per graded decision, and both sides of every fence.

Each is small enough to read and is named for the reading it separates. Where a rule has two
sides - the sliver taken and the sliver left, the growth blocked and the growth open, the flush
that stands and the flush that does not happen - both sides are here, because a verifier that
tests only the failure side is beaten by a host that turns conservative everywhere.

Nothing here carries an expected trace. `seal/gt.json` holds those, frozen from the model.
"""

CASES = {

    # --- geometry: rounding, the size a part can hold, and where a range is placed -----

    "round-up": [
        "span 2048", "part 512",
        "get a 1",
        "get b 9",
        "get c 8",
        "get d 0",
    ],

    "too-big": [
        "span 2048", "part 512",
        "get a 512",
        "get b 513",
        "get c 900",
        "get d 8",
        "fit d 600",
    ],

    "left-most": [
        "span 2048", "part 512",
        "get a 64", "get b 8", "get c 64", "get d 8", "get e 64",
        "put a", "put d", "sweep",
        "get f 8",
    ],

    "part-edge": [
        "span 2048", "part 512",
        "get a 448",
        "get b 128",
        "get c 64",
    ],

    # --- the sliver, from both sides of sixteen bytes ---------------------------------

    "sliver-take": [
        "span 2048", "part 512",
        "get a 64", "get b 64", "get c 64",
        "put b", "sweep",
        "get d 56",
    ],

    "sliver-leave": [
        "span 2048", "part 512",
        "get a 64", "get b 64", "get c 64",
        "put b", "sweep",
        "get d 48",
    ],

    "sliver-end": [
        "span 2048", "part 512",
        "get a 504",
        "get b 8",
    ],

    "sliver-aside": [
        "span 2048", "part 512",
        "get a 64", "get b 64", "get c 64",
        "put b", "sweep",
        "get d 56",
        "put d",
        "get e 64",
    ],

    # --- the aside list: what it holds back, what it hands out, and in which order -----

    "aside-plain": [
        "span 2048", "part 512",
        "get a 64", "get b 64",
        "put a",
        "get c 64",
    ],

    "aside-newest": [
        "span 2048", "part 512",
        "get a 64", "get b 64", "get c 64",
        "put a", "put c",
        "get d 64",
        "get e 64",
    ],

    "aside-blind": [
        "span 2048", "part 512",
        "get a 64", "get b 64", "get c 64",
        "put b",
        "get d 32",
    ],

    "aside-join": [
        "span 2048", "part 512",
        "get a 200", "get b 200", "get c 112",
        "put b",
        "get d 512",
        "put a",
        "get e 400",
    ],

    "keep-edge": [
        "span 2048", "part 512",
        "get a 256", "get b 256", "get c 264",
        "put a", "put b",
        "get d 512",
        "put c",
        "get e 512",
    ],

    "aside-oldest": [
        "span 4096", "part 512",
    ] + ["get p%d 64" % i for i in range(34)] + [
        "put p%d" % i for i in range(34)
    ] + [
        "get r 128",
    ],

    "aside-again": [
        "span 4096", "part 512",
    ] + ["get p%d 64" % i for i in range(34)] + [
        "put p0",
        "put p1",
        "get q 64",
    ] + ["put p%d" % i for i in range(2, 33)] + [
        "put q",
        "put p33",
        "get r 128",
    ],

    # --- the failed request, and what it leaves behind --------------------------------

    "flush-once": [
        "span 1024", "part 512",
        "get a 256", "get b 256", "get c 256", "get d 256",
        "put a", "put b",
        "get e 512",
    ],

    "flush-stays": [
        "span 1536", "part 512",
        "get a 128", "get b 128", "get c 128", "get d 128",
        "get e 512",
        "get f 512",
        "put a", "put c",
        "get g 256",
        "get h 128",
    ],

    "sweep-op": [
        "span 1024", "part 512",
        "get a 128", "get b 128", "get c 128", "get d 128",
        "put a", "put b",
        "get e 256",
        "sweep",
        "get f 256",
    ],

    # --- resize ------------------------------------------------------------------------

    "grow-open": [
        "span 1024", "part 512",
        "get a 64", "get b 64",
        "put b", "sweep",
        "fit a 128",
    ],

    "grow-blocked": [
        "span 1024", "part 512",
        "get a 64", "get b 64",
        "put b",
        "fit a 128",
    ],

    "grow-part": [
        "span 1536", "part 512",
        "get z 256",
        "get a 128",
        "fit a 512",
        "get y 128",
    ],

    "grow-sliver": [
        "span 1024", "part 512",
        "get a 64", "get b 64", "get c 64",
        "put b", "put c", "sweep",
        "fit a 184",
    ],

    "shrink-tail": [
        "span 1024", "part 512",
        "get a 256",
        "fit a 64",
        "get b 192",
    ],

    "shrink-aside": [
        "span 2048", "part 1024",
        "get a 256",
        "get b 264",
        "get c 8",
        "put b",
        "fit a 64",
        "get d 400",
    ],

    "shrink-keep": [
        "span 1024", "part 512",
        "get a 64",
        "fit a 56",
        "get b 8",
    ],

    "move-order": [
        "span 1024", "part 512",
        "get p 64",
        "get a 264",
        "get b 8",
        "put p", "sweep",
        "put b",
        "fit a 304",
    ],

    "move-fail": [
        "span 1024", "part 512",
        "get a 128", "get b 128", "get c 128", "get d 128",
        "get e 512",
        "fit a 256",
        "get f 128",
        "put a",
        "get g 128",
    ],

    # --- ids ---------------------------------------------------------------------------

    "dup-get": [
        "span 1024", "part 512",
        "get a 64",
        "get a 128",
        "get b 64",
    ],

    "dead-put": [
        "span 1024", "part 512",
        "get a 64",
        "put b",
        "put a",
        "put a",
        "get c 64",
        "get d 64",
    ],

    "dead-fit": [
        "span 1024", "part 512",
        "get a 64",
        "put a",
        "fit a 128",
        "get b 64",
    ],
}

ORDER = sorted(CASES)


def ops(name):
    return list(CASES[name])
