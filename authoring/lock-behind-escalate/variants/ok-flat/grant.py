NEWEST = float("inf")


def relation(held, wait, soft=True):
    """Every waiting transaction to the set it waits on: holders, and earlier waiters if soft."""
    out = {}
    for req in wait.pending.values():
        on = set(held.against(req.txn, req.tgt, req.mode))
        if soft:
            on |= wait.ahead_of(req.txn, req.tgt, req.mode, req.seq)
        out[req.txn] = on
    return out


def closure(rel):
    """Transitive reach of every node, by Tarjan's components in postorder, as sets."""
    reach = {}
    number = {}
    low = {}
    stack = []
    on_stack = set()
    tick = [0]

    def visit(v):
        number[v] = low[v] = tick[0]
        tick[0] += 1
        stack.append(v)
        on_stack.add(v)
        for u in rel.get(v, ()):
            if u not in rel:
                continue
            if u not in number:
                visit(u)
                low[v] = min(low[v], low[u])
            elif u in on_stack:
                low[v] = min(low[v], number[u])
        if low[v] == number[v]:
            members = []
            while True:
                u = stack.pop()
                on_stack.discard(u)
                members.append(u)
                if u == v:
                    break
            got = set(members) if len(members) > 1 else set()
            for u in members:
                for w in rel[u]:
                    got.add(w)
                    got |= reach.get(w, set())
            for u in members:
                reach[u] = got

    for v in rel:
        if v not in number:
            visit(v)
    return reach


def admissible(held, wait, txn, tgt, mode, seq, reach=None):
    if held.against(txn, tgt, mode):
        return False
    ahead = wait.ahead_of(txn, tgt, mode, seq)
    if not ahead:
        return True
    if reach is None:
        reach = closure(relation(held, wait))
    return all(txn in reach.get(u, ()) for u in ahead)
