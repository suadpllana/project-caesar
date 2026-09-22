# Correct variant "packed": the walk over numbered inner nodes, grouped by printed entry.


def agree(first, out, audit, good, ends):
    """first: start ids; good: ids on a path that completes the journal; ends: ids that
    may leave the span with the rest of the journal still completable."""
    here = {k for k in first if k in good}
    restored = []
    while True:
        grow = list(here)
        while grow:
            k = grow.pop()
            for m in audit[k]:
                if m in good and m not in here:
                    here.add(m)
                    grow.append(m)
        by = {}
        stop = False
        for k in here:
            if k in ends:
                stop = True
            for label, e, m in out[k]:
                if m in good:
                    by.setdefault(label, (e, set()))[1].add(m)
        if len(by) == 1 and not stop:
            label, (e, nxt) = by.popitem()
            restored.append(e)
            here = nxt
            continue
        cands = [e for e, _m in by.values()]
        if stop and cands:
            cands.append(None)
        return restored, cands
