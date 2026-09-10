"""What a volume holds, for how long, and what that leaves behind.

A volume's hold on one block is an episode: it opens when the first slot of that volume takes the
block and closes when the last one lets it go. A block may be held at several slots of one volume
at once, and may be taken back after it has left, so a block has a series of episodes per volume
rather than one stretch of time.

A closed episode leaves a run: the pegs of that volume whose stamps fall inside it. What has to be
known about a run is only whether it stands for no keeper, one keeper or more, so a run carries the
two youngest living pegs it covers. No keeper means the run is gone; one keeper means the second of
the two is missing. Both change only when one of those two pegs is shed, which is what keeps a shed
off every run that merely contains it.
"""
from keep import cover

B, V, T1, T2, HI, PEN, OK = range(7)


class Acct:
    def __init__(self):
        self.t = 0
        self.roll = []
        self.made = {}
        self.hn = {}
        self.op = {}
        self.nh = {}
        self.rs = {}
        self.sof = {}
        self.sole = {}
        self.stop = {}
        self.fresh = []
        self.q = []
        self.out = set()
        self.pt = {}
        self.pn = {}
        self.nf = {}
        self.pf = {}
        self.home = {}
        self.hi_at = {}
        self.pen_at = {}


def new():
    return Acct()


def born(a, b, t):
    a.t = t
    a.roll.append(b)
    a.made[b] = t
    a.nh[b] = 0
    a.rs[b] = []


def hold(a, v, x, b, t):
    a.t = t
    k = (b, v)
    n = a.hn.get(k, 0)
    if n == 0:
        a.op[k] = t
        a.nh[b] += 1
        if a.nh[b] == 1:
            touch(a, b, t)
    a.hn[k] = n + 1


def free(a, v, x, b, t):
    a.t = t
    k = (b, v)
    n = a.hn[k] - 1
    if n:
        a.hn[k] = n
        return
    del a.hn[k]
    shut(a, b, v, a.op.pop(k), t)
    a.nh[b] -= 1
    touch(a, b, t)
    flush(a)


def shut(a, b, v, t1, t2):
    """File the run this closed episode leaves under the two youngest pegs it covers."""
    hi = cover.last(a, v, t1, t2)
    if hi is None:
        return
    r = [b, v, t1, t2, hi, cover.under(a, v, hi, t1), True]
    a.rs[b].append(r)
    file(a, r)


def file(a, r):
    a.hi_at.setdefault(a.pn[r[V]][r[HI]], []).append(r)
    if r[PEN] is not None:
        a.pen_at.setdefault(a.pn[r[V]][r[PEN]], []).append(r)


def kill(a, r):
    r[OK] = False
    a.rs[r[B]].remove(r)


def touch(a, b, t):
    """Settle whether the block is kept at all, and whether one peg alone keeps it."""
    rs = a.rs[b]
    held = a.nh[b]
    if not held and not rs and b not in a.stop:
        a.stop[b] = t
        a.fresh.append(b)
    one = None
    if not held and len(rs) == 1 and rs[0][PEN] is None:
        r = rs[0]
        one = a.pn[r[V]][r[HI]]
    was = a.sof.get(b)
    if was != one:
        if was is not None:
            a.sole[was] -= 1
        if one is not None:
            a.sole[one] = a.sole.get(one, 0) + 1
        a.sof[b] = one


def flush(a):
    """Blocks that stopped being kept during one op join the queue in allocation order."""
    if a.fresh:
        a.fresh.sort()
        a.q.extend(a.fresh)
        del a.fresh[:]
