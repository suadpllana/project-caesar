"""Which pending pair is applied next.

A condition and a chunk of its column are pending while a live row takes its
value from one of the chunk's pages without the condition settled for it.  The
pair applied next is the one expected to leave the fewest rows alive: the
smaller of the live rows the chunk holds and the count of the condition on it.
Ties go to the condition written earlier, then to the lower chunk number.
"""

from heapq import heapify, heappop, heappush

from scn import step


def run(seg, q, st, out):
    st.out = out
    U = st.U
    cnt = st.cnt
    ccol = st.ccol
    livech = st.livech
    last = []
    heap = []
    for i in range(len(ccol)):
        lc = livech[ccol[i]]
        ci = cnt[i]
        Ui = U[i]
        row = []
        for j in range(len(Ui)):
            k = lc[j] if lc[j] < ci[j] else ci[j]
            row.append(k)
            if Ui[j] > 0:
                heap.append((k, i, j))
        last.append(row)
    heapify(heap)
    dirty = st.dirty
    colconds = st.colconds
    for c in dirty:
        dirty[c].clear()
    while heap:
        k, i, j = heappop(heap)
        if U[i][j] <= 0:
            continue
        a = livech[ccol[i]][j]
        b = cnt[i][j]
        if k != (a if a < b else b):
            continue
        step.apply(st, i, j, out)
        for c, js in dirty.items():
            if not js:
                continue
            lc = livech[c]
            for i2 in colconds[c]:
                Ui = U[i2]
                ci = cnt[i2]
                li = last[i2]
                for j2 in js:
                    if Ui[j2] > 0:
                        a = lc[j2]
                        b = ci[j2]
                        nk = a if a < b else b
                        if nk != li[j2]:
                            li[j2] = nk
                            heappush(heap, (nk, i2, j2))
            js.clear()
