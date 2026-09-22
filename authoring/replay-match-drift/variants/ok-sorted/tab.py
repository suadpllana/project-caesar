"""Variant A: the history as queues, popped rather than indexed."""
from collections import deque


class Tab(object):
    def __init__(self, log):
        self.rows = []
        self.kinds = {}
        self.answers = {}
        self.sigs = {}
        self.chs = {}
        rank = {}
        for pos, (ev, args) in enumerate(log):
            if ev == "go":
                at = rank.get(args[0], 0)
                rank[args[0]] = at + 1
                self.kinds.setdefault(args[0], []).append((pos, args[1]))
                self.rows.append((pos, args[0], at))
            elif ev == "ok":
                self.answers.setdefault(args[0] + "|" + args[1], deque()).append(
                    (pos, int(args[2])))
            elif ev == "sig":
                self.sigs.setdefault(args[0], deque()).append((pos, int(args[1])))
            elif ev == "ch":
                self.chs.setdefault(args[0], deque()).append((pos, int(args[1])))

    def slot(self, kind, i):
        row = self.kinds.get(kind)
        if row is None or i >= len(row):
            return None
        return row[i]

    def answer(self, kind, name, j):
        row = self.answers.get(kind + "|" + name)
        if not row:
            return None
        return row.popleft()

    def signal(self, tag, j):
        row = self.sigs.get(tag)
        if not row:
            return None
        return row[0]

    def choice(self, key, j):
        row = self.chs.get(key)
        if not row:
            return None
        return row[0]

    def drop_signal(self, tag):
        self.sigs[tag].popleft()

    def drop_choice(self, key):
        self.chs[key].popleft()

    def issued(self):
        return self.rows
