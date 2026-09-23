"""Which pending pair of a condition and a chunk is applied next.

A condition and a chunk of its column are pending while the condition has not
been applied to the chunk and the chunk still holds a live row.  The next pair
is the one expected to leave the fewest rows alive: the smaller of the live rows
the chunk holds and the count of the condition on it, ties to the condition
written earlier, then to the lower chunk number.
"""

from heapq import heappop

from scn import step


def run(seg, q, st, out):
    heap = st.heap
    conds = q.conds
    done = st.done
    key = st.key
    live = st.live
    while heap:
        k, pos, j = heappop(heap)
        if done[pos][j] or key[pos][j] != k:
            continue
        cd = conds[pos]
        if live[cd.c][j] <= 0:
            continue
        done[pos][j] = 1
        step.apply(st, cd, j, out)
