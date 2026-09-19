#!/bin/bash
# equal gate scores rank by the larger expert index
set -euo pipefail

cat > /app/lay/gate.py <<'PYEOF'
"""Ranking, and the want list that placement rewrites.

The ranking of a token never changes during a step, so it is computed once and kept. The want
list does change: every expert that refuses the token is struck out, and the shortest prefix
reaching the threshold is taken again over what is left, which is generally longer than before
because the scores that used to carry the prefix over the line are gone.
"""


def rank(weight):
    """Experts by score descending, ties to the smaller index."""
    return sorted(range(len(weight)), key=lambda e: (-weight[e], -e))


def want(order, weight, w, out_of):
    """The shortest prefix of `order` minus `out_of` whose scores reach `w`.

    When what is left sums to less than the threshold the whole of it is wanted, which is the
    same rule read at its end rather than a separate case.
    """
    wl = []
    tot = 0
    for e in order:
        if e in out_of:
            continue
        wl.append(e)
        tot += weight[e]
        if tot >= w:
            break
    return wl
PYEOF

cat > /app/lay/cap.py <<'PYEOF'
"""Buffer sizing.

Buffers are allocated once for the whole step, before any token is placed, from what the first
microbatch asks for scaled up by the number of microbatches. The wants that deferral creates
later in the step therefore press against a size that was fixed before they existed.
"""


def slots(cfg, wanted, mbs):
    """Per-expert slots for the step, rounded up."""
    unit = 100 * cfg.ex
    return (cfg.f * wanted * mbs + unit - 1) // unit


def budget(cfg, c):
    """Placements a bank may still hold once the step is over, rounded up."""
    return (cfg.g * c * cfg.bw + 99) // 100
PYEOF

cat > /app/lay/buf.py <<'PYEOF'
"""Expert buffers, held as slots rather than as a count.

Two things free a slot in the middle of a step: a displacement takes away every placement the
occupant holds from that rank on, and the next arrival at that expert fills the lowest index
that is free rather than the next one never used. A counter cannot say either, so a buffer is
a slot map with the returned indices kept in order beside it.

The order over displaceable occupants is a heap with lazy deletion, and that is affordable
because of the step's own invariant: a token is displaced at most once, so an entry that has
stopped being valid can never become valid again and is thrown away the moment it surfaces.
Scanning the buffer for the weakest occupant is exactly as correct and is what the wide
programs are there to rule out.
"""
import heapq


class Bufs:
    __slots__ = ("c", "hold", "nxt", "back", "weak")

    def __init__(self, ex, c):
        self.c = c
        self.hold = [{} for _ in range(ex)]
        self.nxt = [0] * ex
        self.back = [[] for _ in range(ex)]
        self.weak = [[] for _ in range(ex)]

    def free(self, e):
        """The lowest free slot index of e, or None when the buffer is full."""
        if self.back[e]:
            return self.back[e][0]
        return self.nxt[e] if self.nxt[e] < self.c else None

    def fill(self, e, token, weight):
        """Put token in the lowest free slot. The caller has checked there is one."""
        if self.back[e]:
            slot = heapq.heappop(self.back[e])
        else:
            slot = self.nxt[e]
            self.nxt[e] += 1
        self.hold[e][slot] = token
        heapq.heappush(self.weak[e], (weight, -slot, token))
        return slot

    def seize(self, e, slot, token, weight):
        """Hand an occupied slot straight to token: the slot never becomes free."""
        self.hold[e][slot] = token
        heapq.heappush(self.weak[e], (weight, -slot, token))

    def drop(self, e, slot):
        del self.hold[e][slot]
        heapq.heappush(self.back[e], slot)

    def weakest(self, e, gone):
        """Lowest-scoring occupant not yet displaced this step, ties to the larger slot."""
        pile = self.weak[e]
        while pile:
            weight, negslot, token = pile[0]
            slot = -negslot
            if self.hold[e].get(slot) == token and not gone[token]:
                return weight, slot, token
            heapq.heappop(pile)
        return None

    def count(self, e):
        return len(self.hold[e])

    def at(self, e):
        return self.hold[e]
PYEOF

cat > /app/lay/back.py <<'PYEOF'
"""What a token carries through a step, and the queue that survives a microbatch.

Three of these are per token and none of them is a field on anything the service ships: the
experts that have refused it, whether it has already been displaced, and the want list as it
now stands. The queue holds only tokens that lost or never got rank zero, in the order the
losses happened, and it is emptied at the head of the next microbatch. The last microbatch has
no next one, so a loss there is simply held and nothing is printed for it.
"""


class Track:
    __slots__ = ("wl", "place", "blocked", "gone", "pending")

    def __init__(self, n):
        self.wl = [() for _ in range(n)]
        self.place = [[] for _ in range(n)]
        self.blocked = [set() for _ in range(n)]
        self.gone = [False] * n
        self.pending = []

    def take(self):
        held = self.pending
        self.pending = []
        return held

    def refuse(self, token, e):
        self.blocked[token].add(e)

    def defer(self, token, last, out):
        if last:
            return
        self.pending.append(token)
        out.line("def %d" % token)
PYEOF

cat > /app/lay/put.py <<'PYEOF'
"""The step: capacity, then the microbatch queues, then the shed, then the report.

A token is placed at the experts of its want list in rank order and stops at the first one it
cannot enter, so what it holds is always a prefix of that list. That is what makes a loss
total below the rank it happened at: the placements after it would no longer be a prefix, so
they go too, and their slots are free for whatever arrives next.

A full expert is not a closed door. The weakest occupant that has not already been displaced
this step leaves if the arrival outscores it there, and the arrival takes that exact slot
rather than the lowest free one, because the slot never became free.
"""
from lay import back, buf, cap, gate, tally, trim


def _ids(mbs):
    base = 0
    out = []
    for mb in mbs:
        out.append(list(range(base, base + len(mb))))
        base += len(mb)
    return out


def _first_wanted(cfg, mbs):
    """The wanted slots of the first microbatch, which is what the buffers are sized from."""
    if not mbs:
        return 0
    n = 0
    for weight in mbs[0]:
        n += len(gate.want(gate.rank(weight), weight, cfg.w, ()))
    return n


def _oust(bufs, st, weights, vt, e, last, out):
    """Take e away from vt, and with it every placement vt holds at a later rank."""
    where = st.place[vt]
    r = 0
    while where[r][0] != e:
        r += 1
    for ee, ss in where[r + 1:]:
        bufs.drop(ee, ss)
    st.place[vt] = where[:r]
    st.gone[vt] = True
    st.refuse(vt, e)
    if r == 0:
        st.defer(vt, last, out)


def _admit(cfg, weights, order, bufs, st, token, last, out):
    wl = gate.want(order[token], weights[token], cfg.w, st.blocked[token])
    st.wl[token] = wl
    held = []
    for e in wl:
        weight = weights[token][e]
        slot = bufs.free(e)
        if slot is None:
            weak = bufs.weakest(e, st.gone)
            if weak is None or weak[0] >= weight:
                st.refuse(token, e)
                break
            _oust(bufs, st, weights, weak[2], e, last, out)
            bufs.seize(e, weak[1], token, weight)
            held.append((e, weak[1]))
            continue
        held.append((e, bufs.fill(e, token, weight)))
    st.place[token] = held
    if wl and not held:
        st.defer(token, last, out)


def step(cfg, mbs, out):
    weights = []
    for mb in mbs:
        weights.extend(mb)
    n = len(weights)
    order = [gate.rank(weight) for weight in weights]

    c = cap.slots(cfg, _first_wanted(cfg, mbs), len(mbs))
    z = cap.budget(cfg, c)
    out.line("cap %d %d" % (c, z))

    st = back.Track(n)
    bufs = buf.Bufs(cfg.ex, c)

    groups = _ids(mbs)
    for m, group in enumerate(groups):
        last = m == len(groups) - 1
        for token in st.take() + group:
            _admit(cfg, weights, order, bufs, st, token, last, out)

    trim.shed(cfg, weights, bufs, st, z)
    tally.report(cfg, weights, bufs, st, out, n)
PYEOF

cat > /app/lay/trim.py <<'PYEOF'
"""The bank shed, once the step is over.

A bank holds fewer placements than its experts' buffers together can, so the step can end over
budget. Banks are walked in index order and the weakest placement leaves until the bank fits,
and with it every placement its token holds at a later rank - which is how a removal in one
bank lowers the load of a later one. That is also why the banks that have to shed cannot be
listed before shedding starts: the list is only true of the state it was read from.

The order inside a bank is built when the bank is reached, so it already reflects what earlier
banks took away, and stale entries are skipped rather than removed.
"""
import heapq


def _load(cfg, bufs, lo):
    n = 0
    for e in range(lo, lo + cfg.bw):
        n += bufs.count(e)
    return n


def shed(cfg, weights, bufs, st, z):
    for k in range(cfg.banks()):
        lo = k * cfg.bw
        n = _load(cfg, bufs, lo)
        if n <= z:
            continue
        pile = []
        for e in range(lo, lo + cfg.bw):
            for slot, token in bufs.at(e).items():
                pile.append((weights[token][e], -e, -slot, token))
        heapq.heapify(pile)
        while n > z and pile:
            _s, nege, negslot, token = heapq.heappop(pile)
            e = -nege
            slot = -negslot
            if bufs.at(e).get(slot) != token:
                continue
            where = st.place[token]
            r = 0
            while where[r] != (e, slot):
                r += 1
            for ee, ss in where[r:]:
                bufs.drop(ee, ss)
                if lo <= ee < lo + cfg.bw:
                    n -= 1
            st.place[token] = where[:r]
PYEOF

cat > /app/lay/tally.py <<'PYEOF'
"""What the step reports once the shed has run.

The residual of a token is what its want list asked for and did not get, so it is read off the
want list as it finally stands rather than off the ranking or off the list the token started
with - a deferred token's list is not the one it was first given.

The balance number pairs demand with supply: for each expert, how many tokens finally wanted
it against how many placements it kept. Demand is not the count taken before placement began,
because being refused makes a token want more.
"""


def report(cfg, weights, bufs, st, out, n):
    wanted = [0] * cfg.ex
    for token in range(n):
        where = st.place[token]
        got = set(e for e, _slot in where)
        res = 0
        for e in st.wl[token]:
            wanted[e] += 1
            if e not in got:
                res += weights[token][e]
        parts = " ".join("%d:%d" % (e, slot) for e, slot in where)
        if parts:
            out.line("tok %d %s res %d" % (token, parts, res))
        else:
            out.line("tok %d res %d" % (token, res))

    bal = 0
    for e in range(cfg.ex):
        bal += wanted[e] * bufs.count(e)
    out.line("bal %d" % bal)
PYEOF
