"""The bank shed, walking a list sorted once rather than popping a heap."""


def shed(cfg, sc, bufs, st, z):
    for k in range(cfg.banks()):
        lo = k * cfg.bw
        hi = lo + cfg.bw
        load = 0
        for e in range(lo, hi):
            load += bufs.count(e)
        if load <= z:
            continue
        row = []
        for e in range(lo, hi):
            for slot, tid in bufs.at(e).items():
                row.append((sc[tid][e], -e, -slot, tid))
        row.sort()
        at = 0
        while load > z and at < len(row):
            _s, nege, negslot, tid = row[at]
            at += 1
            e = -nege
            slot = -negslot
            if bufs.at(e).get(slot) != tid:
                continue
            experts, slots = st.place[tid]
            r = 0
            while not (experts[r] == e and slots[r] == slot):
                r += 1
            for i in range(r, len(experts)):
                if lo <= experts[i] < hi:
                    load -= 1
                bufs.drop(experts[i], slots[i])
            del experts[r:]
            del slots[r:]
