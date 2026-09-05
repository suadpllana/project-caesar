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
WIDE_EVERY = 60


def is_wide(idx):
    return idx % WIDE_EVERY == WIDE_EVERY - 1


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


def wide(nonce, idx):
    """The wide family: ten thousand feeds over a hundred and fifty thousand ticks, each
    feed busy for a short stretch, so only a few share the link at any moment.
    A feed sits idle until its stretch begins, so its producer opens with a
    batch under the floor, waits for the window to come back, and then paces
    itself the way the small streams do. A policy that looks at every feed on
    every tick does work in proportion to feeds times ticks and is killed long
    before it finishes."""
    rng = random.Random((int(nonce) * 1000003) ^ (idx * 7919 + 977))
    nfeed = rng.randint(9000, 11000)
    ticks = rng.randint(150000, 170000)
    feeds = list(range(nfeed))
    ev = []
    for fd in feeds:
        start = rng.randint(10, ticks - 80)
        span = rng.randint(24, 50)
        ev.append([start, "a", fd, rng.randint(5, 12)])
        out = 0
        landed = 1
        when = start + rng.randint(3, 5)
        while when < start + span:
            size = rng.randint(3, 16)
            if out + size <= rng.choice([28, 34, 38, 40]):
                ev.append([when, "a", fd, size])
                out += size
                landed += 1
            else:
                ev.append([when, "t", fd, 0])
                out = max(0, out - rng.randint(6, 14))
            when += rng.randint(1, 3)
        when = start + rng.randint(2, 6)
        while when < start + span:
            ev.append([when, "t", fd, 0])
            when += rng.randint(3, 7)
        for step in range(landed):
            ev.append([when, "t", fd, 0])
            when += rng.randint(1, 2)
        if rng.random() < 0.4:
            at = start + span + rng.randint(0, 4)
            ev.append([at, "x", fd, 0])
            if rng.random() < 0.5:
                back = at + rng.randint(3, 9)
                if back < ticks:
                    ev.append([back, "o", fd, 0])
                    burst = rng.randint(1, 3)
                    for step in range(burst):
                        if back + 1 + step < ticks:
                            ev.append([back + 1 + step, "a", fd, rng.randint(5, 14)])
                    for step in range(burst):
                        if back + 5 + 2 * step < ticks:
                            ev.append([back + 5 + 2 * step, "t", fd, 0])
    ev.sort(key=lambda row: (row[0], OPS.index(row[1]), row[2], row[3]))
    return {"name": "g%04d" % idx, "ticks": ticks, "feeds": feeds, "ev": ev}


def batch(nonce, count):
    return [wide(nonce, i) if is_wide(i) else stream(nonce, i) for i in range(count)]


def small(nonce, count):
    """The batch without its wide members, for authoring checks that want
    many streams quickly."""
    return [stream(nonce, i) for i in range(count) if not is_wide(i)]
