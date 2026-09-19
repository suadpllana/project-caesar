"""What one row ends up taking, when several links reach it.

Two rules, and the second is only reachable because nothing is applied while the reach runs:
a row taken out ignores every effect on its columns, and where more than one link acts on one
column, or takes the same row out, the one declared first decides. The link a row was reached
through first is not the one that decides it - the reach walks tables in an order that has
nothing to do with declaration order, so the smallest index has to win explicitly.
"""


class Hit:
    __slots__ = ("gone", "cols")

    def __init__(self):
        self.gone = None
        self.cols = {}


class Meld:
    __slots__ = ("rows",)

    def __init__(self):
        self.rows = {}

    def at(self, tab, key):
        by = self.rows.setdefault(tab, {})
        here = by.get(key)
        if here is None:
            here = by[key] = Hit()
        return here

    def drop(self, tab, key, li):
        here = self.at(tab, key)
        if here.gone is None or li < here.gone:
            here.gone = li

    def col(self, tab, key, ci, kind, val, li):
        here = self.at(tab, key)
        now = here.cols.get(ci)
        if now is None or li < now[2]:
            here.cols[ci] = (kind, val, li)

    def newkey(self, tab, key):
        here = self.rows.get(tab, {}).get(key)
        if here is None or here.gone is not None:
            return None
        got = here.cols.get(0)
        if got is None or got[0] != "move":
            return None
        return got[1]
