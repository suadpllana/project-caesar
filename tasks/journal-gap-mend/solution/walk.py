# Reference walk of one span: what every account agrees on, and where they first part.


def _through(here, edges, live):
    """Close a set of inner nodes over audit steps: an audit may sit anywhere."""
    out = set(here)
    todo = list(here)
    while todo:
        node = todo.pop()
        for entry, nxt in edges[node]:
            if entry is None and nxt in live and nxt not in out:
                out.add(nxt)
                todo.append(nxt)
    return out


def agree(starts, edges, exits, live, after):
    """Restored entries and the candidates at the first disagreement (None = the span ends
    here), over the inner nodes that can still complete the journal."""
    here = {(t, s, 0) for t, s in starts if (t, s, 0) in live}
    restored = []
    while True:
        here = _through(here, edges, live)
        cands = {}
        for node in here:
            if node in exits and node[:2] in after:
                cands.setdefault(None, set())
            for entry, nxt in edges[node]:
                if entry is not None and nxt in live:
                    cands.setdefault(entry, set()).add(nxt)
        if len(cands) == 1 and None not in cands:
            entry, here = cands.popitem()
            restored.append(entry)
            continue
        return restored, ([] if list(cands) == [None] else list(cands))
