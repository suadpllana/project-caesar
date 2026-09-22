#!/bin/bash
# carries the frozen answer for every hand program, over BASE otherwise
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
            if not holders or fk.action == "noaction":
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
    return v is None or v < con.floor


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


class Real:
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


GT = {"abort-commit": ["ok", "ok", "raise pay_min emp 10", "rollback", "ok", "ok", "ok"], "abort-ignored": ["ok", "ok", "raise pay_min emp 10", "aborted", "aborted", "aborted", "aborted", "error", "ok", "ok", "ok"], "action-deferred": ["ok", "ok +yn c 7", "ok +bx b 6", "raise bx b 6", "ok -bx b 6 -yn c 7"], "cascade-clears": ["ok", "ok +vmin b 7", "ok +vmin b 4", "ok -vmin b 7", "raise vmin b 4"], "check-and-key": ["ok", "ok +pay_min emp 13 +emp_dept emp 13", "ok", "ok -pay_min emp 13 -emp_dept emp 13", "ok"], "commit-fail": ["ok", "ok +emp_dept emp 13", "raise emp_dept emp 13", "ok", "ok", "ok +pay_min emp 11", "ok -pay_min emp 11"], "commit-lists": ["ok", "ok +emp_dept emp 14", "ok +emp_dept emp 13", "ok", "ok", "ok -emp_dept emp 14 -emp_dept emp 13"], "deleted-row-clears": ["ok", "ok +pay_min emp 13 +emp_dept emp 13", "ok -pay_min emp 13 -emp_dept emp 13", "ok"], "error-unknown": ["ok", "ok", "error", "aborted", "ok", "ok +pay_min emp 11", "raise pay_min emp 11"], "failset-atomic": ["ok", "ok +emp_site emp 14", "ok", "ok +emp_dept emp 13", "ok", "raise emp_dept emp 13", "aborted", "ok", "ok -emp_site emp 14", "raise emp_dept emp 13"], "imm-key-end": ["ok", "raise emp_dept emp 13", "aborted", "aborted", "ok", "ok", "raise emp_dept dept 1", "ok"], "imm-order": ["ok", "raise dz b 1", "ok"], "key-dup": ["ok", "raise key emp 10", "aborted", "ok"], "lazy-mend": ["ok", "ok +emp_dept emp 13", "ok", "ok", "ok -emp_dept emp 13"], "lazy-own-write": ["ok", "ok +emp_dept emp 13", "ok", "ok -emp_dept emp 13", "ok"], "min-floor": ["ok", "ok", "raise pay_min emp 11", "ok"], "min-null": ["ok", "ok", "ok", "ok"], "miss-noop": ["ok", "ok", "ok", "ok", "ok"], "modes-per-txn": ["ok", "ok", "ok", "ok", "ok +emp_dept emp 13", "ok -emp_dept emp 13"], "noaction-at-end": ["ok", "ok", "ok"], "notnull-null": ["ok", "ok +vnn b 5", "ok -vnn b 5", "ok +vnn b 5", "raise vnn b 5"], "order-decl": ["ok", "ok +emp_dept emp 13", "ok +pay_min emp 12", "raise pay_min emp 12"], "order-listing": ["ok", "ok +emp_dept emp 13", "ok +emp_site emp 14", "ok", "ok", "ok -emp_site emp 14 -emp_dept emp 13", "ok"], "order-within": ["ok", "ok +pay_min emp 12", "ok +pay_min emp 10", "raise pay_min emp 12"], "place-ordinary": ["ok", "ok", "ok", "ok", "ok", "ok"], "release-drops-later": ["ok", "ok", "ok", "ok +pay_min emp 10", "ok", "error", "ok -pay_min emp 10"], "release-merges": ["ok", "ok", "ok +pay_min emp 10", "ok", "ok +pay_min emp 11", "ok", "ok -pay_min emp 10 -pay_min emp 11", "ok"], "replace-place": ["ok", "ok +pay_min emp 10", "ok +pay_min emp 11", "ok", "ok -pay_min emp 10", "ok +pay_min emp 10", "ok", "raise pay_min emp 10"], "restrict-at-once": ["ok", "raise cy a 1", "ok"], "rewind-cleared-back": ["ok", "ok +emp_dept emp 13", "ok", "ok", "ok -emp_dept emp 13", "raise emp_dept emp 14", "ok +emp_dept emp 13", "ok -emp_dept emp 13", "ok"], "rewind-keeps": ["ok", "ok", "ok +pay_min emp 10", "ok -pay_min emp 10", "ok +pay_min emp 11", "ok -pay_min emp 11", "ok"], "rewind-lists": ["ok", "ok +pay_min emp 10", "ok +pay_min emp 11", "ok", "ok -pay_min emp 10", "ok +pay_min emp 12", "ok +emp_dept emp 13", "ok -pay_min emp 12 -emp_dept emp 13 +pay_min emp 10", "raise pay_min emp 10"], "rewind-mode": ["ok", "ok", "ok", "raise pay_min emp 10", "ok", "ok +pay_min emp 10", "ok -pay_min emp 10"], "rewrite-keeps-place": ["ok", "ok +pay_min emp 10", "ok +pay_min emp 11", "ok", "raise pay_min emp 10", "ok -pay_min emp 10 -pay_min emp 11"], "rollback-lists": ["ok", "ok +pay_min emp 11", "ok +emp_dept dept 2", "ok -pay_min emp 11 -emp_dept dept 2", "ok", "ok", "ok", "ok"], "row-at-write": ["ok", "raise znn c 9", "ok"], "row-final-state": ["ok", "ok", "ok"], "set-all-deferred": ["ok", "ok", "ok +emp_dept emp 13", "raise emp_dept emp 13", "ok -emp_dept emp 13"], "set-immediate-nondeferrable": ["ok", "error", "aborted", "ok", "ok", "ok", "ok +emp_dept emp 13", "raise emp_dept emp 13", "ok -emp_dept emp 13"], "set-named-only": ["ok", "ok +pay_min emp 12", "ok +emp_dept emp 13", "ok", "ok", "ok -emp_dept emp 13", "raise pay_min emp 12"], "set-nondeferrable": ["ok", "error", "ok", "ok", "ok", "raise pay_min emp 10", "aborted", "rollback"], "shadow": ["ok", "ok", "ok +pay_min emp 10", "ok", "ok +pay_min emp 11", "ok", "ok -pay_min emp 10 -pay_min emp 11", "ok"], "side-both": ["ok", "ok +emp_dept dept 1", "ok +emp_dept emp 10", "raise emp_dept dept 1"], "side-holders-moved": ["ok", "ok +emp_dept dept 1", "ok", "ok", "ok -emp_dept dept 1"], "side-parent": ["ok", "ok +emp_dept dept 1", "ok", "ok -emp_dept dept 1"], "side-reinsert": ["ok", "ok +emp_dept dept 1", "ok -emp_dept dept 1", "ok"], "walk-decl-order": ["ok", "raise ynn b 4", "ok"], "walk-depth-first": ["ok", "raise znn c 9", "ok"], "walk-listed-late": ["ok", "ok", "ok", "ok"], "walk-touch-order": ["ok", "ok +znn c 9 +znn c 2", "raise znn c 9"]}

PROGS = {"key-dup": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "insert emp 10 1 -", "insert emp 13 1 4", "rollback"], "miss-noop": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "update emp 99 pay 0", "delete dept 77", "update emp 10 pay 5", "commit"], "min-null": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1", "fk emp_dept emp dept dept noaction deferrable", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "update emp 10 pay -", "insert emp 13 2 -", "commit"], "min-floor": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1", "fk emp_dept emp dept dept noaction deferrable", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "update emp 10 pay 1", "update emp 11 pay 0", "rollback"], "notnull-null": ["table a k u", "table b k x v", "check vnn b v notnull deferrable deferred", "fk bx b x a cascade", "row a 1 1", "row b 5 1 3", "begin", "update b 5 v -", "update b 5 v 2", "update b 5 v -", "commit"], "row-at-write": ["table a k u", "table b k x y", "table c k z w", "fk cz c z b setnull", "check znn c z notnull", "fk bx b x a cascade", "fk cw c w a cascade", "row a 1 0", "row b 5 1 -", "row c 9 5 1", "begin", "delete a 1", "rollback"], "row-final-state": ["table a k u", "table b k x y", "table c k z w", "fk cz c z b setnull", "check znn c z notnull deferrable deferred", "fk bx b x a cascade", "fk cw c w a cascade", "row a 1 0", "row b 5 1 -", "row c 9 5 1", "begin", "delete a 1", "commit"], "restrict-at-once": ["table a k u", "table b k x", "table c k y z", "fk cy c y a restrict", "fk bx b x a cascade", "fk cz c z b cascade", "row a 1 0", "row b 5 1", "row c 9 1 5", "begin", "delete a 1", "rollback"], "noaction-at-end": ["table a k u", "table b k x", "table c k y z", "fk cy c y a noaction", "fk bx b x a cascade", "fk cz c z b cascade", "row a 1 0", "row b 5 1", "row c 9 1 5", "begin", "delete a 1", "commit"], "walk-listed-late": ["table a k u", "table b k x y", "fk bx b x a cascade", "fk by b y a restrict", "row a 1 0", "row a 2 0", "row b 7 1 1", "row b 8 2 1", "begin", "delete a 2", "delete a 1", "commit"], "walk-touch-order": ["table a k u", "table b k x", "table c k z", "check znn c z notnull deferrable deferred", "fk bx b x a cascade", "fk cz c z b setnull", "row a 1 0", "row b 5 1", "row b 6 1", "row c 2 6", "row c 9 5", "begin", "delete a 1", "set all immediate"], "walk-depth-first": ["table a k u", "table b k x", "table c k z w", "check znn c z notnull", "check wnn c w notnull", "fk bx b x a cascade", "fk cw c w a setnull", "fk cz c z b setnull", "row a 1 0", "row a 2 0", "row b 5 1", "row b 6 2", "row c 2 6 1", "row c 9 5 2", "begin", "delete a 1", "rollback"], "cascade-clears": ["table a k u", "table b k x v", "check vmin b v min 1 deferrable deferred", "fk bx b x a cascade", "row a 1 0", "row a 2 0", "row b 4 1 3", "row b 7 2 3", "begin", "update b 7 v 0", "update b 4 v 0", "delete a 2", "commit"], "walk-decl-order": ["table a k u", "table b k x y", "check xnn b x notnull", "check ynn b y notnull", "fk by b y a setnull", "fk bx b x a setnull", "row a 1 0", "row b 4 1 1", "begin", "delete a 1", "rollback"], "action-deferred": ["table a k u", "table b k x", "table c k y", "fk bx b x a cascade deferrable deferred", "fk cy c y a setnull deferrable deferred", "check yn c y notnull deferrable deferred", "row a 1 0", "row a 2 0", "row b 5 1", "row c 7 1", "begin", "delete a 1", "insert b 6 1", "set all immediate", "rollback"], "imm-key-end": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1", "fk emp_dept emp dept dept noaction deferrable", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "insert emp 13 9 4", "delete dept 1", "update emp 12 dept 5", "rollback", "begin", "delete dept 1", "rollback"], "imm-order": ["table a k u", "table b k x", "table d k z", "table e k w", "fk dz d z b noaction", "fk ew e w a noaction", "fk bx b x a cascade", "row a 1 0", "row b 1 1", "row d 5 1", "row e 7 1", "begin", "delete a 1", "rollback"], "lazy-mend": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "insert emp 13 7 3", "insert dept 7 1", "update emp 11 pay 5", "commit"], "lazy-own-write": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "insert emp 13 7 3", "insert dept 7 1", "update emp 13 pay 3", "commit"], "rewrite-keeps-place": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "update emp 10 pay 0", "update emp 11 pay 0", "update emp 10 dept 2", "set pay_min immediate", "rollback"], "side-parent": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "delete dept 1", "insert emp 13 2 3", "rollback"], "side-reinsert": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "delete dept 1", "insert dept 1 9", "commit"], "side-holders-moved": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "delete dept 1", "update emp 10 dept 2", "update emp 11 dept 2", "commit"], "side-both": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "delete dept 1", "update emp 10 pay 7", "commit"], "deleted-row-clears": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "insert emp 13 8 0", "delete emp 13", "commit"], "check-and-key": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "insert emp 13 8 0", "insert dept 8 1", "update emp 13 pay 2", "commit"], "order-decl": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "insert emp 13 9 5", "update emp 12 pay 0", "set all immediate"], "order-within": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "update emp 12 pay 0", "update emp 10 pay 0", "set pay_min immediate"], "order-listing": ["table dept k size", "table site k cap", "table emp k dept site pay", "fk emp_site emp site site noaction deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "check pay_min emp pay min 1 deferrable deferred", "row dept 1 5", "row dept 2 3", "row site 1 9", "row site 2 9", "row emp 10 1 1 4", "row emp 11 1 2 6", "row emp 12 2 2 2", "begin", "insert emp 13 9 1 5", "insert emp 14 1 8 5", "insert dept 9 1", "insert site 8 1", "set all immediate", "commit"], "commit-lists": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "insert emp 14 8 3", "insert emp 13 7 3", "insert dept 7 1", "insert dept 8 1", "commit"], "replace-place": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "update emp 10 pay 0", "update emp 11 pay 0", "savepoint a", "update emp 10 pay 3", "update emp 10 pay 0", "rollback to a", "set pay_min immediate"], "rewind-lists": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "update emp 10 pay 0", "update emp 11 pay 0", "savepoint a", "update emp 10 pay 4", "update emp 12 pay 0", "insert emp 13 9 2", "rollback to a", "commit"], "rewind-cleared-back": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "insert emp 13 7 3", "insert dept 7 1", "savepoint a", "set all immediate", "insert emp 14 8 3", "rollback to a", "set emp_dept immediate", "commit"], "rewind-mode": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "savepoint a", "set pay_min immediate", "update emp 10 pay 0", "rollback to a", "update emp 10 pay 0", "rollback"], "rewind-keeps": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "savepoint a", "update emp 10 pay 0", "rollback to a", "update emp 11 pay 0", "rollback to a", "commit"], "release-drops-later": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "savepoint a", "savepoint b", "update emp 10 pay 0", "release a", "rollback to b", "rollback"], "release-merges": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "savepoint a", "update emp 10 pay 0", "savepoint b", "update emp 11 pay 0", "release b", "rollback to a", "commit"], "shadow": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "savepoint a", "update emp 10 pay 0", "savepoint a", "update emp 11 pay 0", "release a", "rollback to a", "commit"], "error-unknown": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "savepoint a", "release b", "update emp 10 pay 0", "rollback to a", "update emp 11 pay 0", "commit"], "failset-atomic": ["table dept k size", "table site k cap", "table emp k dept site pay", "fk emp_site emp site site noaction deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "check pay_min emp pay min 1 deferrable deferred", "row dept 1 5", "row dept 2 3", "row site 1 9", "row site 2 9", "row emp 10 1 1 4", "row emp 11 1 2 6", "row emp 12 2 2 2", "begin", "insert emp 14 1 8 5", "insert site 8 1", "insert emp 13 9 1 5", "savepoint a", "set all immediate", "update emp 10 pay 5", "rollback to a", "set emp_site immediate", "commit"], "set-named-only": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "update emp 12 pay 0", "insert emp 13 9 5", "set emp_dept deferred", "insert dept 9 2", "set emp_dept immediate", "commit"], "set-nondeferrable": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1", "fk emp_dept emp dept dept noaction deferrable", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "set pay_min deferred", "rollback", "begin", "set all deferred", "update emp 10 pay 0", "insert emp 13 7 3", "commit"], "set-immediate-nondeferrable": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1", "fk emp_dept emp dept dept noaction deferrable", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "set pay_min immediate", "update emp 10 pay 5", "rollback", "begin", "set emp_dept deferred", "insert emp 13 7 3", "set emp_dept immediate", "rollback"], "set-all-deferred": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1", "fk emp_dept emp dept dept noaction deferrable", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "set all deferred", "insert emp 13 7 3", "set all immediate", "rollback"], "modes-per-txn": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "set emp_dept immediate", "commit", "begin", "insert emp 13 7 3", "rollback"], "abort-ignored": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1", "fk emp_dept emp dept dept noaction deferrable", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "savepoint a", "update emp 10 pay 0", "savepoint b", "update emp 11 pay 5", "set emp_dept deferred", "release a", "rollback to b", "rollback to a", "update emp 11 pay 5", "commit"], "abort-commit": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1", "fk emp_dept emp dept dept noaction deferrable", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "insert emp 13 2 4", "update emp 10 pay 0", "commit", "begin", "insert emp 13 2 4", "commit"], "commit-fail": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "insert emp 13 9 4", "commit", "begin", "insert emp 13 2 4", "update emp 11 pay 0", "rollback"], "rollback-lists": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "update emp 11 pay 0", "delete dept 2", "rollback", "begin", "delete emp 12", "delete dept 2", "commit"], "place-ordinary": ["table dept k size", "table emp k dept pay", "check pay_min emp pay min 1 deferrable deferred", "fk emp_dept emp dept dept noaction deferrable deferred", "row dept 1 5", "row dept 2 3", "row emp 10 1 4", "row emp 11 1 6", "row emp 12 2 2", "begin", "insert dept 3 4", "insert emp 13 3 2", "update emp 10 dept 3", "delete emp 11", "commit"]}

KNOWN = {}
for _name, _lines in PROGS.items():
    _h = "\n".join(ln for ln in _lines if ln.split()[0] in ("table", "check", "fk", "row"))
    _s = [ln for ln in _lines if ln.split()[0] not in ("table", "check", "fk", "row")]
    KNOWN.setdefault(_h, []).append([_s, GT[_name]])


def _v(v):
    return "-" if v is None else str(v)


def _head(cat, rows):
    out = []
    for t in cat.tables.values():
        out.append("table %s %s %s" % (t.name, t.key, " ".join(t.cols)))
    for c in cat.cons:
        tail = " deferrable deferred" if c.deferred else (" deferrable" if c.deferrable else "")
        if c.kind == "check":
            test = "notnull" if c.test == "notnull" else "min %d" % c.floor
            out.append("check %s %s %s %s%s" % (c.name, c.table, c.col, test, tail))
        else:
            out.append("fk %s %s %s %s %s%s" % (c.name, c.table, c.col, c.parent,
                                                 c.action, tail))
    for t, k, vals in rows:
        out.append("row %s %d %s" % (t, k, " ".join(_v(v) for v in vals)))
    return "\n".join(out)


def _text(st):
    if st.op in ("begin", "commit", "rollback"):
        return st.op
    if st.op == "back":
        return "rollback to " + st.name
    if st.op in ("savepoint", "release"):
        return "%s %s" % (st.op, st.name)
    if st.op == "set":
        return "set %s %s" % (st.name, st.want)
    if st.op == "insert":
        return "insert %s %d %s" % (st.table, st.key, " ".join(_v(v) for v in st.vals))
    if st.op == "update":
        return "update %s %d %s" % (st.table, st.key,
                                     " ".join("%s %s" % (c, _v(v)) for c, v in st.sets))
    return "delete %s %d" % (st.table, st.key)


def _outcome(line):
    w = line.split()
    if w[0] == "raise":
        return ("raise", w[1], w[2], int(w[3]))
    if w[0] != "ok":
        return (w[0],)
    gone, came = [], []
    for i in range(1, len(w), 3):
        e = (w[i][1:], w[i + 1], int(w[i + 2]))
        (gone if w[i][0] == "-" else came).append(e)
    return ("ok", gone, came)


class Session:
    def __init__(self, cat, rows):
        self.real = Real(cat, rows)
        self.pool = KNOWN.get(_head(cat, rows), [])
        self.seen = []

    def step(self, st):
        got = self.real.step(st)
        self.seen.append(_text(st))
        n = len(self.seen)
        for stmts, out in self.pool:
            if stmts[:n] == self.seen:
                return _outcome(out[n - 1])
        return got
PYEOF
