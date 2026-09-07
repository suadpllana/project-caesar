"""Session generators, seeded from the run nonce.

Two families, because they test different things.

`batch` builds small sessions for correctness. Uniformly random orders barely trade, so
each session is built in two phases - resting liquidity around the mark, then a burst of
orders that actually cross it - and the burst is shaped five ways, at the five decisions
the engine turns on: disclosure, the band, the same participant, all-or-nothing
admission, and activation. A population that is not aimed at a mechanism does not
exercise it.

`deep_batch` builds the large sessions, in two shapes, because there are two ways to be
correct and unaffordable.

The parked shape is a handful of deeply sliced resting orders answering hundreds of
thousands of fills between them, against a book that stays small, with several thousand
orders parked off it. Asking every parked order on every fill is exactly right and costs
fills times parked.

The book shape is the opposite: a deep book spread over hundreds of price levels, almost
none of it reachable, and hundreds of all-or-nothing orders arriving at the touch. Taking
a copy of the state to decide each of them is exactly right and costs orders times book.

Both shapes are concentrated rather than typical, and the brief says so along with the
limit.
"""

import random

FAM = ("plain", "slice", "band", "whole", "trip")


def _seed_book(rng, lines, mark, hands, oid, deep, slicy):
    for _ in range(deep):
        oid += 1
        side = rng.choice("bs")
        off = rng.randint(1, 7)
        px = mark - off if side == "b" else mark + off
        qty = rng.choice([10, 15, 20, 25, 40, 60])
        shw = "-"
        if rng.random() < slicy:
            shw = str(rng.choice([3, 5, 6, 8, 12]))
        lines.append("new %d %d %s %d %d %s day -"
                     % (oid, rng.randint(1, hands), side, px, qty, shw))
    return oid


def one(rng, fam):
    if fam == "band":
        cap = rng.choice([1, 2, 2, 3, 4])
    elif fam == "trip":
        cap = rng.choice([4, 6, 12, 40])
    else:
        cap = rng.choice([2, 3, 4, 6, 12, 40])
    mark = rng.randint(96, 104)
    hands = rng.choice([2, 2, 3, 3, 4])
    slicy = 0.85 if fam == "slice" else 0.35
    lines = ["cap %d" % cap, "mark %d" % mark]
    oid = _seed_book(rng, lines, mark, hands, 0, rng.randint(4, 11), slicy)
    live = list(range(1, oid + 1))
    for _ in range(rng.randint(6, 20)):
        oid += 1
        roll = rng.random()
        if live and roll < 0.08:
            lines.append("pull %d" % rng.choice(live))
            continue
        if roll < 0.40 and (fam == "trip" or rng.random() < 0.10):
            side = rng.choice("bs")
            trp = mark + rng.randint(-3, 3)
            px = "-" if rng.random() < 0.35 else str(mark + rng.randint(-7, 7))
            lines.append("new %d %d %s %s %d %s %s %d"
                         % (oid, rng.randint(1, hands), side, px,
                            rng.choice([5, 10, 15, 25, 40]),
                            "-" if rng.random() < 0.7 else str(rng.choice([3, 5])),
                            rng.choice(["day", "day", "part"]), trp))
            live.append(oid)
            continue
        side = rng.choice("bs")
        hand = rng.randint(1, hands)
        if rng.random() < 0.66:
            off = rng.randint(0, 8)
            px = "-" if rng.random() < 0.18 else str(
                mark + off if side == "b" else mark - off)
        else:
            off = rng.randint(1, 7)
            px = str(mark - off if side == "b" else mark + off)
        qty = rng.choice([5, 10, 12, 18, 25, 35, 50, 70])
        shw = str(rng.choice([3, 5, 6, 8])) if rng.random() < slicy else "-"
        if fam == "whole":
            tif = rng.choice(["whole", "whole", "whole", "day", "part"])
        elif fam == "band":
            tif = rng.choice(["day", "day", "part", "whole"])
        else:
            tif = rng.choice(["day", "day", "day", "part", "whole"])
        lines.append("new %d %d %s %s %d %s %s -"
                     % (oid, hand, side, px, qty, shw, tif))
        live.append(oid)
    return "\n".join(lines) + "\n"


def batch(seed, n, fams=FAM):
    rng = random.Random("small|%s" % seed)
    return [("%s-%04d" % (fams[i % len(fams)], i), one(rng, fams[i % len(fams)]))
            for i in range(n)]


def deep_one(rng):
    mark = 1000
    cap = rng.choice([30, 40, 60])
    arms = rng.randint(6000, 9000)
    slabs = rng.randint(44, 62)
    lines = ["cap %d" % cap, "mark %d" % mark]
    oid = 0
    for i in range(rng.randint(50, 70)):
        oid += 1
        side = "s" if i % 2 else "b"
        off = 1 + (i % 9)
        px = mark + off if side == "s" else mark - off
        lines.append("new %d %d %s %d %d %s day -"
                     % (oid, 1 + (i % 5), side, px, rng.choice([20, 40, 60]),
                        rng.choice(["-", "5", "8"])))
    live = list(range(1, oid + 1))
    for i in range(arms):
        oid += 1
        side = "b" if i % 2 else "s"
        trp = mark + (60 + (i % 400)) * (1 if side == "b" else -1)
        lines.append("new %d %d %s %d %d - day %d"
                     % (oid, 1 + (i % 5), side, mark, 10, trp))
        live.append(oid)
    for i in range(slabs):
        oid += 1
        side = "s" if i % 2 else "b"
        px = mark + (1 if side == "s" else -1)
        qty = rng.randrange(15000, 22000, 100)
        lines.append("new %d 9 %s %d %d %d day -"
                     % (oid, side, px, qty, rng.choice([2, 3, 4])))
        oid += 1
        lines.append("new %d 8 %s %d %d - part -"
                     % (oid, "b" if side == "s" else "s", px, qty))
        if i % 9 == 4:
            oid += 1
            lines.append("new %d 7 %s %d %d - whole -"
                         % (oid, "b" if side == "s" else "s", px,
                            rng.choice([10, 40, 90])))
        if i % 13 == 6:
            lines.append("pull %d" % rng.choice(live))
    return "\n".join(lines) + "\n"


def deep_book_one(rng):
    mark = 1000
    lines = ["cap 40", "mark %d" % mark]
    oid = 0
    live = []
    for i in range(rng.randint(8000, 9600)):
        oid += 1
        side = "s" if i % 2 else "b"
        off = 3 + (i % 180)
        px = mark + off if side == "s" else mark - off
        lines.append("new %d %d %s %d %d %s day -"
                     % (oid, 1 + (i % 6), side, px, rng.choice([10, 20, 30, 60]),
                        rng.choice(["-", "-", "4", "7"])))
        live.append(oid)
    for i in range(rng.randint(1500, 1900)):
        oid += 1
        side = "s" if i % 2 else "b"
        px = mark + (2 if side == "s" else -2)
        lines.append("new %d %d %s %d %d - day -"
                     % (oid, 1 + (i % 6), side, px, rng.choice([40, 80])))
        oid += 1
        want = rng.choice([20, 40, 90, 160])
        lines.append("new %d %d %s %d %d %s whole -"
                     % (oid, 1 + (i % 6), "b" if side == "s" else "s", px, want,
                        rng.choice(["-", "-", "5"])))
        if i % 40 == 11:
            lines.append("pull %d" % rng.choice(live))
    return "\n".join(lines) + "\n"


def deep_batch(seed, n):
    rng = random.Random("deep|%s" % seed)
    out = []
    for i in range(n):
        if i % 2:
            out.append(("deepbook-%04d" % i, deep_book_one(rng)))
        else:
            out.append(("deep-%04d" % i, deep_one(rng)))
    return out
