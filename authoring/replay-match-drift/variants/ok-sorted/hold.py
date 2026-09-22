"""Variant A: a deque of untaken commands per branch."""
from collections import deque


class Hold(object):
    def __init__(self):
        self.rows = {}

    def add(self, bid, rec):
        self.rows.setdefault(bid, deque()).append(rec)

    def first(self, bid):
        row = self.rows.get(bid)
        if not row:
            return None
        return row[0]

    def drop(self, bid, rec):
        row = self.rows.get(bid)
        if not row:
            return
        keep = deque(one for one in row if one is not rec)
        self.rows[bid] = keep
