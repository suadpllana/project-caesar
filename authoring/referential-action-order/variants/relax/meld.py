"""Variant: the links that reached a row are kept flat and merged once, by sorting."""


class Hit:
    __slots__ = ("gone", "cols")

    def __init__(self):
        self.gone = None
        self.cols = {}


def melt(edge, kind, tab, key, new):
    """One entry per row, keyed by the pair rather than nested by table."""
    rows = {}
    for seat in sorted(edge, key=lambda e: e[2]):
        ktab, ck, li = seat
        ci, act, val = edge[seat]
        here = rows.get((ktab, ck))
        if here is None:
            here = rows[(ktab, ck)] = Hit()
        if act == "drop":
            if here.gone is None:
                here.gone = li
        elif ci not in here.cols:
            here.cols[ci] = (act, val, li)
    here = rows.get((tab, key))
    if here is None:
        here = rows[(tab, key)] = Hit()
    if kind == "out":
        here.gone = -1
    else:
        here.cols[0] = ("follow", new, -1)
    return rows
