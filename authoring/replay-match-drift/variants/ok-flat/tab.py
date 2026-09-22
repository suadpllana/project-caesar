"""Variant B: one pass into flat arrays, every lookup a bisect-free direct index."""


class Tab(object):
    def __init__(self, log):
        self.go_pos = []
        self.go_kind = []
        self.go_name = []
        self.go_rank = []
        self.kind_rows = {}
        self.ok_rows = {}
        self.sig_rows = {}
        self.ch_rows = {}
        counted = {}
        for pos in range(len(log)):
            ev, args = log[pos]
            if ev == "go":
                kind = args[0]
                rank = counted.get(kind, 0)
                counted[kind] = rank + 1
                self.kind_rows.setdefault(kind, []).append(len(self.go_pos))
                self.go_pos.append(pos)
                self.go_kind.append(kind)
                self.go_name.append(args[1])
                self.go_rank.append(rank)
            elif ev == "ok":
                self.ok_rows.setdefault((args[0], args[1]), []).append((pos, int(args[2])))
            elif ev == "sig":
                self.sig_rows.setdefault(args[0], []).append((pos, int(args[1])))
            elif ev == "ch":
                self.ch_rows.setdefault(args[0], []).append((pos, int(args[1])))

    def slot(self, kind, i):
        rows = self.kind_rows.get(kind)
        if rows is None or i >= len(rows):
            return None
        at = rows[i]
        return self.go_pos[at], self.go_name[at]

    def answer(self, kind, name, j):
        rows = self.ok_rows.get((kind, name))
        if rows is None or j >= len(rows):
            return None
        return rows[j]

    def signal(self, tag, j):
        rows = self.sig_rows.get(tag)
        if rows is None or j >= len(rows):
            return None
        return rows[j]

    def choice(self, key, j):
        rows = self.ch_rows.get(key)
        if rows is None or j >= len(rows):
            return None
        return rows[j]

    def issued(self):
        return [(self.go_pos[at], self.go_kind[at], self.go_rank[at])
                for at in range(len(self.go_pos))]

    def total_go(self):
        return len(self.go_pos)

    def rank_of(self, at):
        return self.go_kind[at], self.go_rank[at]
