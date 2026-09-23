"""Apply pending pairs, always the one expected to leave the fewest rows
alive, until nothing is pending."""

from heapq import heappop, heappush

from scn import step


def run(seg, q, st, out):
    heap = st.heap
    pend = st.pend
    ckey = st.ckey
    cnt = st.cnt
    livech = st.livech
    ccond = st.ccond
    while heap:
        key, i, j = heappop(heap)
        if pend[i][j] <= 0 or ckey[i][j] != key:
            continue
        dirty = st.dirty = set()
        step.apply(st, i, j, out)
        for c, jj in dirty:
            lc = livech[c][jj]
            for i2 in ccond[c]:
                if pend[i2][jj] > 0:
                    k2 = cnt[i2][jj]
                    if lc < k2:
                        k2 = lc
                    if k2 != ckey[i2][jj]:
                        ckey[i2][jj] = k2
                        heappush(heap, (k2, i2, jj))
