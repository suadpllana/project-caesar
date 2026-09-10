"""Programs generated inside the verifier, from a seed drawn after the agent is gone.

Twelve families. Ten are small and concentrate one mechanism far above its natural rate: the
sliver on both sides of sixteen bytes, a range set aside and taken and set aside again, more
than thirty-two aside at once, a free run straddling a part boundary, a request that fails and
leaves the arena joined behind it, a growth into bytes that are aside against a growth into
bytes that are in the map, a resize that moves to exactly its own size, ranges over the aside
threshold that never enter the list at all.

Two are large and exist for the execution limit rather than for a rule. `wide` fills about two thirds
of a four megabyte arena with live ranges and small holes and then asks for sizes none of those
holes can take, so every placement has to skip thousands of parts. `churn` drives the aside list
past its bound tens of thousands of times over an arena of the same size, so every return to the
map has to find its neighbours.

Nothing here knows the answer: the model computes it.
"""
import random

FAMILIES = [
    ("plain", True),
    ("press", True),
    ("again", True),
    ("sliv", True),
    ("edge", True),
    ("full", True),
    ("grow", True),
    ("move", True),
    ("big", True),
    ("mix", True),
    ("wide", False),
    ("churn", False),
]

BIG_EACH = 3


def _head(span, part):
    return ["span %d" % span, "part %d" % part]


def _plain(rng):
    out = _head(4096, 512)
    names = []
    for _ in range(160):
        r = rng.random()
        if r < 0.45 or not names:
            name = "x%d" % rng.randrange(40)
            out.append("get %s %d" % (name, rng.choice(
                [0, 1, 8, 16, 24, 33, 40, 64, 100, 128, 250, 260, 300, 512, 520])))
            names.append(name)
        elif r < 0.74:
            out.append("put %s" % rng.choice(names))
        elif r < 0.94:
            out.append("fit %s %d" % (rng.choice(names), rng.choice(
                [8, 16, 24, 40, 64, 96, 128, 200, 400])))
        else:
            out.append("sweep")
    return out


def _press(rng):
    out = _head(16384, 1024)
    live = []
    for i in range(70):
        name = "p%d" % i
        out.append("get %s %d" % (name, rng.choice([16, 24, 32, 40, 48, 64, 96, 120])))
        live.append(name)
    rng.shuffle(live)
    for i, name in enumerate(live):
        out.append("put %s" % name)
        if i % 7 == 3:
            out.append("get q%d %d" % (i, rng.choice([16, 24, 32, 40, 48, 64, 96, 120])))
        if i % 23 == 11:
            out.append("sweep")
    for i in range(30):
        out.append("get r%d %d" % (i, rng.choice([16, 24, 32, 40, 64])))
    return out


def _again(rng):
    out = _head(16384, 1024)
    s = rng.choice([24, 32, 48])
    t = s + rng.choice([8, 16, 24])
    for i in range(40):
        out.append("get a%d %d" % (i, s))
    for i in range(40):
        out.append("get e%d %d" % (i, t))
    seq = ["a%d" % i for i in range(40)] + ["e%d" % i for i in range(40)]
    rng.shuffle(seq)
    pend = []
    for k, name in enumerate(seq):
        out.append("put %s" % name)
        if k % 6 == 5:
            g = "g%d" % k
            out.append("get %s %d" % (g, s if k % 12 == 5 else t))
            pend.append(g)
        if len(pend) >= 3:
            out.append("put %s" % pend.pop(0))
        if k % 17 == 9:
            out.append("get h%d %d" % (k, rng.choice([2 * s, 128, 200])))
    for g in pend:
        out.append("put %s" % g)
    out.append("get r 128")
    out.append("get u 256")
    out.append("sweep")
    for i in range(10):
        out.append("get d%d %d" % (i, rng.choice([s, t, 128, 300])))
    return out


def _sliv(rng):
    out = _head(8192, 1024)
    hole = rng.choice([48, 56, 64, 72, 96, 128])
    for i in range(9):
        out.append("get s%d %d" % (i, hole))
    for i in (1, 3, 5, 7):
        out.append("put s%d" % i)
    out.append("sweep")
    for k, want in enumerate([hole - 8, hole - 16, hole - 24, hole]):
        out.append("get t%d %d" % (k, want))
    for i in range(6):
        out.append("get u%d %d" % (i, rng.choice([hole - 8, hole - 16, hole, 16, 24])))
    for i in range(0, 9, 2):
        out.append("put s%d" % i)
    out.append("sweep")
    for i in range(8):
        out.append("get v%d %d" % (i, rng.choice([hole - 8, hole + 8, 2 * hole - 8, 16])))
    return out


def _edge(rng):
    out = _head(4096, 256)
    for i in range(14):
        out.append("get e%d %d" % (i, rng.choice([64, 96, 128, 160, 200, 248, 256])))
    for i in rng.sample(range(14), 7):
        out.append("put e%d" % i)
    out.append("sweep")
    for i in range(14):
        out.append("get f%d %d" % (i, rng.choice([128, 160, 192, 224, 256, 264, 32])))
    for i in rng.sample(range(14), 6):
        out.append("put f%d" % i)
    out.append("sweep")
    for i in range(10):
        out.append("get g%d %d" % (i, rng.choice([200, 232, 248, 256, 8])))
    return out


def _full(rng):
    out = _head(2048, 512)
    for i in range(14):
        out.append("get h%d %d" % (i, rng.choice([64, 96, 128, 192, 256])))
    for i in range(8):
        out.append("get i%d %d" % (i, rng.choice([256, 384, 512])))
    for i in rng.sample(range(14), 6):
        out.append("put h%d" % i)
    for i in range(10):
        out.append("get j%d %d" % (i, rng.choice([64, 128, 256, 512])))
    for i in range(8):
        out.append("put i%d" % i)
    for i in range(10):
        out.append("get k%d %d" % (i, rng.choice([16, 64, 256, 512])))
    return out


def _grow(rng):
    out = _head(8192, 1024)
    for i in range(16):
        out.append("get w%d %d" % (i, rng.choice([32, 48, 64, 96])))
    for i in range(1, 16, 2):
        out.append("put w%d" % i)
        out.append("fit w%d %d" % (i - 1, rng.choice([80, 120, 160, 200])))
    out.append("sweep")
    for i in range(0, 16, 4):
        out.append("fit w%d %d" % (i, rng.choice([100, 140, 220, 24, 8])))
    for i in range(14):
        out.append("get y%d %d" % (i, rng.choice([32, 64, 128])))
    for i in range(0, 14, 2):
        out.append("put y%d" % (i + 1))
        out.append("fit y%d %d" % (i, rng.choice([72, 104, 168, 240])))
        out.append("sweep")
        out.append("fit y%d %d" % (i, rng.choice([16, 40, 88, 136, 300])))
    return out


def _move(rng):
    out = _head(8192, 1024)
    size = rng.choice([40, 64, 96, 128])
    for i in range(10):
        out.append("get m%d %d" % (i, size))
    out.append("put m3")
    out.append("fit m0 %d" % size)
    out.append("fit m1 %d" % (size + 32))
    out.append("put m5")
    out.append("fit m4 %d" % (size + 8))
    out.append("sweep")
    for i in range(6):
        out.append("fit m%d %d" % (i, rng.choice([size, size + 8, size - 8, size + 64, 300])))
    for i in range(12):
        out.append("get n%d %d" % (i, rng.choice([size, size + 8, 200, 264, 300])))
    for i in range(0, 12, 2):
        out.append("put n%d" % (i + 1))
        out.append("fit n%d %d" % (i, rng.choice([size + 24, 264, 304, 16])))
    return out


def _big(rng):
    out = _head(16384, 1024)
    for i in range(12):
        out.append("get B%d %d" % (i, rng.choice([264, 300, 384, 512, 700, 1024])))
    for i in rng.sample(range(12), 6):
        out.append("put B%d" % i)
    for i in range(10):
        out.append("get C%d %d" % (i, rng.choice([264, 320, 512, 64, 32])))
    for i in range(6):
        out.append("fit C%d %d" % (i, rng.choice([200, 264, 600, 1024, 40])))
    for i in range(6):
        out.append("put C%d" % i)
    for i in range(8):
        out.append("get D%d %d" % (i, rng.choice([264, 512, 1000, 16])))
    return out


def _mix(rng):
    out = _head(8192, 512)
    names = []
    for _ in range(220):
        r = rng.random()
        if r < 0.40 or not names:
            name = "z%d" % rng.randrange(50)
            out.append("get %s %d" % (name, rng.choice(
                [0, 8, 16, 24, 40, 56, 64, 96, 120, 248, 256, 264, 320, 504, 512, 600])))
            names.append(name)
        elif r < 0.70:
            out.append("put %s" % rng.choice(names))
        elif r < 0.92:
            out.append("fit %s %d" % (rng.choice(names), rng.choice(
                [8, 16, 32, 48, 64, 88, 120, 256, 264, 500])))
        else:
            out.append("sweep")
    return out


def _wide(rng):
    span, part = 4194304, 1024
    out = _head(span, part)
    hold = 0
    for i in range(46000):
        out.append("get L%d %d" % (i, rng.choice([24, 32, 40, 56, 64, 88, 120, 160, 200])))
        hold += 1
    for i in range(0, 46000, 3):
        out.append("put L%d" % i)
    live = []
    for step in range(60000):
        if live and (step % 3 == 2 or len(live) > 900):
            out.append("put %s" % live.pop(rng.randrange(len(live))))
        else:
            name = "H%d" % step
            out.append("get %s %d" % (name, rng.choice([264, 300, 360, 424, 512])))
            live.append(name)
        if step % 5 == 1:
            out.append("get S%d %d" % (step, rng.choice([16, 24, 32])))
        if step % 5 == 3:
            out.append("put S%d" % (step - 2))
    return out


def _churn(rng):
    span, part = 4194304, 1024
    out = _head(span, part)
    for i in range(52000):
        out.append("get K%d %d" % (i, rng.choice([24, 32, 40, 56, 64, 96])))
    for i in range(0, 52000, 2):
        out.append("put K%d" % i)
    live = ["K%d" % i for i in range(1, 52000, 2)]
    for step in range(40000):
        if step % 2 == 0:
            name = "T%d" % step
            out.append("get %s %d" % (name, rng.choice([24, 32, 40, 56, 64, 96, 120])))
            live.append(name)
        else:
            out.append("put %s" % live.pop(rng.randrange(len(live))))
        if step % 1499 == 0:
            out.append("sweep")
        if step % 313 == 7:
            out.append("get W%d %d" % (step, rng.choice([300, 512, 800])))
    return out


BUILD = {
    "plain": _plain,
    "press": _press,
    "again": _again,
    "sliv": _sliv,
    "edge": _edge,
    "full": _full,
    "grow": _grow,
    "move": _move,
    "big": _big,
    "mix": _mix,
    "wide": _wide,
    "churn": _churn,
}


def programs(seed, per):
    """Every graded nonce program, in a fixed order, from one seed."""
    out = []
    for fam, small in FAMILIES:
        count = per if small else BIG_EACH
        for i in range(count):
            rng = random.Random("%s|%s|%d" % (seed, fam, i))
            out.append((fam, "%s-%02d" % (fam, i), BUILD[fam](rng)))
    return out
