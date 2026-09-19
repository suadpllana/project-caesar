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
