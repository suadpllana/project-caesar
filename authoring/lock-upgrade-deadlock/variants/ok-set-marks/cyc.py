def onloop(rel, roots):
    """Transactions lying on a cycle of `rel` that passes through one of `roots`.

    The settle loop leaves the relation acyclic, so a cycle can only have appeared
    through an edge that changed since; every such cycle lies inside the subgraph
    reachable from the transaction whose edges changed. Tarjan over that subgraph.
    """
    seen = set()
    out = []
    for start in roots:
        if start in seen or start not in rel:
            continue
        out.extend(_scc(rel, start, seen))
    return out


def _scc(rel, start, seen):
    idx = {}
    low = {}
    on = set()
    stack = []
    work = [(start, iter(rel.get(start, ())))]
    idx[start] = low[start] = 0
    stack.append(start)
    on.add(start)
    seen.add(start)
    n = 1
    big = []
    while work:
        node, it = work[-1]
        step = next(it, None)
        if step is not None:
            if step not in idx:
                idx[step] = low[step] = n
                n += 1
                stack.append(step)
                on.add(step)
                seen.add(step)
                work.append((step, iter(rel.get(step, ()))))
            elif step in on:
                if idx[step] < low[node]:
                    low[node] = idx[step]
            continue
        work.pop()
        if work:
            up = work[-1][0]
            if low[node] < low[up]:
                low[up] = low[node]
        if low[node] == idx[node]:
            part = []
            while True:
                m = stack.pop()
                on.discard(m)
                part.append(m)
                if m == node:
                    break
            if len(part) > 1:
                big.extend(part)
    return big


def pick(txs):
    """The transaction a cut takes: fewest items held, then the later request, then the
    larger number."""
    best = None
    for t in txs:
        key = (t.nk, -t.req.seq, -t.num)
        if best is None or key < best[0]:
            best = (key, t)
    return best[1]
