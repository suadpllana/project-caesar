import heapq
from itertools import groupby

from plan.span import ends


def order(pp, settled):
    m, emit, holds = settled

    def when(k):
        return ends(pp, *k)

    rows = []
    for _end, group in groupby(sorted(emit, key=when), key=when):
        group = list(group)
        inside = set(group)
        need = {k: {d for d in m.memo[k]["deps"] if d in inside} for k in group}
        ready = [(pp.pos[k[0]], k) for k in group if not need[k]]
        heapq.heapify(ready)
        while ready:
            _, k = heapq.heappop(ready)
            v = m.memo[k]
            rows.append(("temp", k[0], k[1]) if v["kind"] == "temp" else ("run", k[0], k[1], v["why"]))
            for u in group:
                if k in need[u]:
                    need[u].discard(k)
                    if not need[u]:
                        heapq.heappush(ready, (pp.pos[u[0]], u))
    for k in sorted(holds, key=lambda k: (when(k), pp.pos[k[0]])):
        rows.append(("hold", k[0], k[1], m.memo[k]["why"]))
    return rows
