"""The shed, popping a heap built when each bank is reached."""
import heapq


def shed(cfg, sc, bufs, st, z):
    for k in range(cfg.banks()):
        lo = k * cfg.bw
        hi = lo + cfg.bw
        load = sum(bufs.count(e) for e in range(lo, hi))
        if load <= z:
            continue
        pile = [(sc[tid][e], -e, -slot, tid)
                for e in range(lo, hi) for slot, tid in bufs.at(e).items()]
        heapq.heapify(pile)
        while load > z and pile:
            _s, nege, negslot, tid = heapq.heappop(pile)
            e = -nege
            slot = -negslot
            if bufs.at(e).get(slot) != tid:
                continue
            row = st.held(tid)
            r = row.index((e, slot))
            for ee, ss in row[r:]:
                if lo <= ee < hi:
                    load -= 1
                bufs.drop(ee, ss)
            del row[r:]
