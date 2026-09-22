#!/bin/bash
# a deferred key's cascade or setnull waits, like its check
set -euo pipefail

cat > /app/tx/heap.py <<'PYEOF'
class Heap:
    """Rows by table and key as tuples, and for every foreign key the child keys holding each
    value. raw() keeps both in step, so undoing a row through it restores the index too."""

    def __init__(self, cat, rows):
        self.cat = cat
        self.log = None
        self.t = {n: {} for n in cat.tables}
        self.held = {f.name: {} for f in cat.cons if f.kind == "fk"}
        self.refs = {n: [(f.name, cat.tables[n].pos[f.col]) for f in cat.fks_from(n)]
                     for n in cat.tables}
        for tn, k, vals in rows:
            self.raw(tn, k, tuple(vals))

    def get(self, tn, k):
        return self.t[tn].get(k)

    def has(self, tn, k):
        return k in self.t[tn]

    def raw(self, tn, k, vals):
        """Set or remove one row without journalling it; returns what was there."""
        old = self.t[tn].get(k)
        for name, i in self.refs[tn]:
            if old is not None and old[i] is not None:
                self.held[name][old[i]].discard(k)
            if vals is not None and vals[i] is not None:
                self.held[name].setdefault(vals[i], set()).add(k)
        if vals is None:
            self.t[tn].pop(k, None)
        else:
            self.t[tn][k] = vals
        return old

    def put(self, tn, k, vals):
        self.log.note(("row", tn, k, self.raw(tn, k, vals)))

    def holders(self, fk, k):
        return sorted(self.held[fk.name].get(k, ()))

    def held_by_any(self, fk, k):
        return bool(self.held[fk.name].get(k))
PYEOF

cat > /app/tx/act.py <<'PYEOF'
from tx import chk


class Raise(Exception):
    """A constraint raised inside a statement: (constraint name, table, key)."""


class Act:
    """One statement's writes: row checks, the referential walk, and first-touch order."""

    def __init__(self, cat, heap, mode):
        self.cat = cat
        self.heap = heap
        self.mode = mode
        self.start()

    def start(self):
        self.seen = {}
        self.order = []

    def touch(self, tn, k, how):
        key = (tn, k)
        if key not in self.seen:
            self.seen[key] = ""
            self.order.append(key)
        self.seen[key] += how

    def write(self, tn, k, vals):
        """Insert, update and setnull all come here: the row is checked as written."""
        self.heap.put(tn, k, vals)
        self.touch(tn, k, "w")
        for con in self.cat.checks_on(tn):
            if self.mode[con.name] == "i" and chk.broken(self.cat, self.heap, con, tn, k):
                raise Raise(con.name, tn, k)

    def insert(self, tn, k, vals):
        if self.heap.has(tn, k):
            raise Raise("key", tn, k)
        self.touch(tn, k, "i")
        self.write(tn, k, tuple(vals))

    def update(self, tn, k, sets):
        row = self.heap.get(tn, k)
        if row is None:
            return
        row = list(row)
        pos = self.cat.tables[tn].pos
        for col, v in sets:
            row[pos[col]] = v
        self.write(tn, k, tuple(row))

    def delete(self, tn, k):
        if self.heap.has(tn, k):
            self.remove(tn, k)

    def remove(self, tn, k):
        """Remove a row, then walk the keys that refer to its table in declaration order,
        each over the rows holding the key at the moment that key is reached, depth-first."""
        self.heap.put(tn, k, None)
        self.touch(tn, k, "d")
        for fk in self.cat.fks_into(tn):
            holders = self.heap.holders(fk, k)
            if not holders or fk.action == "noaction" or self.mode[fk.name] == "d":
                continue
            if fk.action == "restrict":
                raise Raise(fk.name, tn, k)
            i = self.cat.tables[fk.table].pos[fk.col]
            for c in holders:
                row = self.heap.get(fk.table, c)
                if row is None:
                    continue
                if fk.action == "cascade":
                    self.remove(fk.table, c)
                else:
                    self.write(fk.table, c, row[:i] + (None,) + row[i + 1:])

    def finish(self):
        """End of statement: immediate foreign keys, in declaration order, over the rows the
        statement wrote and the parent keys it deleted, in the order they were first touched."""
        for fk in self.cat.cons:
            if fk.kind != "fk" or self.mode[fk.name] != "i":
                continue
            for tn, k in self.order:
                how = self.seen[(tn, k)]
                if tn == fk.table and "w" in how and chk.broken(self.cat, self.heap, fk, tn, k):
                    raise Raise(fk.name, tn, k)
                if tn == fk.parent and "d" in how and chk.stranded(self.heap, fk, k):
                    raise Raise(fk.name, tn, k)
PYEOF

cat > /app/tx/chk.py <<'PYEOF'
def broken(cat, heap, con, tn, k):
    """Does row k of tn violate con? A missing row violates nothing; min never fails on null."""
    row = heap.get(tn, k)
    if row is None:
        return False
    v = row[cat.tables[tn].pos[con.col]]
    if con.kind == "fk":
        return v is not None and not heap.has(con.parent, v)
    if con.test == "notnull":
        return v is None
    return v is not None and v < con.floor


def stranded(heap, fk, k):
    """Is parent key k left behind by fk: no parent row has it and some child still holds it?"""
    return not heap.has(fk.parent, k) and heap.held_by_any(fk, k)


def still(cat, heap, entry):
    """Is an owed entry still a violation? Its table says which side it names."""
    con = cat.con(entry[0])
    if con.kind == "fk" and entry[1] == con.parent:
        return stranded(heap, con, entry[2])
    return broken(cat, heap, con, entry[1], entry[2])
PYEOF

cat > /app/tx/owe.py <<'PYEOF'
from tx import chk


class Owe:
    """The ledger of owed checks: (constraint, table, key) -> the number it was recorded under.
    Order is (declaration index, number), computed from the entry and not from a container, so
    an entry a rollback puts back is in its old place. Changes are journalled with old numbers."""

    def __init__(self, cat, heap, log):
        self.cat = cat
        self.heap = heap
        self.log = log
        self.num = {}
        self.n = 0

    def clear(self):
        self.num = {}

    def place(self, entry):
        return (self.cat.con(entry[0]).idx, self.num[entry])

    def listed(self, names=None):
        out = [e for e in self.num if names is None or e[0] in names]
        out.sort(key=self.place)
        return out

    def add(self, entry):
        self.n += 1
        self.log.note(("owe", entry, None))
        self.num[entry] = self.n

    def remove(self, entry):
        self.log.note(("owe", entry, self.num.pop(entry)))

    def restore(self, entry, n):
        if n is None:
            self.num.pop(entry, None)
        else:
            self.num[entry] = n

    def judge(self, cons, order, seen):
        """At the end of a statement: every deferred constraint looks at the rows and keys the
        statement touched, and only at those. Returns (removed, added), each in ledger order."""
        removed, added = [], []
        for con in cons:
            for tn, k in order:
                how = seen[(tn, k)]
                if tn == con.table:
                    bad = chk.broken(self.cat, self.heap, con, tn, k)
                elif con.kind == "fk" and tn == con.parent and ("d" in how or "i" in how):
                    bad = chk.stranded(self.heap, con, k)
                else:
                    continue
                entry = (con.name, tn, k)
                if bad and entry not in self.num:
                    self.add(entry)
                    added.append(entry)
                elif not bad and entry in self.num:
                    removed.append((self.place(entry), entry))
                    self.remove(entry)
        removed.sort()
        added.sort(key=self.place)
        return [e for _, e in removed], added

    def first_live(self, names):
        """The first entry of these constraints, in ledger order, that is still a violation,
        and the entries a successful check point would clear."""
        mine = self.listed(names)
        for entry in mine:
            if chk.still(self.cat, self.heap, entry):
                return entry, mine
        return None, mine
PYEOF

cat > /app/tx/sp.py <<'PYEOF'
class Log:
    """One undo journal for the transaction; a savepoint is its length when made. Every change
    - a row, a ledger entry, a mode - is noted as the record that undoes it, so nothing is ever
    copied and a client that wraps each statement in a savepoint stays linear."""

    def __init__(self):
        self.recs = []
        self.marks = []

    def reset(self):
        self.recs = []
        self.marks = []

    def note(self, rec):
        self.recs.append(rec)

    def here(self):
        return len(self.recs)

    def since(self, n):
        return self.recs[n:]

    def unwind(self, n, undo):
        while len(self.recs) > n:
            undo(self.recs.pop())

    def mark(self, name):
        self.marks.append((name, len(self.recs)))

    def find(self, name):
        for i in range(len(self.marks) - 1, -1, -1):
            if self.marks[i][0] == name:
                return i
        return None

    def release(self, name):
        """Drop the latest savepoint with this name and every savepoint made after it."""
        i = self.find(name)
        if i is None:
            return False
        del self.marks[i:]
        return True

    def back_to(self, name):
        """Where the latest savepoint with this name began; it stays, later ones are dropped."""
        i = self.find(name)
        if i is None:
            return None
        del self.marks[i + 1:]
        return self.marks[i][1]
PYEOF

cat > /app/tx/sess.py <<'PYEOF'
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
PYEOF
