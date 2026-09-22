"""Variant A: the log as queues. Answers come off a deque per kind and name."""
from collections import deque


class Tab(object):
    def __init__(self, log):
        self.rows = []
        self.by_kind = {}
        self.answers = {}
        self.signals = {}
        self.choices = {}
        rank = {}
        for pos, (ev, args) in enumerate(log):
            if ev == "go":
                at = rank.get(args[0], 0)
                rank[args[0]] = at + 1
                self.by_kind.setdefault(args[0], []).append((pos, args[1]))
                self.rows.append((pos, args[0], at))
            elif ev == "ok":
                self.answers.setdefault(args[0] + "\x00" + args[1], deque()).append(
                    (pos, int(args[2])))
            elif ev == "sig":
                self.signals.setdefault(args[0], deque()).append((pos, int(args[1])))
            elif ev == "ch":
                self.choices.setdefault(args[0], deque()).append((pos, int(args[1])))

    def slot(self, kind, i):
        row = self.by_kind.get(kind)
        if row is None or i >= len(row):
            return None
        return row[i]

    def answer(self, kind, name, j):
        row = self.answers.get(kind + "\x00" + name)
        if not row:
            return None
        return row.popleft()

    def signal(self, tag, j):
        row = self.signals.get(tag)
        if not row:
            return None
        return row[0]

    def choice(self, key, j):
        row = self.choices.get(key)
        if not row:
            return None
        return row[0]

    def drop_signal(self, tag):
        self.signals[tag].popleft()

    def drop_choice(self, key):
        self.choices[key].popleft()

    def issued(self):
        return self.rows
