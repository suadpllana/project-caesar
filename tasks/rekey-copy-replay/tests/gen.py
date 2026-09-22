"""Programs generated from a seed drawn after the agent's container is gone.

The families are shaped around the graded rules rather than sampled from the input space.
An unshaped program almost never makes an entry stale, never moves a row off a key another
row is waiting for and never stops a chunk short of its range, so every wrong reading scores
the same as the right one. Each family below leans on one mechanism; the last two exist for
the execution limit rather than for a rule.

  plain     ordinary traffic: writes, chunks and plays interleaved, little contention
  stale     a chunk read after the writes it covers, so entries arrive already reflected
  ahead     writes far above the cursor with chunks held back, so entries are dropped unread
  movey     updates that change the first two fields, so rows move under the new key
  clash     a small field space, so rows queue behind one another for the same new key
  holey     heavy deletes, so a chunk stops short of the top of its reach
  latekey   keys written below the cursor after the walk has passed them
  sameish   updates that leave the first two fields alone and change only the third
  missy     deletes of rows the rebuild never took
  wide      one long program, many keys, many chunks
  deep      more chunks than keys, with the journal far longer than the source
"""
import random

FAMILIES = (
    ("plain", False),
    ("stale", False),
    ("ahead", False),
    ("movey", False),
    ("clash", False),
    ("holey", False),
    ("latekey", False),
    ("sameish", False),
    ("missy", False),
    ("wide", True),
    ("deep", True),
)

BIG = 3


class Build:
    def __init__(self, rng, chunk, span):
        self.rng = rng
        self.lines = ["cfg %d" % chunk]
        self.live = set()
        self.span = span
        self.next = 1

    def key(self):
        k = self.next
        self.next += self.rng.randint(1, 3)
        return k

    def fields(self):
        return (self.rng.randrange(self.span), self.rng.randrange(self.span),
                self.rng.randint(0, 40))

    def set(self, k, fld=None):
        a, b, c = fld if fld is not None else self.fields()
        self.lines.append("set %d %d %d %d" % (k, a, b, c))
        self.live.add(k)

    def kill(self, k):
        self.lines.append("del %d" % k)
        self.live.discard(k)

    def copy(self):
        self.lines.append("copy")

    def play(self, n):
        self.lines.append("play %d" % n)

    def done(self):
        self.lines.append("cut")
        return self.lines


def _plain(rng):
    b = Build(rng, rng.choice([2, 3, 4]), rng.choice([3, 4, 6]))
    for _ in range(rng.randint(14, 26)):
        roll = rng.random()
        if roll < 0.55 or not b.live:
            b.set(b.key())
        elif roll < 0.68:
            b.set(rng.choice(sorted(b.live)))
        elif roll < 0.74:
            b.kill(rng.choice(sorted(b.live)))
        elif roll < 0.88:
            b.copy()
        else:
            b.play(rng.randint(1, 5))
    return b.done()


def _stale(rng):
    b = Build(rng, rng.choice([2, 3]), rng.choice([3, 5]))
    keys = []
    for _ in range(rng.randint(8, 14)):
        k = b.key()
        keys.append(k)
        b.set(k)
    for _ in range(rng.randint(6, 12)):
        b.set(rng.choice(keys))
        if rng.random() < 0.5:
            b.copy()
        if rng.random() < 0.4:
            b.play(rng.randint(1, 4))
    for _ in range(3):
        b.copy()
    b.play(rng.randint(2, 8))
    return b.done()


def _ahead(rng):
    b = Build(rng, 2, rng.choice([3, 4]))
    keys = []
    for _ in range(rng.randint(10, 16)):
        k = b.key()
        keys.append(k)
        b.set(k)
    for _ in range(rng.randint(8, 16)):
        b.set(rng.choice(keys))
        if rng.random() < 0.55:
            b.play(rng.randint(1, 3))
        if rng.random() < 0.22:
            b.copy()
    return b.done()


def _movey(rng):
    b = Build(rng, rng.choice([2, 3]), rng.choice([2, 3, 4]))
    keys = []
    for _ in range(rng.randint(6, 10)):
        k = b.key()
        keys.append(k)
        b.set(k)
    b.copy()
    b.copy()
    b.play(rng.randint(2, 6))
    for _ in range(rng.randint(10, 20)):
        b.set(rng.choice(keys))
        if rng.random() < 0.45:
            b.play(rng.randint(1, 4))
        if rng.random() < 0.3:
            b.copy()
    return b.done()


def _clash(rng):
    b = Build(rng, rng.choice([3, 4]), 2)
    keys = []
    for _ in range(rng.randint(10, 16)):
        k = b.key()
        keys.append(k)
        b.set(k)
    for _ in range(rng.randint(12, 22)):
        roll = rng.random()
        if roll < 0.4:
            b.set(rng.choice(keys))
        elif roll < 0.5 and b.live:
            b.kill(rng.choice(sorted(b.live)))
        elif roll < 0.78:
            b.copy()
        else:
            b.play(rng.randint(1, 5))
    return b.done()


def _holey(rng):
    b = Build(rng, rng.choice([3, 4, 5]), rng.choice([3, 5]))
    keys = []
    for _ in range(rng.randint(14, 22)):
        k = b.key()
        keys.append(k)
        b.set(k)
    for _ in range(rng.randint(6, 12)):
        if b.live and rng.random() < 0.7:
            b.kill(rng.choice(sorted(b.live)))
        else:
            b.set(rng.choice(keys))
    for _ in range(rng.randint(8, 16)):
        if rng.random() < 0.6:
            b.copy()
        else:
            b.play(rng.randint(1, 6))
        if rng.random() < 0.25 and b.live:
            b.kill(rng.choice(sorted(b.live)))
    return b.done()


def _latekey(rng):
    b = Build(rng, rng.choice([3, 4]), 2)
    room = []
    for _ in range(rng.randint(8, 12)):
        k = b.key()
        room.append(k)
        if rng.random() < 0.7:
            b.set(k)
    for _ in range(rng.randint(3, 5)):
        b.copy()
    b.play(rng.randint(2, 6))
    for _ in range(rng.randint(12, 20)):
        roll = rng.random()
        if roll < 0.46:
            b.set(rng.choice(room[:max(2, len(room) // 2)]))
        elif roll < 0.6:
            b.set(rng.choice(room))
        elif roll < 0.7 and b.live:
            b.kill(rng.choice(sorted(b.live)))
        elif roll < 0.88:
            b.play(rng.randint(1, 4))
        else:
            b.copy()
    return b.done()


def _sameish(rng):
    b = Build(rng, rng.choice([2, 3]), rng.choice([2, 3]))
    keys = []
    held = {}
    for _ in range(rng.randint(8, 14)):
        k = b.key()
        keys.append(k)
        a, bb, c = b.fields()
        held[k] = (a, bb)
        b.set(k, (a, bb, c))
    b.copy()
    b.copy()
    b.play(rng.randint(2, 6))
    for _ in range(rng.randint(12, 20)):
        k = rng.choice(keys)
        if rng.random() < 0.7:
            a, bb = held[k]
            b.set(k, (a, bb, rng.randint(0, 40)))
        else:
            a, bb, c = b.fields()
            held[k] = (a, bb)
            b.set(k, (a, bb, c))
        if rng.random() < 0.5:
            b.play(rng.randint(1, 4))
        if rng.random() < 0.3:
            b.copy()
    return b.done()


def _missy(rng):
    b = Build(rng, rng.choice([2, 3]), rng.choice([3, 4]))
    room = []
    for _ in range(rng.randint(10, 16)):
        k = b.key()
        room.append(k)
        b.set(k)
    for _ in range(rng.randint(3, 5)):
        b.copy()
    b.play(rng.randint(4, 10))
    for _ in range(rng.randint(14, 24)):
        roll = rng.random()
        if roll < 0.34:
            k = rng.choice(room)
            b.kill(k)
            if rng.random() < 0.6:
                b.kill(k)
        elif roll < 0.5:
            b.set(rng.choice(room))
        elif roll < 0.74:
            b.copy()
        else:
            b.play(rng.randint(2, 8))
    return b.done()


def _wide(rng):
    b = Build(rng, 5, 70)
    keys = []
    for _ in range(2000):
        k = b.key()
        keys.append(k)
        b.set(k)
    for step in range(10000):
        b.copy()
        for _ in range(4):
            k = b.key()
            keys.append(k)
            b.set(k)
        for _ in range(2):
            roll = rng.random()
            if roll < 0.14:
                b.kill(rng.choice(keys))
            else:
                b.set(rng.choice(keys))
        if step % 2 == 0:
            b.play(rng.randint(6, 14))
    return b.done()


def _deep(rng):
    b = Build(rng, 2, 12)
    keys = []
    for _ in range(1200):
        k = b.key()
        keys.append(k)
        b.set(k)
    for step in range(9000):
        b.copy()
        for _ in range(2):
            k = b.key()
            keys.append(k)
            b.set(k)
        for _ in range(10):
            roll = rng.random()
            if roll < 0.12:
                b.kill(rng.choice(keys))
            else:
                b.set(rng.choice(keys))
        b.play(rng.randint(8, 16))
    return b.done()


SHAPES = {
    "plain": _plain,
    "stale": _stale,
    "ahead": _ahead,
    "movey": _movey,
    "clash": _clash,
    "holey": _holey,
    "latekey": _latekey,
    "sameish": _sameish,
    "missy": _missy,
    "wide": _wide,
    "deep": _deep,
}


def programs(seed, per):
    out = []
    for fam, big in FAMILIES:
        count = BIG if big else per
        for i in range(count):
            rng = random.Random("%s/%s/%d" % (seed, fam, i))
            out.append((fam, "%s-%03d" % (fam, i), SHAPES[fam](rng)))
    return out
