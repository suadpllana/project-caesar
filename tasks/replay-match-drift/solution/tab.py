"""The recorded log, indexed once on the axes the rules actually count on.

Two different counters decide two different things, and the whole task turns on their
being different:

  * a command is matched to a recorded `go` by its position among the `go` events OF ITS
    OWN KIND, so `go` is a dict keyed by kind;
  * an answer is paired with a command by their positions among the events of that KIND
    AND NAME together, so `ok` is a dict keyed by the pair.

Everything is built in one pass over the log because the log is fixed before the body
starts. That is the invariant the execution limit rests on: the shipped service looks the
answer up by walking the log for every command, which stays exactly correct and cannot
finish the wide programs.
"""


class Tab(object):
    def __init__(self, log):
        self.go = {}
        self.ok = {}
        self.sig = {}
        self.ch = {}
        self.order = []
        seen = {}
        for pos, (ev, args) in enumerate(log):
            if ev == "go":
                kind = args[0]
                at = seen.get(kind, 0)
                seen[kind] = at + 1
                self.go.setdefault(kind, []).append((pos, args[1]))
                self.order.append((pos, kind, at))
            elif ev == "ok":
                self.ok.setdefault((args[0], args[1]), []).append((pos, int(args[2])))
            elif ev == "sig":
                self.sig.setdefault(args[0], []).append((pos, int(args[1])))
            elif ev == "ch":
                self.ch.setdefault(args[0], []).append((pos, int(args[1])))

    def slot(self, kind, i):
        row = self.go.get(kind)
        if row is None or i >= len(row):
            return None
        return row[i]

    def answer(self, kind, name, j):
        row = self.ok.get((kind, name))
        if row is None or j >= len(row):
            return None
        return row[j]

    def signal(self, tag, j):
        row = self.sig.get(tag)
        if row is None or j >= len(row):
            return None
        return row[j]

    def choice(self, key, j):
        row = self.ch.get(key)
        if row is None or j >= len(row):
            return None
        return row[j]

    def issued(self):
        return self.order
