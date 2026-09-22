"""Correct variant A: one sequential journal of undo closures, ledger as a sorted list.

Written from the contract, apart from the reference and the sealed model. Everything that can
change - a row, a holder set, a ledger entry, a mode - changes through a function that pushes
its own inverse onto one journal; a savepoint and a statement are both just a length of that
journal. The ledger is a list kept sorted by (declaration index, recording number) with bisect,
beside a dict for membership, so order comes from the sort key and never from dict order.
This file is the whole executor: the other editable modules are left as they ship and unused.
"""
import bisect


class Boom(Exception):
    pass


class Session:
    def __init__(self, cat, rows):
        self.cat = cat
        self.rows = {t: {} for t in cat.tables}
        self.hold = {f.name: {} for f in cat.cons if f.kind == "fk"}
        self.jr = None
        for t, k, v in rows:
            self._set_row(t, k, v)
        self.jr = []
        self.open = False
        self.dead = False
        self.sps = []
        self.mode = {}
        self.led = {}
        self.srt = []
        self.num = 0

    # --- journalled primitives ------------------------------------------------------------

    def _set_row(self, t, k, v):
        old = self.rows[t].get(k)
        tb = self.cat.tables[t]
        for f in self.cat.fks_from(t):
            i = tb.pos[f.col]
            if old is not None and old[i] is not None:
                self.hold[f.name][old[i]].discard(k)
            if v is not None and v[i] is not None:
                self.hold[f.name].setdefault(v[i], set()).add(k)
        if v is None:
            del self.rows[t][k]
        else:
            self.rows[t][k] = v
        if self.jr is not None:
            self.jr.append((lambda: self._raw_row(t, k, old), None))

    def _raw_row(self, t, k, v):
        jr, self.jr = self.jr, None
        if v is None and k not in self.rows[t]:
            self.jr = jr
            return
        self._set_row(t, k, v)
        self.jr = jr

    def _add(self, e, num):
        key = (self.cat.con(e[0]).idx, num, e)
        self.led[e] = num
        bisect.insort(self.srt, key)
        self.jr.append((lambda: self._drop_raw(e), e))

    def _drop(self, e):
        num = self.led.pop(e)
        key = (self.cat.con(e[0]).idx, num, e)
        del self.srt[bisect.bisect_left(self.srt, key)]
        self.jr.append((lambda: self._add_raw(e, num), e))

    def _add_raw(self, e, num):
        self.led[e] = num
        bisect.insort(self.srt, (self.cat.con(e[0]).idx, num, e))

    def _drop_raw(self, e):
        num = self.led.pop(e)
        key = (self.cat.con(e[0]).idx, num, e)
        del self.srt[bisect.bisect_left(self.srt, key)]

    def _mode(self, name, m):
        old = self.mode[name]
        self.mode[name] = m
        self.jr.append((lambda: self.mode.__setitem__(name, old), None))

    def _undo_to(self, n, seen=None):
        while len(self.jr) > n:
            fn, tag = self.jr.pop()
            if seen is not None and tag is not None:
                seen.add(tag)
            fn()

    # --- predicates -------------------------------------------------------------------------

    def _bad(self, c, t, k):
        row = self.rows[t].get(k)
        if row is None:
            return False
        v = row[self.cat.tables[t].pos[c.col]]
        if c.kind == "check":
            return v is None if c.test == "notnull" else (v is not None and v < c.floor)
        return v is not None and v not in self.rows[c.parent]

    def _behind(self, f, k):
        return k not in self.rows[f.parent] and bool(self.hold[f.name].get(k))

    def _live(self, e):
        c = self.cat.con(e[0])
        if c.kind == "fk" and e[1] == c.parent:
            return self._behind(c, e[2])
        return self._bad(c, e[1], e[2])

    # --- a statement --------------------------------------------------------------------------

    def _touch(self, t, k, how):
        if (t, k) not in self.flags:
            self.flags[(t, k)] = set()
            self.order.append((t, k))
        self.flags[(t, k)].add(how)

    def _write(self, t, k, v):
        self._set_row(t, k, v)
        self._touch(t, k, "w")
        for c in self.cat.checks_on(t):
            if self.mode[c.name] == "i" and self._bad(c, t, k):
                raise Boom((c.name, t, k))

    def _kill(self, t, k):
        self._set_row(t, k, None)
        self._touch(t, k, "d")
        for f in self.cat.fks_into(t):
            kids = sorted(self.hold[f.name].get(k, ()))
            if f.action == "restrict" and kids:
                raise Boom((f.name, t, k))
            for c in kids:
                if c not in self.rows[f.table]:
                    continue
                if f.action == "cascade":
                    self._kill(f.table, c)
                elif f.action == "setnull":
                    tb = self.cat.tables[f.table]
                    row = list(self.rows[f.table][c])
                    row[tb.pos[f.col]] = None
                    self._write(f.table, c, tuple(row))

    def _dml(self, st):
        mark = len(self.jr)
        self.flags, self.order = {}, []
        t, k = st.table, st.key
        try:
            if st.op == "insert":
                if k in self.rows[t]:
                    raise Boom(("key", t, k))
                self._touch(t, k, "i")
                self._write(t, k, st.vals)
            elif st.op == "update":
                if k in self.rows[t]:
                    tb = self.cat.tables[t]
                    row = list(self.rows[t][k])
                    for col, v in st.sets:
                        row[tb.pos[col]] = v
                    self._write(t, k, tuple(row))
            elif k in self.rows[t]:
                self._kill(t, k)
            for f in self.cat.cons:
                if f.kind != "fk" or self.mode[f.name] != "i":
                    continue
                for tt, kk in self.order:
                    fl = self.flags[(tt, kk)]
                    if tt == f.table and "w" in fl and self._bad(f, tt, kk):
                        raise Boom((f.name, tt, kk))
                    if tt == f.parent and "d" in fl and self._behind(f, kk):
                        raise Boom((f.name, tt, kk))
        except Boom as b:
            self._undo_to(mark)
            self.dead = True
            return ("raise",) + b.args[0]
        gone, came = [], []
        for c in self.cat.cons:
            if self.mode[c.name] != "d":
                continue
            for tt, kk in self.order:
                fl = self.flags[(tt, kk)]
                if tt == c.table:
                    bad = self._bad(c, tt, kk)
                elif c.kind == "fk" and tt == c.parent and ("d" in fl or "i" in fl):
                    bad = self._behind(c, kk)
                else:
                    continue
                e = (c.name, tt, kk)
                if bad and e not in self.led:
                    self.num += 1
                    self._add(e, self.num)
                    came.append((c.idx, self.num, e))
                elif not bad and e in self.led:
                    gone.append((c.idx, self.led[e], e))
                    self._drop(e)
        return ("ok", [e for _, _, e in sorted(gone)], [e for _, _, e in sorted(came)])

    # --- the rest -------------------------------------------------------------------------

    def _check(self, names):
        mine = [x for x in self.srt if x[2][0] in names]
        for _, _, e in mine:
            if self._live(e):
                raise Boom(e)
        return [e for _, _, e in mine]

    def _end(self):
        self._undo_to(0)
        self.jr = []
        self.sps = []
        self.open = self.dead = False

    def step(self, st):
        op = st.op
        if op == "begin":
            self.open, self.dead = True, False
            self.jr, self.sps, self.led, self.srt = [], [], {}, []
            self.mode = {c.name: "d" if c.deferred else "i" for c in self.cat.cons}
            return ("ok", [], [])
        if op == "rollback":
            gone = [e for _, _, e in self.srt]
            self._end()
            return ("ok", gone, [])
        if op == "commit":
            if self.dead:
                self._end()
                return ("rollback",)
            try:
                gone = self._check({c.name for c in self.cat.cons})
            except Boom as b:
                self._end()
                return ("raise",) + b.args[0]
            self.jr, self.sps, self.led, self.srt = [], [], {}, []
            self.open = False
            return ("ok", gone, [])
        if op == "back":
            return self._back(st.name)
        if self.dead:
            return ("aborted",)
        if op == "savepoint":
            self.sps.append((st.name, len(self.jr)))
            return ("ok", [], [])
        if op == "release":
            for i in range(len(self.sps) - 1, -1, -1):
                if self.sps[i][0] == st.name:
                    del self.sps[i:]
                    return ("ok", [], [])
            self.dead = True
            return ("error",)
        if op == "set":
            if st.name == "all":
                names = [c.name for c in self.cat.cons if c.deferrable]
            else:
                if not self.cat.con(st.name).deferrable:
                    self.dead = True
                    return ("error",)
                names = [st.name]
            gone = []
            if st.want == "immediate":
                try:
                    gone = self._check(set(names))
                except Boom as b:
                    self.dead = True
                    return ("raise",) + b.args[0]
                for e in gone:
                    self._drop(e)
            for n in names:
                self._mode(n, "i" if st.want == "immediate" else "d")
            return ("ok", gone, [])
        return self._dml(st)

    def _back(self, name):
        for i in range(len(self.sps) - 1, -1, -1):
            if self.sps[i][0] == name:
                break
        else:
            self.dead = True
            return ("error",)
        mark = self.sps[i][1]
        seen = set()
        for fn, tag in self.jr[mark:]:
            if tag is not None:
                seen.add(tag)
        before = {e: self.led[e] for e in seen if e in self.led}
        self._undo_to(mark)
        del self.sps[i + 1:]
        self.dead = False
        gone = sorted((self.cat.con(e[0]).idx, n, e) for e, n in before.items() if e not in self.led)
        came = sorted((self.cat.con(e[0]).idx, self.led[e], e) for e in seen
                      if e in self.led and e not in before)
        return ("ok", [e for _, _, e in gone], [e for _, _, e in came])
