import heapq

from plan.span import ends


def order(pp, settled):
    s, out, holds = settled
    rank = {k: (ends(pp, *k), pp.pos[k[0]]) for k in out}
    count = {k: 0 for k in out}
    after = {}
    for k in out:
        for d in set(s.nodes[k].before):
            if d in out:
                count[k] += 1
                after.setdefault(d, []).append(k)
    heap = [(rank[k], k) for k in out if count[k] == 0]
    heapq.heapify(heap)
    rows = []
    while heap:
        _, k = heapq.heappop(heap)
        n = s.nodes[k]
        rows.append(("run", k[0], k[1], n.word) if n.line == "run" else ("temp", k[0], k[1]))
        for u in after.get(k, ()):
            count[u] -= 1
            if count[u] == 0:
                heapq.heappush(heap, (rank[u], u))
    holds.sort(key=lambda k: (ends(pp, *k), pp.pos[k[0]]))
    rows.extend(("hold", k[0], k[1], s.nodes[k].word) for k in holds)
    return rows
