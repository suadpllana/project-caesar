"""The generated half of the graded set.

Eleven families, each shaped around a mechanism rather than sampled at random, because an
unshaped population does not exercise a rule often enough to separate a wrong reading from the
reference. `cover` puts a reader's own change over a key another transaction then commits;
`restore` moves a value and moves it back while a reader is open; `same` rewrites a key with
the value it already holds; `edge` lands scans exactly on their row limit and writes just
inside and just past the last row returned; `stale` reads at a base the rows have already
moved past; `roll` writes a key on both sides of a mark; `order` kills several transactions
with one commit; `empty` commits nothing and drops.

`deep` and `wide` are the two scale families. In both the long-lived transaction is never
broken - the committers work on keys it never touched - so an engine that re-tests every claim
of every open transaction at every commit does all of that work and is still exactly correct.

The seed is drawn inside the verifier after the agent's container is gone, so no submission can
have seen these programs.
"""
import random

FAMILIES = [
    ("plain", False),
    ("cover", False),
    ("restore", False),
    ("same", False),
    ("edge", False),
    ("stale", False),
    ("roll", False),
    ("order", False),
    ("empty", False),
    ("deep", True),
    ("wide", True),
]

BIG = 3


class Tape:
    """A program under construction, with just enough state to stay valid."""

    def __init__(self, rng):
        self.rng = rng
        self.lines = []
        self.live = []
        self.marks = {}
        self.nxt = 1

    def start(self):
        tid = self.nxt
        self.nxt += 1
        self.live.append(tid)
        self.marks[tid] = []
        self.lines.append("open %d" % tid)
        return tid

    def op(self, text):
        self.lines.append(text)

    def seed_rows(self, keys, vals):
        tid = self.start()
        for key in keys:
            self.op("put %d %d %d" % (tid, key, self.rng.randrange(vals)))
        self.finish(tid)

    def finish(self, tid, drop=False):
        self.live.remove(tid)
        self.marks.pop(tid, None)
        self.op("%s %d" % ("drop" if drop else "seal", tid))

    def commit(self, key, val):
        tid = self.start()
        if val is None:
            self.op("del %d %d" % (tid, key))
        else:
            self.op("put %d %d %d" % (tid, key, val))
        self.finish(tid)

    def close(self):
        for tid in list(self.live):
            self.finish(tid)
        return self.lines


def _plain(rng):
    t = Tape(rng)
    keys, vals = 16, 4
    t.seed_rows(sorted(rng.sample(range(keys), rng.randrange(3, 8))), vals)
    for _ in range(rng.randrange(20, 40)):
        if not t.live or (len(t.live) < 4 and rng.random() < 0.3):
            t.start()
            continue
        tid = rng.choice(t.live)
        pick = rng.random()
        if pick < 0.22:
            t.op("get %d %d" % (tid, rng.randrange(keys)))
        elif pick < 0.42:
            lo = rng.randrange(keys)
            t.op("span %d %d %d %d" % (tid, lo, min(keys - 1, lo + rng.randrange(1, 8)),
                                       rng.randrange(1, 4)))
        elif pick < 0.60:
            t.op("put %d %d %d" % (tid, rng.randrange(keys), rng.randrange(vals)))
        elif pick < 0.70:
            t.op("del %d %d" % (tid, rng.randrange(keys)))
        elif pick < 0.78:
            name = rng.choice("ab")
            t.marks[tid].append(name)
            t.op("mark %d %s" % (tid, name))
        elif pick < 0.86:
            if t.marks[tid]:
                t.op("back %d %s" % (tid, rng.choice(t.marks[tid])))
        elif pick < 0.94:
            t.finish(tid, drop=rng.random() < 0.2)
        else:
            lo = rng.randrange(keys)
            t.op("look %d %d" % (lo, min(keys - 1, lo + rng.randrange(1, 6))))
    t.close()
    t.op("look 0 %d" % (keys - 1))
    return t.lines


def _cover(rng):
    t = Tape(rng)
    keys = 12
    t.seed_rows(sorted(rng.sample(range(keys), 5)), 4)
    key = rng.randrange(keys)
    reader = t.start()
    t.op("put %d %d %d" % (reader, key, rng.randrange(4)))
    named = rng.random() < 0.8
    if named:
        t.op("mark %d m" % reader)
        if rng.random() < 0.6:
            t.op("put %d %d %d" % (reader, key, rng.randrange(4)))
    lo = max(0, key - rng.randrange(1, 4))
    hi = min(keys - 1, key + rng.randrange(1, 4))
    if rng.random() < 0.5:
        t.op("span %d %d %d %d" % (reader, lo, hi, rng.randrange(1, 4)))
    else:
        t.op("get %d %d" % (reader, key))
    if rng.random() < 0.7:
        t.commit(key, None if rng.random() < 0.25 else rng.randrange(4))
    if named and rng.random() < 0.8:
        t.op("back %d m" % reader)
    t.op("get %d %d" % (reader, key))
    t.op("span %d %d %d %d" % (reader, lo, hi, 2))
    t.close()
    t.op("look 0 %d" % (keys - 1))
    return t.lines


def _restore(rng):
    t = Tape(rng)
    keys = 10
    start = {k: rng.randrange(4) for k in rng.sample(range(keys), 5)}
    tid = t.start()
    for key in sorted(start):
        t.op("put %d %d %d" % (tid, key, start[key]))
    t.finish(tid)
    key = rng.choice(sorted(start))
    reader = t.start()
    if rng.random() < 0.5:
        t.op("get %d %d" % (reader, key))
    else:
        t.op("span %d 0 %d 4" % (reader, keys - 1))
    other = rng.randrange(4)
    while other == start[key]:
        other = rng.randrange(4)
    t.commit(key, other)
    t.commit(key, start[key])
    t.op("get %d %d" % (reader, key))
    t.close()
    t.op("look 0 %d" % (keys - 1))
    return t.lines


def _same(rng):
    t = Tape(rng)
    keys = 10
    start = {k: rng.randrange(4) for k in rng.sample(range(keys), 6)}
    tid = t.start()
    for key in sorted(start):
        t.op("put %d %d %d" % (tid, key, start[key]))
    t.finish(tid)
    key = rng.choice(sorted(start))
    mine = rng.choice(sorted(start))
    reader = t.start()
    t.op("span %d 0 %d %d" % (reader, keys - 1, rng.randrange(2, 5)))
    t.op("put %d %d %d" % (reader, mine, rng.randrange(4)))
    t.commit(key, start[key])
    if rng.random() < 0.6:
        t.commit(mine, start.get(mine, 0))
    t.op("get %d %d" % (reader, key))
    t.close()
    t.op("look 0 %d" % (keys - 1))
    return t.lines


def _edge(rng):
    """Scans that land exactly on their row limit, and commits just inside and just past the
    last row returned; and scans that come back short, with an insert in the gap."""
    t = Tape(rng)
    keys = 20
    rows = sorted(rng.sample(range(keys), rng.randrange(5, 9)))
    t.seed_rows(rows, 4)
    reader = t.start()
    short = rng.random() < 0.35
    n = len(rows) + rng.randrange(1, 3) if short else rng.randrange(1, len(rows) + 1)
    t.op("span %d 0 %d %d" % (reader, keys - 1, n))
    if short:
        gap = [k for k in range(keys) if k not in rows]
        t.commit(rng.choice(gap) if gap else rows[0], rng.randrange(4))
    elif rng.random() < 0.5:
        after = [k for k in range(rows[n - 1] + 1, keys) if k not in rows]
        t.commit(rng.choice(after) if after else rows[n - 1], rng.randrange(4))
    else:
        t.commit(rng.choice(rows[:n]), rng.randrange(4))
    t.op("span %d 0 %d %d" % (reader, keys - 1, n))
    t.close()
    t.op("look 0 %d" % (keys - 1))
    return t.lines


def _stale(rng):
    """Reads taken at a base the rows have already moved past."""
    t = Tape(rng)
    keys = 12
    rows = sorted(rng.sample(range(keys), 5))
    t.seed_rows(rows, 4)
    reader = t.start()
    moved = []
    for _ in range(rng.randrange(1, 4)):
        key = rng.choice(rows) if rng.random() < 0.7 else rng.randrange(keys)
        moved.append(key)
        t.commit(key, None if rng.random() < 0.2 else rng.randrange(4))
    key = rng.choice(moved) if rng.random() < 0.75 else rng.randrange(keys)
    if rng.random() < 0.5:
        t.op("get %d %d" % (reader, key))
    else:
        t.op("span %d %d %d %d" % (reader, max(0, key - rng.randrange(0, 3)), keys - 1,
                                   rng.randrange(1, 4)))
    t.op("put %d %d %d" % (reader, rng.choice(rows), rng.randrange(4)))
    t.close()
    t.op("look 0 %d" % (keys - 1))
    return t.lines


def _roll(rng):
    """Marks and rollbacks: a key written on both sides of a mark, a mark rolled back to twice,
    and a key the rollback leaves the transaction with no change on at all."""
    t = Tape(rng)
    keys = 14
    t.seed_rows(sorted(rng.sample(range(keys), 5)), 4)
    key = rng.randrange(keys)
    other = rng.randrange(keys)
    only = rng.randrange(keys)
    while only == key:
        only = rng.randrange(keys)
    reader = t.start()
    t.op("put %d %d %d" % (reader, key, rng.randrange(4)))
    t.op("mark %d m" % reader)
    t.op("put %d %d %d" % (reader, key, rng.randrange(4)))
    t.op("put %d %d %d" % (reader, only, rng.randrange(4)))
    if rng.random() < 0.4:
        t.op("back %d m" % reader)
        t.op("put %d %d %d" % (reader, other, rng.randrange(4)))
    t.op("span %d 0 %d %d" % (reader, keys - 1, rng.randrange(2, 5)))
    t.op("back %d m" % reader)
    if rng.random() < 0.7:
        t.commit(only, rng.randrange(4))
    if rng.random() < 0.3:
        t.commit(key, rng.randrange(4))
    t.op("get %d %d" % (reader, key))
    t.op("get %d %d" % (reader, only))
    t.close()
    t.op("look 0 %d" % (keys - 1))
    return t.lines


def _order(rng):
    t = Tape(rng)
    keys = 10
    t.seed_rows(sorted(rng.sample(range(keys), 5)), 4)
    key = rng.randrange(keys)
    ids = rng.sample(range(20, 40), rng.randrange(3, 5))
    for tid in ids:
        t.op("open %d" % tid)
        t.live.append(tid)
        t.marks[tid] = []
        t.op("span %d 0 %d 4" % (tid, keys - 1))
        t.op("get %d %d" % (tid, key))
    t.commit(key, rng.randrange(4))
    for tid in ids:
        t.op("get %d %d" % (tid, key))
    t.close()
    t.op("look 0 %d" % (keys - 1))
    return t.lines


def _empty(rng):
    t = Tape(rng)
    keys = 8
    t.seed_rows(sorted(rng.sample(range(keys), 4)), 3)
    reader = t.start()
    t.op("get %d %d" % (reader, rng.randrange(keys)))
    for _ in range(rng.randrange(1, 4)):
        tid = t.start()
        t.finish(tid, drop=rng.random() < 0.4)
    key = rng.randrange(keys)
    t.commit(key, rng.randrange(3))
    later = t.start()
    t.op("get %d %d" % (later, key))
    t.op("look 0 %d" % (keys - 1))
    t.close()
    return t.lines


def _deep(rng):
    """One transaction holding thousands of claims while thousands of commits go past it.

    The commits write keys the reader has read, with the value those keys already hold, so
    nothing it holds ever stops standing and every claim on the key has to be looked at.
    """
    t = Tape(rng)
    pool = sorted(rng.sample(range(4000), 800))
    held = {key: rng.randrange(6) for key in pool}
    tid = t.start()
    for key in pool:
        t.op("put %d %d %d" % (tid, key, held[key]))
    t.finish(tid)
    reader = t.start()
    mine = 100000
    rounds = 1500
    for i in range(rounds):
        t.op("get %d %d" % (reader, rng.choice(pool)))
        t.op("put %d %d %d" % (reader, mine + i, rng.randrange(6)))
        t.op("get %d %d" % (reader, rng.choice(pool)))
        key = rng.choice(pool)
        t.commit(key, held[key])
        t.op("get %d %d" % (reader, rng.choice(pool)))
        key = rng.choice(pool)
        t.commit(key, held[key])
    t.op("span %d 0 %d 3" % (reader, 4000))
    t.close()
    t.op("look %d %d" % (mine, mine + 3))
    return t.lines


def _wide(rng):
    """Scans over wide ranges, and commits that write keys inside them without moving a row."""
    t = Tape(rng)
    reach = 30000
    rows = sorted(rng.sample(range(reach), 2600))
    held = {key: rng.randrange(6) for key in rows}
    tid = t.start()
    for key in rows:
        t.op("put %d %d %d" % (tid, key, held[key]))
    t.finish(tid)
    reader = t.start()
    for i in range(90):
        if i % 4:
            t.op("span %d 0 %d 4000" % (reader, reach - 1))
        else:
            t.op("span %d 0 %d %d" % (reader, reach - 1, rng.randrange(1, 4)))
    for i in range(1200):
        key = rng.choice(rows)
        t.commit(key, held[key])
    t.op("get %d %d" % (reader, rows[0]))
    t.close()
    t.op("look 0 3")
    return t.lines


MAKERS = {
    "plain": _plain, "cover": _cover, "restore": _restore, "same": _same, "edge": _edge,
    "stale": _stale, "roll": _roll, "order": _order, "empty": _empty, "deep": _deep,
    "wide": _wide,
}


def programs(seed, per):
    """Every generated program of the graded set, as (family, name, lines)."""
    work = []
    for fam, big in FAMILIES:
        count = BIG if big else per
        for i in range(count):
            rng = random.Random("%s|%s|%d" % (seed, fam, i))
            work.append((fam, "%s-%03d" % (fam, i), MAKERS[fam](rng)))
    return work
