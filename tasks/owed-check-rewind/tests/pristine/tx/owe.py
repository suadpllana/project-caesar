from tx import chk


class Owe:
    def __init__(self, cat, heap):
        self.cat = cat
        self.heap = heap
        self.cur = []

    def reset(self):
        self.cur = []

    def now(self, modes):
        out = []
        for con in self.cat.cons:
            if modes.get(con.name) == "d":
                for k in chk.scan(self.cat, self.heap, con):
                    out.append((con.name, con.table, k))
        return out

    def redo(self, modes):
        new = self.now(modes)
        gone = [e for e in self.cur if e not in new]
        came = [e for e in new if e not in self.cur]
        self.cur = new
        return gone, came
