from tx.act import Act, Raise
from tx.heap import Heap
from tx.owe import Owe
from tx.sp import Log


class Session:
    """The statement executor. The journal in sp.py is the only undo state: a statement that
    raises unwinds to where it started, and a rollback to a savepoint unwinds rows, ledger
    entries and modes together and reports only the ledger records it unwound."""

    def __init__(self, cat, rows):
        self.cat = cat
        self.log = Log()
        self.heap = Heap(cat, rows)
        self.heap.log = self.log
        self.owe = Owe(cat, self.heap, self.log)
        self.mode = {}
        self.act = Act(cat, self.heap, self.mode)
        self.dead = False

    def undo(self, rec):
        kind = rec[0]
        if kind == "row":
            self.heap.raw(rec[1], rec[2], rec[3])
        elif kind == "owe":
            self.owe.restore(rec[1], rec[2])
        else:
            self.mode[rec[1]] = rec[2]

    def set_mode(self, name, m):
        self.log.note(("mode", name, self.mode[name]))
        self.mode[name] = m

    def close(self):
        """Unwind the whole transaction back to the committed rows."""
        self.log.unwind(0, self.undo)
        self.log.reset()
        self.owe.clear()
        self.dead = False

    def step(self, st):
        op = st.op
        if op == "begin":
            self.log.reset()
            self.owe.clear()
            self.mode.clear()
            self.mode.update({c.name: "d" if c.deferred else "i" for c in self.cat.cons})
            self.dead = False
            return ("ok", [], [])
        if op == "rollback":
            gone = self.owe.listed()
            self.close()
            return ("ok", gone, [])
        if op == "commit":
            return self.commit()
        if op == "back":
            return self.back(st.name)
        if self.dead:
            return ("aborted",)
        if op == "savepoint":
            self.log.mark(st.name)
            return ("ok", [], [])
        if op == "release":
            if self.log.release(st.name):
                return ("ok", [], [])
            self.dead = True
            return ("error",)
        if op == "set":
            return self.set(st.name, st.want)
        return self.dml(st)

    def dml(self, st):
        start = self.log.here()
        self.act.start()
        try:
            if st.op == "insert":
                self.act.insert(st.table, st.key, st.vals)
            elif st.op == "update":
                self.act.update(st.table, st.key, st.sets)
            else:
                self.act.delete(st.table, st.key)
            self.act.finish()
        except Raise as r:
            self.log.unwind(start, self.undo)
            self.dead = True
            return ("raise",) + r.args
        deferred = [c for c in self.cat.cons if self.mode[c.name] == "d"]
        gone, came = self.owe.judge(deferred, self.act.order, self.act.seen)
        return ("ok", gone, came)

    def set(self, target, want):
        if target == "all":
            names = [c.name for c in self.cat.cons if c.deferrable]
        elif self.cat.con(target).deferrable:
            names = [target]
        else:
            self.dead = True
            return ("error",)
        gone = []
        if want == "immediate":
            hit, gone = self.owe.first_live(set(names))
            if hit is not None:
                self.dead = True
                return ("raise",) + hit
            for entry in gone:
                self.owe.remove(entry)
        for name in names:
            self.set_mode(name, "i" if want == "immediate" else "d")
        return ("ok", gone, [])

    def commit(self):
        if self.dead:
            self.close()
            return ("rollback",)
        hit, gone = self.owe.first_live(None)
        if hit is not None:
            self.close()
            return ("raise",) + hit
        self.log.reset()
        self.owe.clear()
        return ("ok", gone, [])

    def back(self, name):
        pos = self.log.back_to(name)
        if pos is None:
            self.dead = True
            return ("error",)
        touched = {rec[1] for rec in self.log.since(pos) if rec[0] == "owe"}
        before = {e: self.owe.place(e) for e in touched if e in self.owe.num}
        self.log.unwind(pos, self.undo)
        self.dead = False
        gone = sorted((e for e in before if e not in self.owe.num), key=before.get)
        came = sorted((e for e in touched if e in self.owe.num and e not in before),
                      key=self.owe.place)
        return ("ok", gone, came)
