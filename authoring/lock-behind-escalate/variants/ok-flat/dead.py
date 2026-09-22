from lm import grant

WHITE, GREY, BLACK = 0, 1, 2


def on_cycle(rel):
    """Nodes on a cycle of the relation, by a three-colour walk: a back edge closes a cycle
    and every node between its two ends is on it."""
    colour = {v: WHITE for v in rel}
    found = set()
    for root in rel:
        if colour[root] != WHITE:
            continue
        path = [root]
        colour[root] = GREY
        iters = {root: iter(rel[root])}
        while path:
            v = path[-1]
            for u in iters[v]:
                if u not in rel:
                    continue
                if colour[u] == WHITE:
                    colour[u] = GREY
                    path.append(u)
                    iters[u] = iter(rel[u])
                    break
                if colour[u] == GREY:
                    found.update(path[path.index(u):])
            else:
                colour[v] = BLACK
                path.pop()
    return found


def pick(held, wait):
    cyclic = on_cycle(grant.relation(held, wait, soft=False))
    if not cyclic:
        return None
    return min(cyclic, key=lambda t: (held.count(t), -wait.pending[t].seq))
