def onloop(rel, roots):
    """Every transaction on a ring of `rel`, by Kosaraju over the whole relation. `roots`
    is accepted for the interface and ignored: this variant searches everything, every time."""
    order = []
    seen = set()
    for start in rel:
        if start in seen:
            continue
        seen.add(start)
        work = [(start, iter(rel.get(start, ())))]
        while work:
            node, kids = work[-1]
            nxt = next(kids, None)
            if nxt is None:
                work.pop()
                order.append(node)
            elif nxt not in seen:
                seen.add(nxt)
                work.append((nxt, iter(rel.get(nxt, ()))))
    back = {}
    for a, bs in rel.items():
        for b in bs:
            back.setdefault(b, []).append(a)
    done = set()
    out = []
    for start in reversed(order):
        if start in done:
            continue
        part = []
        work = [start]
        done.add(start)
        while work:
            node = work.pop()
            part.append(node)
            for prev in back.get(node, ()):
                if prev not in done and prev in rel:
                    done.add(prev)
                    work.append(prev)
        if len(part) > 1:
            out.extend(part)
    return out


def pick(txs):
    best = None
    for t in txs:
        key = (t.nk, -t.req.seq, -t.num)
        if best is None or key < best[0]:
            best = (key, t)
    return best[1]
