"""Stream generator.

Deterministic across processes: every collection is built as a sorted list and
nothing iterates a set, so the runner and the grader build the same streams.

Arrivals are paced against a notional outstanding count rather than drawn
blind. A producer that ignores the link entirely spends every stream in fault,
which grades nothing; pacing keeps most arrivals legal and leaves the feeds
sitting close to their ceilings, which is the state the threshold and the
obligation both turn on.
"""

import random

OPS = ("a", "o", "t", "x")


def stream(nonce, idx):
    rng = random.Random((int(nonce) * 1000003) ^ (idx * 7919 + 13))
    nfeed = rng.randint(3, 6)
    ticks = rng.randint(40, 90)
    feeds = list(range(nfeed))
    ev = []
    shut, back = {}, {}
    for fd in feeds:
        if rng.random() < 0.55:
            at = rng.randint(8, max(9, ticks - 16))
            shut[fd] = at
            if rng.random() < 0.5:
                back[fd] = at + rng.randint(3, 9)
    for fd in feeds:
        out = 0
        when = rng.randint(0, 3)
        while when < ticks:
            size = rng.randint(3, 16)
            if out + size <= rng.choice([28, 34, 38, 40]):
                ev.append([when, "a", fd, size])
                out += size
            else:
                ev.append([when, "t", fd, 0])
                out = max(0, out - rng.randint(6, 14))
            when += rng.randint(1, 3)
        when = rng.randint(2, 6)
        while when < ticks:
            ev.append([when, "t", fd, 0])
            when += rng.randint(3, 7)
    for fd in sorted(shut):
        ev.append([shut[fd], "x", fd, 0])
    for fd in sorted(back):
        if back[fd] < ticks:
            ev.append([back[fd], "o", fd, 0])
            for step in range(rng.randint(1, 3)):
                at = back[fd] + 1 + step
                if at < ticks:
                    ev.append([at, "a", fd, rng.randint(14, 26)])
    ev.sort(key=lambda row: (row[0], OPS.index(row[1]), row[2], row[3]))
    return {"name": "g%04d" % idx, "ticks": ticks, "feeds": feeds, "ev": ev}


def batch(nonce, count):
    return [stream(nonce, i) for i in range(count)]
