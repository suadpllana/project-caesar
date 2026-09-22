"""Variant B: one list per branch, reached through a list of lists indexed by branch number.

An earlier shape of this file kept every branch's untaken commands in one flat list and walked
it. That is correct and it measured 19.4 s on the six scale run files against 2.7 for the
reference, which is inside the 60 s limit and is recorded in STATE.md as the headroom a poor but
correct auxiliary structure has.
"""


class Hold(object):
    def __init__(self):
        self.rows = []

    def add(self, bid, rec):
        while len(self.rows) <= bid:
            self.rows.append([])
        self.rows[bid].append(rec)

    def first(self, bid):
        if bid >= len(self.rows) or not self.rows[bid]:
            return None
        return self.rows[bid][0]

    def drop(self, bid, rec):
        if bid >= len(self.rows):
            return
        row = self.rows[bid]
        for at in range(len(row)):
            if row[at] is rec:
                row.pop(at)
                return
