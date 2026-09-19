"""The enumerated plans: one per graded decision, plus the must-still-work side of each fence.

Each plan is small enough to work through by hand, and each is named for the decision it pins.
No expected output lives here - the frozen traces are in the sealed directory, which the
process that runs submitted code cannot read.

The corpora are written so that a property holds whatever order a source hands its samples in.
A source of two samples with one over the cap, for instance, hands them over as either
`ok, over` or `over, ok`, and a plan long enough to see several of its epochs sees both, so the
lazily passed-over tail and the tail crossed on arrival are both covered without the plan
having to pick a permutation.
"""

CAP = 100
IN = (40, 60, 90, 75, 55, 80, 35, 65)
OVER = (150, 210, 320, 175)


def src(name, hold, vals):
    return "src %s %d %s" % (name, hold, ",".join(str(v) for v in vals))


def head(seed, srcs, pat):
    return ["seed %d" % seed, "cap %d" % CAP] + srcs + ["mix " + " ".join(pat)]


def clean(n):
    return IN[:n]


def hot(n, over):
    vals = list(IN[:n])
    for i in range(over):
        vals[(i * 2) % n] = OVER[i % len(OVER)]
    return vals


PLANS = {}


def plan(name, lines):
    PLANS[name] = lines


# --- the deal, from both axes -------------------------------------------------------

plan("deal-ranks", head(11, [src("a", 0, clean(5)), src("b", 0, clean(4))], ["a", "b"]) + [
    "open r 4 1 1", "take r 1",
    "show r 0 0 0", "show r 0 1 0", "show r 0 2 0", "show r 0 3 0",
])


plan("deal-seats", head(12, [src("a", 0, clean(5)), src("b", 0, clean(4))], ["a", "b", "a"]) + [
    "open r 1 2 3", "take r 1",
    "show r 0 0 0", "show r 0 0 1", "show r 0 0 2",
])


plan("deal-both", head(13, [src("a", 0, clean(6)), src("b", 0, clean(5))], ["a", "b"]) + [
    "open r 2 2 2", "take r 1",
    "show r 0 0 0", "show r 0 0 1", "show r 0 1 0", "show r 0 1 1",
])


plan("deal-wide-geometry",
     head(14, [src("a", 0, clean(7)), src("b", 0, clean(6)), src("c", 0, clean(5))],
            ["a", "b", "c", "a"]) + [
    "open r 8 4 8", "take r 2",
    "show r 0 5 2", "show r 1 0 0", "show r 1 7 7",
])


plan("deal-steps-follow",
     head(15, [src("a", 0, clean(4)), src("b", 0, clean(3))], ["a", "b", "b"]) + [
    "open r 2 1 2", "take r 4",
    "show r 0 0 0", "show r 1 1 1", "show r 2 0 1", "show r 3 1 0",
])


# --- the cap and the refill --------------------------------------------------------

plan("cap-none-over", head(21, [src("a", 0, clean(3)), src("b", 0, clean(3))], ["a", "b"]) + [
    "open r 1 1 1", "take r 8",
    "show r 0 0 0", "show r 3 0 0", "show r 7 0 0",
    "feed r 1", "save r k0",
])


plan("cap-pass-by", head(22, [src("a", 0, hot(4, 1)), src("b", 0, clean(3))], ["a", "b"]) + [
    "open r 1 1 1", "take r 10",
    "show r 1 0 0", "show r 5 0 0", "show r 9 0 0",
    "feed r 2", "save r k0",
])


plan("cap-pass-by-two",
     head(23, [src("a", 0, hot(5, 2)), src("b", 0, clean(3))], ["a", "b", "a"]) + [
    "open r 1 1 2", "take r 6",
    "show r 0 0 0", "show r 2 0 1", "show r 5 0 0",
    "save r k0",
])


plan("cap-all-but-one", head(24, [src("a", 0, (40, 150, 210, 320)), src("b", 0, clean(3))],
            ["a", "b"]) + [
    "open r 1 1 1", "take r 7",
    "show r 0 0 0", "show r 4 0 0", "show r 6 0 0",
    "feed r 1", "save r k0",
])


plan("cap-exactly-at-cap", head(26, [src("a", 0, (CAP, CAP + 1, 40)), src("b", 0, (CAP, 60))],
            ["a", "b"]) + [
    "open r 1 1 1", "take r 8",
    "show r 0 0 0", "show r 1 0 0", "show r 4 0 0", "show r 7 0 0",
    "feed r 1", "save r k0",
])


plan("cap-same-source-again",
     head(25, [src("a", 0, (150, 40, 210, 60)), src("b", 0, (90,))], ["a", "b"]) + [
    "open r 1 1 1", "take r 6",
    "show r 0 0 0", "show r 1 0 0", "show r 2 0 0", "show r 5 0 0",
])


# --- epochs -----------------------------------------------------------------------

plan("epoch-wrap", head(31, [src("a", 0, clean(3)), src("b", 0, clean(2))], ["a", "b"]) + [
    "open r 1 1 1", "take r 12",
    "show r 0 0 0", "show r 6 0 0", "show r 11 0 0",
    "save r k0",
])


plan("epoch-fresh-order", head(32, [src("a", 0, clean(4))], ["a"]) + [
    "open r 1 1 1", "take r 12",
    "show r 0 0 0", "show r 3 0 0", "show r 4 0 0", "show r 7 0 0", "show r 8 0 0",
])


plan("epoch-cursor-rolls", head(33, [src("a", 0, clean(2)), src("b", 0, clean(2))], ["a", "b"]) + [
    "open r 1 1 1", "take r 2", "save r k0",
    "take r 2", "save r k1",
    "take r 2", "save r k2",
    "take r 2", "save r k3",
])


plan("epoch-tail-over-cap",
     head(34, [src("a", 0, (40, 150)), src("b", 0, clean(2))], ["a", "b"]) + [
    "open r 1 1 1", "take r 1", "save r k0",
    "take r 1", "save r k1",
    "take r 1", "save r k2",
    "take r 1", "save r k3",
    "take r 1", "save r k4",
])


plan("epoch-own-counter", head(35, [src("a", 0, clean(2)), src("b", 0, clean(5))], ["a", "b"]) + [
    "open r 1 1 1", "take r 9", "save r k0",
    "show r 8 0 0", "show r 2 0 0",
])


# --- allowances and retirement ----------------------------------------------------

plan("hold-zero-runs-on", head(41, [src("a", 0, clean(2)), src("b", 0, clean(3))], ["a", "b"]) + [
    "open r 1 1 1", "take r 14",
    "show r 12 0 0", "show r 13 0 0",
    "save r k0",
])


plan("hold-one-epoch", head(42, [src("a", 1, clean(3)), src("b", 0, clean(2))], ["a", "b"]) + [
    "open r 1 1 1", "take r 3", "save r k0",
    "take r 2", "save r k1",
    "take r 3", "save r k2",
    "show r 5 0 0", "show r 7 0 0",
])


plan("hold-two-epochs",
     head(43, [src("a", 2, clean(3)), src("b", 0, clean(4))], ["a", "b", "b"]) + [
    "open r 1 1 1", "take r 9", "save r k0",
    "take r 9", "save r k1",
    "show r 5 0 0", "show r 14 0 0", "show r 17 0 0",
])


plan("hold-last-delivery",
     head(44, [src("a", 1, (40, 150)), src("b", 0, clean(3))], ["a", "b"]) + [
    "open r 1 1 1", "take r 1", "save r k0",
    "take r 1", "save r k1",
    "take r 1", "save r k2",
    "take r 1", "save r k3",
    "show r 0 0 0", "show r 2 0 0", "show r 3 0 0",
])


plan("hold-counts-deliveries",
     head(45, [src("a", 2, hot(4, 2)), src("b", 0, clean(3))], ["a", "b"]) + [
    "open r 1 1 1", "take r 4", "save r k0",
    "take r 4", "save r k1",
    "take r 4", "save r k2",
    "show r 3 0 0", "show r 7 0 0", "show r 11 0 0",
])


plan("hold-gone-in-record",
     head(46, [src("a", 1, clean(2)), src("b", 0, clean(3))], ["a", "b"]) + [
    "open r 1 1 1", "take r 3", "save r k0",
    "take r 4", "save r k1",
])


# --- the mix after a retirement ---------------------------------------------------

plan("mix-entries-leave",
     head(51, [src("a", 1, clean(2)), src("b", 0, clean(3)), src("c", 0, clean(3))],
            ["a", "b", "c"]) + [
    "open r 1 1 1", "take r 12",
    "show r 3 0 0", "show r 5 0 0", "show r 6 0 0", "show r 7 0 0", "show r 11 0 0",
    "save r k0",
])


plan("mix-offset-from-stretch",
     head(52, [src("a", 1, clean(2)), src("b", 0, clean(4)), src("c", 0, clean(4))],
            ["a", "b", "c", "b"]) + [
    "open r 1 1 1", "take r 14",
    "show r 4 0 0", "show r 5 0 0", "show r 6 0 0", "show r 7 0 0",
    "show r 8 0 0", "show r 13 0 0", "save r k0",
])


plan("mix-named-twice", head(53, [src("a", 1, clean(3)), src("b", 0, clean(4))],
            ["a", "b", "a", "b", "b"]) + [
    "open r 1 1 1", "take r 16",
    "show r 5 0 0", "show r 6 0 0", "show r 7 0 0", "show r 15 0 0",
    "save r k0",
])


plan("mix-two-retire",
     head(54, [src("a", 1, clean(2)), src("b", 2, clean(2)), src("c", 0, clean(3))],
            ["a", "b", "c", "b"]) + [
    "open r 1 1 1", "take r 18",
    "show r 3 0 0", "show r 7 0 0", "show r 9 0 0", "show r 13 0 0", "show r 17 0 0",
    "save r k0",
])


plan("mix-retire-inside-step",
     head(56, [src("a", 1, clean(2)), src("b", 0, clean(3)), src("c", 0, clean(3))],
            ["a", "b", "c", "a"]) + [
    "open r 1 8 1", "take r 2",
    "show r 0 0 0", "show r 1 0 0",
    "save r k0",
])


plan("mix-survivors-keep-order",
     head(55, [src("a", 0, clean(3)), src("b", 1, clean(2)), src("c", 0, clean(3))],
            ["c", "b", "a"]) + [
    "open r 1 1 1", "take r 12",
    "show r 5 0 0", "show r 6 0 0", "show r 7 0 0", "show r 8 0 0", "show r 11 0 0",
    "save r k0",
])


# --- the record, and what a load rewinds to ---------------------------------------

plan("state-before-the-slot",
     head(61, [src("a", 0, clean(3)), src("b", 0, clean(3))], ["a", "b"]) + [
    "open r 1 1 1", "take r 1", "save r k0",
    "take r 1", "save r k1",
    "take r 1", "save r k2",
])


plan("keep-rewind-to-done",
     head(62, [src("a", 0, clean(4)), src("b", 0, clean(3))], ["a", "b", "a"]) + [
    "open r 2 1 2", "take r 3", "feed r 5", "save r k0",
    "load q k0 2 1 2", "take q 2", "show q 0 0 0", "show q 1 1 1",
])


plan("keep-nothing-to-rewind",
     head(63, [src("a", 0, clean(4)), src("b", 0, clean(3))], ["a", "b", "a"]) + [
    "open r 2 1 2", "take r 3", "save r k0",
    "load q k0 2 1 2", "take q 2", "show q 0 0 0", "show q 1 1 1",
])


plan("keep-record-geometry",
     head(64, [src("a", 0, clean(5)), src("b", 0, clean(4))], ["a", "b"]) + [
    "open r 4 2 2", "take r 3", "feed r 2", "save r k0",
    "load q k0 1 1 1", "take q 4",
    "show q 0 0 0", "show q 3 0 0",
])


plan("keep-chain-base",
     head(65, [src("a", 0, clean(5)), src("b", 0, clean(4))], ["a", "b", "b"]) + [
    "open r 2 1 1", "take r 4", "feed r 2", "save r k0",
    "load q k0 1 1 2", "take q 3", "feed q 3", "save q k1",
    "load p k1 2 2 1", "take p 2", "show p 0 0 0", "show p 1 1 0",
])


plan("keep-chain-three-deep",
     head(66, [src("a", 0, clean(3)), src("b", 0, clean(5))], ["a", "b"]) + [
    "open r 1 1 2", "take r 3", "feed r 1", "save r k0",
    "load q k0 1 1 1", "take q 2", "save q k1",
    "load p k1 1 1 1", "take p 2", "feed p 2", "save p k2",
    "load s k2 1 1 1", "take s 2", "show s 0 0 0", "show s 1 0 0",
])


plan("edge-rewind-on-retire",
     head(67, [src("a", 1, clean(2)), src("b", 0, clean(3)), src("c", 0, clean(3))],
            ["a", "b", "c"]) + [
    "open r 1 1 1", "take r 4", "feed r 4", "save r k0",
    "load q k0 1 1 1", "take q 4",
    "show q 0 0 0", "show q 1 0 0", "show q 3 0 0",
])


plan("edge-save-past-retire",
     head(68, [src("a", 2, clean(2)), src("b", 0, clean(3)), src("c", 0, clean(4))],
            ["a", "b", "a", "c"]) + [
    "open r 1 1 1", "take r 5", "feed r 6", "save r k0",
    "load q k0 1 1 2", "take q 3", "show q 0 0 0", "show q 2 0 1",
])


plan("edge-rewind-over-retire",
     head(69, [src("a", 1, hot(4, 1)), src("b", 0, clean(3)), src("c", 0, clean(3))],
            ["a", "b", "c", "a"]) + [
    "open r 1 1 2", "take r 3", "feed r 4", "save r k0",
    "load q k0 2 1 1", "take q 4",
    "show q 0 0 0", "show q 1 1 0", "show q 3 0 0",
])


ORDER = tuple(sorted(PLANS))


def ops(name):
    return list(PLANS[name])
