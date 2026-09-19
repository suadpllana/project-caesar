import heapq


def _load(cfg, bufs, lo):
    n = 0
    for e in range(lo, lo + cfg.bw):
        n += bufs.count(e)
    return n


def shed(cfg, weights, bufs, st, z):
    over = []
    for k in range(cfg.banks()):
        lo = k * cfg.bw
        n = _load(cfg, bufs, lo)
        if n > z:
            over.append((lo, n))

    for lo, n in over:
        pile = []
        for e in range(lo, lo + cfg.bw):
            for slot, token in bufs.at(e).items():
                pile.append((weights[token][e], -e, -slot, token))
        heapq.heapify(pile)
        while n > z and pile:
            _s, nege, negslot, token = heapq.heappop(pile)
            e = -nege
            slot = -negslot
            bufs.drop(e, slot)
            st.place[token] = [p for p in st.place[token] if p != (e, slot)]
            n -= 1
