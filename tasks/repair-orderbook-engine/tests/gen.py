"""Session generators, seeded from the run nonce.

Two families, because they test different things.

`batch` builds small sessions for correctness. Uniformly random orders barely trade, so
each session is built in two phases - resting liquidity around the mark, then a burst of
orders that actually cross it - and the burst is shaped six ways, at the decisions the
engine turns on: disclosure, the band, the same participant, all-or-nothing admission,
activation, and what a failed whole fired or pulled. A population that is not aimed at a
mechanism does not exercise it. The spark family parks on one side with trip prices
stepping toward the mark, so an order that arrived earlier fires later, tops the other
side up with liquidity of every participant, and sends whole orders too big for it.

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

The additional fill-pace family combines nested whole orders with intervening
activations. Small sessions never contain more than sixteen trip-bearing messages.
The large fill-pace book has one waiting activation at a time and alternates episodes
where descendant execution consumes or supplies capacity to an interrupted whole.
"""

import random

FAM = ("plain", "slice", "band", "whole", "trip", "spark")


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


def spark_one(rng):
    """Order-pace whole orders that come up short after fills that fired.

    One side is swept. The parked orders sit on it with trip prices stepping toward the
    mark, so the one that arrived first fires last; the whole orders are on it too, bigger
    than what rests on the other side inside the band; and the other side is topped up
    between them, so the walks make fills before they come up short.
    """
    cap = rng.choice([3, 4, 6, 8])
    mark = rng.randint(96, 104)
    hands = rng.choice([2, 3, 3, 4])
    sweep = rng.choice("bs")
    other = "s" if sweep == "b" else "b"
    sign = 1 if sweep == "b" else -1
    lines = ["cap %d" % cap, "mark %d" % mark]
    live = []
    oid = 0

    def top_up(qtys):
        px = mark + sign * rng.randint(1, 4)
        shw = "-" if rng.random() < 0.65 else str(rng.choice([3, 5, 8]))
        lines.append("new %d %d %s %d %d %s day -"
                     % (oid, rng.randint(1, hands), other, px, rng.choice(qtys), shw))
        live.append(oid)

    for _ in range(rng.randint(2, 4)):
        oid += 1
        top_up([10, 15, 20, 25])
    parked = 0
    for _ in range(rng.randint(8, 18)):
        oid += 1
        roll = rng.random()
        if roll < 0.08 and live:
            oid -= 1
            lines.append("pull %d" % rng.choice(live))
            continue
        if roll < 0.40:
            step = (3, 2, 1)[parked % 3]
            parked += 1
            px = "-" if rng.random() < 0.35 else str(mark + sign * rng.randint(2, 7))
            lines.append("new %d %d %s %s %d %s %s %d"
                         % (oid, rng.randint(1, hands), sweep, px,
                            rng.choice([5, 10, 15, 25]),
                            "-" if rng.random() < 0.7 else str(rng.choice([3, 5])),
                            rng.choice(["day", "day", "part", "whole"]), mark + sign * step))
            live.append(oid)
            continue
        if roll < 0.62:
            top_up([10, 15, 20, 25, 40])
            continue
        px = "-" if rng.random() < 0.3 else str(mark + sign * rng.randint(2, 7))
        lines.append("new %d %d %s %s %d - %s -"
                     % (oid, rng.randint(1, hands), sweep, px, rng.choice([25, 35, 50, 70, 90]),
                        rng.choice(["whole", "whole", "whole", "day", "part"])))
        live.append(oid)
    return "\n".join(lines) + "\n"


def batch(seed, n, fams=FAM):
    rng = random.Random("small|%s" % seed)
    out = []
    for i in range(n):
        fam = fams[i % len(fams)]
        text = spark_one(rng) if fam == "spark" else one(rng, fam)
        out.append(("%s-%04d" % (fam, i), text))
    return out


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


def fill_one(rng, index):
    mark = rng.randint(950, 1050)
    cap = rng.choice([1, 2, 3, 5, 8])
    lines = ["pace fill", "cap %d" % cap, "mark %d" % mark]
    ids = rng.sample(range(1, 1000000), 160)
    at = 0
    for i in range(rng.randint(4, 9)):
        side = rng.choice("bs")
        off = rng.randint(0, 4)
        px = mark - off if side == "b" else mark + off
        lines.append("new %d %d %s %d %d %s day -" % (
            ids[at], rng.randint(1, 5), side, px, rng.randint(1, 12),
            rng.choice(["-", "1", "2", "3"])))
        at += 1
    # At most sixteen trip-bearing messages exist in one session, independent of
    # whether any of them fire or are restored by an unsuccessful whole order.
    armed = 0
    for i in range(72):
        if i % 11 == 8:
            lines.append("pull %d" % rng.choice(ids[:at]))
            continue
        side = rng.choice("bs")
        px = "-" if rng.random() < 0.18 else str(mark + rng.randint(-6, 6))
        trp = "-"
        if armed < 16 and (i < 8 or rng.random() < 0.29):
            trp = str(mark + rng.randint(-3, 3))
            armed += 1
        tif = rng.choice(["day", "part", "whole", "whole"])
        lines.append("new %d %d %s %s %d %s %s %s" % (
            ids[at], rng.randint(1, 5), side, px, rng.randint(1, 16),
            rng.choice(["-", "1", "2", "4"]), tif, trp))
        at += 1
    for oid in rng.sample(ids[:at], 8):
        lines.append("pull %d" % oid)
    return "\n".join(lines) + "\n"


def fill_batch(seed, n=120):
    rng = random.Random("fill|%s" % seed)
    return [("fill-random-%04d" % i, fill_one(rng, i)) for i in range(n)]


def deep_fill_one(rng):
    mark = 1000
    lines = ["pace fill", "cap 4", "mark %d" % mark]
    oid = 0
    for i in range(rng.randint(8400, 9200)):
        oid += 1
        side = "s" if i % 2 else "b"
        off = 300 + (i % 180)
        px = mark + off if side == "s" else mark - off
        lines.append("new %d %d %s %d %d %s day -" % (
            oid, 10 + (i % 6), side, px, rng.choice([10, 20, 40]),
            rng.choice(["-", "4", "7"])))
    for i in range(rng.randint(1500, 1700)):
        side = "s" if i % 2 else "b"
        taker = "b" if side == "s" else "s"
        unit = rng.randint(1, 4)
        consume = i % 3 != 1
        maker, child, parent = oid + 1, oid + 2, oid + 3
        oid += 3
        lines.append("new %d 1 %s %d %d %d day -" % (
            maker, side, mark, 2 * unit if consume else unit, unit))
        lines.append("new %d 2 %s %d %d - %s %d" % (
            child, taker if consume else side, mark, unit,
            "whole" if consume else "day", mark))
        lines.append("new %d 3 %s %d %d - whole -" % (
            parent, taker, mark, 2 * unit))
        if consume:
            lines.append("pull %d" % maker)
            lines.append("pull %d" % child)
    return "\n".join(lines) + "\n"


def fill_deep_batch(seed, n=1):
    rng = random.Random("filldeep|%s" % seed)
    return [("fill-deepbook-%04d" % i, deep_fill_one(rng)) for i in range(n)]
