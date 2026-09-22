from lm import grant


def hard_edges(held, wait):
    edges = {}
    for txn, req in wait.of.items():
        edges[txn] = {u for u, t2, m2 in held.holders(txn)
                      if grant.clash(req.tgt, req.mode, t2, m2)}
    return edges


def on_cycle(edges, start):
    seen = set()
    todo = list(edges.get(start, ()))
    while todo:
        cur = todo.pop()
        if cur == start:
            return True
        if cur not in seen:
            seen.add(cur)
            todo.extend(edges.get(cur, ()))
    return False


def victim(held, wait):
    edges = hard_edges(held, wait)
    cyclic = [v for v in edges if on_cycle(edges, v)]
    if not cyclic:
        return None
    return max(cyclic, key=lambda v: int(v[1:]))
