from tx import chk
from tx.act import Act
from tx.heap import Heap
from tx.owe import Owe
from tx.sp import Sp


class Session:
    def __init__(self, cat, rows):
        self.cat = cat
        self.heap = Heap(cat, rows)
        self.act = Act(cat, self.heap)
        self.owe = Owe(cat, self.heap)
        self.sp = Sp(self.heap)
        self.base = None
        self.modes = {}
        self.dead = False

    def step(self, st):
        op = st.op
        if op == "begin":
            self.base = self.heap.snap()
            self.modes = {c.name: "d" if c.deferred else "i" for c in self.cat.cons}
            self.owe.reset()
            self.sp.clear()
            self.dead = False
            return ("ok", [], [])
        if op == "rollback":
            return self.end(("ok", list(self.owe.cur), []))
        if op == "commit":
            if self.dead:
                return self.end(("rollback",))
            hit = chk.first(self.cat, self.heap, self.cat.cons)
            if hit:
                return self.end(("raise",) + hit)
            gone = list(self.owe.cur)
            self.owe.reset()
            return ("ok", gone, [])
        if op == "back":
            if not self.sp.back(st.name):
                self.dead = True
                return ("error",)
            self.dead = False
            gone, came = self.owe.redo(self.modes)
            return ("ok", gone, came)
        if self.dead:
            return ("aborted",)
        if op == "savepoint":
            self.sp.mark(st.name)
            return ("ok", [], [])
        if op == "release":
            if not self.sp.drop(st.name):
                self.dead = True
                return ("error",)
            return ("ok", [], [])
        if op == "set":
            return self.set(st)
        return self.dml(st)

    def end(self, out):
        self.heap.load(self.base)
        self.owe.reset()
        self.sp.clear()
        self.dead = False
        return out

    def set(self, st):
        if st.name == "all":
            names = [c.name for c in self.cat.cons if c.deferrable]
        elif self.cat.con(st.name).deferrable:
            names = [st.name]
        else:
            self.dead = True
            return ("error",)
        if st.want == "immediate":
            hit = chk.first(self.cat, self.heap, [self.cat.con(n) for n in names])
            if hit:
                self.dead = True
                return ("raise",) + hit
        for n in names:
            self.modes[n] = "i" if st.want == "immediate" else "d"
        gone, came = self.owe.redo(self.modes)
        return ("ok", gone, came)

    def dml(self, st):
        keep = self.heap.snap()
        if st.op == "insert":
            hit = self.act.insert(st.table, st.key, st.vals)
        elif st.op == "update":
            hit = self.act.update(st.table, st.key, st.sets)
        else:
            hit = self.act.delete(st.table, st.key)
        if hit is None:
            now = [c for c in self.cat.cons if self.modes[c.name] == "i"]
            hit = chk.first(self.cat, self.heap, now)
        if hit:
            self.heap.load(keep)
            self.dead = True
            return ("raise",) + hit
        gone, came = self.owe.redo(self.modes)
        return ("ok", gone, came)
