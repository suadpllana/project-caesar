"""Variant: the links that reached a row are gathered per row and sorted there."""


def melt(hits, kind, tab, key, new):
    by = {}
    for (seat, li), (ci, act, val) in hits.items():
        by.setdefault(seat, []).append((li, ci, act, val))
    rows = {}
    for seat, got in by.items():
        got.sort()
        gone = None
        cols = {}
        for li, ci, act, val in got:
            if act == "drop":
                if gone is None:
                    gone = li
            elif ci not in cols:
                cols[ci] = (act, val, li)
        rows[seat] = (gone, cols)
    gone, cols = rows.get((tab, key), (None, {}))
    if kind == "out":
        rows[(tab, key)] = (-1, cols)
    else:
        cols = dict(cols)
        cols[0] = ("follow", new, -1)
        rows[(tab, key)] = (None, cols)
    return rows
