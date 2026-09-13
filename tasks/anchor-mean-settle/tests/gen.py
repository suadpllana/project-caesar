"""The generated population, drawn from a seed the submission never saw.

Ten small families and two wide ones. The small families are shaped, not uniform: an
unshaped stream of ops leaves the assumed height almost constant, and a reading that gets
the assumed height wrong then moves almost nothing. Each family concentrates one shape
where the rules argue with each other - a mean that jumps on the first measurement, a mean
that falls, a clamp that bites in the middle of a pass, edits ahead of the anchor, the
anchor itself leaving, a re-text that takes a sample out of the mean, a width change that
takes all of them.

The two wide families are the execution limit. `wide` imports 120000 rows and rolls and
passes across them 6000 times, which keeps reaching rows nobody has measured yet; `deep`
imports 150000, measures the band at the far end, and then edits at the front 9000 times,
each of which moves a row the view is held against the whole length of the list away. Two of
each is enough: one of them alone puts a panel that reads a prefix by walking the row list
past the limit for the whole set.
"""
import random

FAMILIES = (
    ("plain", False),
    ("mixed", False),
    ("grow", False),
    ("shrink", False),
    ("edge", False),
    ("front", False),
    ("anchor", False),
    ("retext", False),
    ("width", False),
    ("empty", False),
    ("wide", True),
    ("deep", True),
)

BIG = 2
SHORT = (20, 30, 34, 38)
TALL = (190, 300, 460, 700)


def _ask(rng):
    return rng.choice(["top", "tall", "face"])


def plain(rng):
    n = rng.randrange(14, 60)
    out = ["bulk %d %d %d" % (n, rng.choice(SHORT), rng.choice([1, 4, 8]))]
    for _ in range(rng.randrange(12, 28)):
        k = rng.randrange(6)
        if k < 2:
            out.append("roll %d" % rng.choice([-700, -240, -13, 24, 96, 300, 1200]))
        elif k < 4:
            out.append("pass")
        else:
            out.append(_ask(rng))
    return out


def mixed(rng):
    n = rng.randrange(10, 40)
    out = ["bulk %d %d %d" % (n, rng.choice(SHORT), rng.choice([1, 4]))]
    for i in range(rng.randrange(2, 6)):
        out.append("ins %d t%d %d" % (rng.randrange(n), i, rng.choice(TALL)))
    for _ in range(rng.randrange(14, 30)):
        k = rng.randrange(7)
        if k < 2:
            out.append("roll %d" % rng.choice([-900, -120, 60, 240, 600, 3000]))
        elif k < 5:
            out.append("pass")
        else:
            out.append(_ask(rng))
    return out


def grow(rng):
    """A pass whose first measurement lifts the assumed height and empties the view."""
    n = rng.randrange(18, 50)
    out = ["bulk %d %d 4" % (n, rng.choice(SHORT))]
    seat = rng.randrange(4, n - 4)
    out.append("ins %d big %d" % (seat, rng.choice(TALL)))
    out.append("roll %d" % (24 * max(0, seat - rng.randrange(1, 4))))
    for _ in range(rng.randrange(3, 8)):
        out.append("pass")
        out.append(_ask(rng))
    return out


def shrink(rng):
    """A pass whose first measurement drops the assumed height and fills the view."""
    n = rng.randrange(10, 24)
    out = ["bulk %d %d 4" % (n, rng.choice(TALL))]
    out.append("bulk %d %d 4" % (rng.randrange(14, 40), rng.choice(SHORT), ))
    out.append("roll %d" % rng.choice([0, 200, 900, 2400]))
    for _ in range(rng.randrange(3, 9)):
        out.append("pass")
        out.append(_ask(rng))
    return out


def edge(rng):
    """Scrolled hard against either end, where a re-seat loses part of its correction."""
    n = rng.randrange(12, 34)
    out = ["bulk %d %d 4" % (n, rng.choice(SHORT))]
    out.append("ins %d big %d" % (n - rng.randrange(1, 4), rng.choice(TALL)))
    out.append("roll %d" % rng.choice([9000, 40000, -9000]))
    for _ in range(rng.randrange(4, 10)):
        k = rng.randrange(5)
        if k < 2:
            out.append("pass")
        elif k == 2:
            out.append("roll %d" % rng.choice([-40, -6, 6, 40, 9000]))
        else:
            out.append(_ask(rng))
    return out


def front(rng):
    """Edits ahead of the anchor while the view stands still."""
    n = rng.randrange(20, 50)
    out = ["bulk %d %d 4" % (n, rng.choice(SHORT)), "roll %d" % rng.choice([240, 480, 700])]
    out.append("pass")
    made = 0
    for _ in range(rng.randrange(14, 30)):
        k = rng.randrange(8)
        if k < 3:
            made += 1
            out.append("ins %d f%d %d" % (rng.randrange(3), made,
                                          rng.choice(SHORT + TALL)))
        elif k < 5 and made:
            out.append("del f%d" % rng.randrange(1, made + 1))
        elif k == 5:
            out.append("pass")
        else:
            out.append(_ask(rng))
    return out


def anchor(rng):
    """The held row itself leaving, moving or being re-texted.

    Every row here is short, so while nothing tall has been measured the assumed height
    stays put and the row the view is held against is the one at index `j`. The family
    names that row rather than a random one, which is the only way a delete or a move of
    the anchor happens often enough to separate the rules that govern it.
    """
    n = rng.randrange(16, 44)
    j = rng.randrange(3, 10)
    order = ["k%d" % (i + 1) for i in range(n)]
    out = ["bulk %d %d 4" % (n, rng.choice(SHORT)), "roll %d" % (24 * j), "pass"]
    made = 0
    for _ in range(rng.randrange(12, 26)):
        k = rng.randrange(9)
        at = min(j, len(order) - 1)
        if not order:
            made += 1
            order.append("g%d" % made)
            out.append("ins 0 g%d %d" % (made, rng.choice(SHORT)))
            continue
        if k < 2:
            out.append("del %s" % order.pop(at))
        elif k < 4:
            to = rng.randrange(max(1, min(4, len(order))))
            rid = order.pop(at)
            order.insert(to, rid)
            out.append("move %s %d" % (rid, to))
        elif k == 4:
            out.append("set %s %d" % (order[at], rng.choice(SHORT + TALL)))
        elif k == 5:
            made += 1
            rid = "g%d" % made
            to = rng.randrange(max(1, at))
            order.insert(to, rid)
            out.append("ins %d %s %d" % (to, rid, rng.choice(SHORT + TALL)))
        elif k == 6:
            out.append("pass")
        else:
            out.append(_ask(rng))
    out += ["top", "tall", "face"]
    return out


def retext(rng):
    """Samples leaving the mean one at a time."""
    n = rng.randrange(12, 30)
    out = ["bulk %d %d 4" % (n, rng.choice(SHORT))]
    out.append("ins 0 big %d" % rng.choice(TALL))
    out += ["pass", "roll %d" % rng.choice([0, 120, 400]), "pass"]
    for _ in range(rng.randrange(10, 22)):
        k = rng.randrange(6)
        if k < 3:
            out.append("set k%d %d" % (rng.randrange(1, n + 1), rng.choice(SHORT + TALL)))
        elif k == 3:
            out.append("set big %d" % rng.choice(SHORT + TALL))
        elif k == 4:
            out.append("pass")
        else:
            out.append(_ask(rng))
    return out


def width(rng):
    """Every measurement given up at once, more than once."""
    n = rng.randrange(12, 32)
    out = ["bulk %d %d 4" % (n, rng.choice([60, 130, 190]))]
    out += ["roll %d" % rng.choice([0, 200, 600]), "pass"]
    for _ in range(rng.randrange(10, 20)):
        k = rng.randrange(6)
        if k < 2:
            out.append("span %d" % rng.choice([7, 12, 20, 40, 90, 200]))
        elif k < 4:
            out.append("pass")
        else:
            out.append(_ask(rng))
    return out


def empty(rng):
    """Lists that run out of rows and come back."""
    out = ["bulk %d %d 4" % (rng.randrange(2, 8), rng.choice(SHORT))]
    live = ["k%d" % (i + 1) for i in range(int(out[0].split()[1]))]
    made = 0
    for _ in range(rng.randrange(14, 30)):
        k = rng.randrange(8)
        if k < 3 and live:
            out.append("del %s" % live.pop(rng.randrange(len(live))))
        elif k < 5:
            made += 1
            rid = "e%d" % made
            at = rng.randrange(len(live) + 1)
            live.insert(at, rid)
            out.append("ins %d %s %d" % (at, rid, rng.choice(SHORT + TALL)))
        elif k == 5:
            out.append("pass")
        elif k == 6:
            out.append("roll %d" % rng.choice([-90, 30, 400]))
        else:
            out.append(_ask(rng))
    out += ["top", "tall", "face"]
    return out


def wide(rng):
    n = 120000
    out = ["bulk %d 30 170" % n]
    for i in range(6000):
        k = i % 10
        if k in (0, 3, 6):
            out.append("roll %d" % rng.choice([-4000, -900, 700, 1500, 9000, 40000]))
        elif k in (1, 4, 7):
            out.append("pass")
        elif k == 2:
            out.append("top")
        elif k == 5:
            out.append("tall")
        elif k == 8:
            out.append("face")
        else:
            out.append("set k%d %d" % (rng.randrange(1, n + 1), rng.choice([20, 300])))
    out += ["top", "tall", "face"]
    return out


def deep(rng):
    n = 150000
    out = ["bulk %d 40 90" % n]
    for _ in range(30):
        out += ["roll 5000000", "roll -700", "pass"]
    for i in range(9000):
        k = i % 8
        if k == 0:
            out.append("ins %d y%d %d" % (rng.randrange(4), i, rng.choice([10, 400])))
        elif k == 1:
            out.append("del y%d" % (i - 1))
        elif k in (2, 5):
            out.append("pass")
        elif k == 3:
            out.append("move k%d %d" % (rng.randrange(1, n + 1), rng.randrange(3)))
        elif k == 4:
            out.append("top")
        elif k == 6:
            out.append("tall")
        else:
            out.append("face")
    out += ["top", "tall", "face"]
    return out


SHAPE = {
    "plain": plain, "mixed": mixed, "grow": grow, "shrink": shrink, "edge": edge,
    "front": front, "anchor": anchor, "retext": retext, "width": width, "empty": empty,
    "wide": wide, "deep": deep,
}


def programs(seed, per):
    out = []
    for fam, big in FAMILIES:
        many = BIG if big else per
        for i in range(many):
            rng = random.Random("%s/%s/%d" % (seed, fam, i))
            out.append((fam, "%s-%d" % (fam, i), SHAPE[fam](rng)))
    return out
