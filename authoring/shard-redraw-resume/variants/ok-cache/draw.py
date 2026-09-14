"""A correct variant that memoises the inverse and the order it has already evaluated.

Same answers, different bookkeeping. Positions and their samples are cached both ways for the
epoch and rank count in force, so a walk that goes back over ground pays for it once. Nothing
about an epoch is materialised: the caches hold only what the run has actually looked at.
"""

from rig import shuf

_FWD = {}
_REV = {}


def _key(run, st):
    return (run.seed, st["epoch"], st["rank"], run.rows)


def at(run, epoch, rank, pos):
    key = (run.seed, epoch, rank, run.rows)
    box = _FWD.setdefault(key, {})
    got = box.get(pos)
    if got is None:
        got = box[pos] = shuf.at(run.seed, epoch, rank, run.rows, pos)
        _REV.setdefault(key, {})[got] = pos
    return got


def back(run, epoch, rank, x):
    key = (run.seed, epoch, rank, run.rows)
    box = _REV.setdefault(key, {})
    got = box.get(x)
    if got is not None:
        return got
    half, mask, salt = shuf._setup(run.seed, epoch, rank, run.rows)
    y = x
    while True:
        lo = y & mask
        hi = y >> half
        for rnd in (3, 2, 1, 0):
            hi, lo = lo ^ (shuf._mix(salt + (hi << 6) + rnd) & mask), hi
        y = (hi << half) | lo
        if y < run.rows:
            box[x] = y
            return y


def fed(run, st, x):
    for rank, head in st["seen"].items():
        if head and back(run, st["epoch"], rank, x) < head:
            return True
    return False


def window(run, st, wide):
    rank = st["rank"]
    pos = st["seen"].get(rank, 0)
    got = []
    while len(got) < wide:
        x = at(run, st["epoch"], rank, pos)
        pos += 1
        if not fed(run, st, x):
            got.append(x)
    st["seen"][rank] = pos
    st["fed"] += wide
    return got


def deal(run, st, got):
    micro = run.micro
    lanes = [[] for _ in range(st["rank"])]
    for c in range(len(got) // micro):
        lanes[c % st["rank"]].extend(got[c * micro:(c + 1) * micro])
    return lanes
