"""Choosing and applying pending pairs until nothing is pending."""

from heapq import heapify, heappop, heappush

from scn import step

SH = 21
MASK = (1 << SH) - 1


def run(seg, q, st, out):
    mem = st.mem
    livech = st.livech
    cbase = mem.cbase
    ccol = mem.ccol
    colconds = st.colconds
    nch = len(mem.cobj)
    keys = st.key
    done = st.done
    cnts = st.cnt
    heap = []
    for cd in q.conds:
        pos = cd.pos
        c = cd.c
        key = [0] * nch
        dn = bytearray(nch)
        cnt = cnts[pos]
        g0 = cbase[c]
        for g in range(g0, g0 + len(seg.cols[c])):
            if step.pending(st, pos, g):
                lv = livech[g]
                ct = cnt[g]
                k = lv if lv < ct else ct
                key[g] = k
                heap.append((((k << SH) | pos) << SH) | g)
            else:
                dn[g] = 1
        keys[pos] = key
        done[pos] = dn
    heapify(heap)
    dirty = st.dirty
    dirty.clear()
    while heap:
        code = heappop(heap)
        g = code & MASK
        rest = code >> SH
        pos = rest & MASK
        k = rest >> SH
        dn = done[pos]
        if dn[g] or keys[pos][g] != k:
            continue
        dn[g] = 1
        if not step.pending(st, pos, g):
            continue
        step.apply(st, pos, g, out)
        if dirty:
            for g2 in dirty:
                lv = livech[g2]
                for pos2 in colconds[ccol[g2]]:
                    if done[pos2][g2]:
                        continue
                    ct = cnts[pos2][g2]
                    nk = lv if lv < ct else ct
                    kk = keys[pos2]
                    if nk != kk[g2]:
                        kk[g2] = nk
                        heappush(heap, (((nk << SH) | pos2) << SH) | g2)
            dirty.clear()
