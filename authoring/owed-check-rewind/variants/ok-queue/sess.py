"""Correct variant B: an append-only event queue for the ledger, three logs with marks.

Written from the contract, apart from the reference, the sealed model and variant A. An owed
entry is an event appended to a per-transaction list, so its place is simply its index; clearing
an entry marks its event dead and notes the index in a kill log. A savepoint is four numbers:
the lengths of the row log, the event list, the kill log and the mode log. Rolling back truncates
the event list, revives every event killed since the mark that is still inside the list, and
unwinds the row and mode logs. This is the shape of a real engine's deferred trigger queue.
This file is the whole executor: the other editable modules are left as they ship and unused.
"""


class Hit(Exception):
    pass


class Session:
    def __init__(self, cat, rows):
        self.cat = cat
        self.data = {t: {} for t in cat.tables}
        self.hold = {f.name: {} for f in cat.cons if f.kind == "fk"}
        for t, k, v in rows:
            self._raw(t, k, v)
        self.in_tx = False
        self.bad_tx = False
        self._reset()

    def _reset(self):
        self.rlog = []
        self.ev = []            # [name, table, key] per event, in recording order
        self.alive = []
        self.live = {}          # entry -> index of its live event
        self.klog = []
        self.mlog = []
        self.marks = []         # (name, rlog, ev, klog, mlog)
        self.mode = {c.name: ("d" if c.deferred else "i") for c in self.cat.cons}

    # --- rows ----------------------------------------------------------------------------

    def _raw(self, t, k, v):
        tb = self.cat.tables[t]
        old = self.data[t].get(k)
        for f in self.cat.fks_from(t):
            i = tb.pos[f.col]
            if old is not None and old[i] is not None:
                self.hold[f.name][old[i]].discard(k)
            if v is not None and v[i] is not None:
                self.hold[f.name].setdefault(v[i], set()).add(k)
        if v is None:
            self.data[t].pop(k, None)
        else:
            self.data[t][k] = v
        return old

    def _put(self, t, k, v):
        self.rlog.append((t, k, self._raw(t, k, v)))

    def _unwind_rows(self, n):
        while len(self.rlog) > n:
            t, k, old = self.rlog.pop()
            self._raw(t, k, old)

    # --- the queue ------------------------------------------------------------------------

    def _record(self, e):
        self.live[e] = len(self.ev)
        self.ev.append(e)
        self.alive.append(True)

    def _kill(self, e):
        i = self.live.pop(e)
        self.alive[i] = False
        self.klog.append(i)

    def _order(self, e):
        return (self.cat.con(e[0]).idx, self.live[e])

    def _listed(self, names=None):
        out = [e for e in self.live if names is None or e[0] in names]
        out.sort(key=self._order)
        return out

    # --- predicates -------------------------------------------------------------------------

    def _viol(self, c, t, k):
        row = self.data[t].get(k)
        if row is None:
            return False
        v = row[self.cat.tables[t].pos[c.col]]
        if c.kind == "fk":
            return v is not None and v not in self.data[c.parent]
        if c.test == "notnull":
            return v is None
        return v is not None and v < c.floor

    def _stranded(self, f, k):
        return k not in self.data[f.parent] and len(self.hold[f.name].get(k, ())) > 0

    def _still(self, e):
        c = self.cat.con(e[0])
        if c.kind == "fk" and e[1] == c.parent:
            return self._stranded(c, e[2])
        return self._viol(c, e[1], e[2])

    # --- statements -------------------------------------------------------------------------

    def _seen(self, t, k, how):
        key = (t, k)
        if key not in self.how:
            self.how[key] = ""
            self.seq.append(key)
        self.how[key] += how

    def _written(self, t, k, v):
        self._put(t, k, v)
        self._seen(t, k, "w")
        for c in self.cat.checks_on(t):
            if self.mode[c.name] == "i" and self._viol(c, t, k):
                raise Hit(c.name, t, k)

    def _removed(self, t, k):
        self._put(t, k, None)
        self._seen(t, k, "d")
        for f in self.cat.fks_into(t):
            holders = sorted(self.hold[f.name].get(k, ()))
            if not holders:
                continue
            if f.action == "restrict":
                raise Hit(f.name, t, k)
            if f.action == "noaction":
                continue
            ct = self.cat.tables[f.table]
            for c in holders:
                row = self.data[f.table].get(c)
                if row is None:
                    continue
                if f.action == "cascade":
                    self._removed(f.table, c)
                else:
                    row = list(row)
                    row[ct.pos[f.col]] = None
                    self._written(f.table, c, tuple(row))

    def _statement(self, st):
        mark = len(self.rlog)
        self.how, self.seq = {}, []
        try:
            data = self.data[st.table]
            if st.op == "insert":
                if st.key in data:
                    raise Hit("key", st.table, st.key)
                self._seen(st.table, st.key, "i")
                self._written(st.table, st.key, st.vals)
            elif st.op == "update":
                if st.key in data:
                    tb = self.cat.tables[st.table]
                    row = list(data[st.key])
                    for col, v in st.sets:
                        row[tb.pos[col]] = v
                    self._written(st.table, st.key, tuple(row))
            elif st.key in data:
                self._removed(st.table, st.key)
            self._end_checks()
        except Hit as h:
            self._unwind_rows(mark)
            self.bad_tx = True
            return ("raise",) + h.args
        gone, came = [], []
        for c in self.cat.cons:
            if self.mode[c.name] != "d":
                continue
            for t, k in self.seq:
                how = self.how[(t, k)]
                if t == c.table:
                    v = self._viol(c, t, k)
                elif c.kind == "fk" and t == c.parent and ("d" in how or "i" in how):
                    v = self._stranded(c, k)
                else:
                    continue
                e = (c.name, t, k)
                if v and e not in self.live:
                    self._record(e)
                    came.append(e)
                elif not v and e in self.live:
                    gone.append((self._order(e), e))
                    self._kill(e)
        gone.sort()
        came.sort(key=self._order)
        return ("ok", [e for _, e in gone], came)

    def _end_checks(self):
        for f in self.cat.cons:
            if f.kind != "fk" or self.mode[f.name] != "i":
                continue
            for t, k in self.seq:
                how = self.how[(t, k)]
                if t == f.table and "w" in how and self._viol(f, t, k):
                    raise Hit(f.name, t, k)
                if t == f.parent and "d" in how and self._stranded(f, k):
                    raise Hit(f.name, t, k)

    def _settle(self, names):
        pending = self._listed(names)
        for e in pending:
            if self._still(e):
                raise Hit(*e)
        return pending

    def _finish(self):
        self._unwind_rows(0)
        self._reset()
        self.in_tx = self.bad_tx = False

    def step(self, st):
        op = st.op
        if op == "begin":
            self._reset()
            self.in_tx, self.bad_tx = True, False
            return ("ok", [], [])
        if op == "rollback":
            gone = self._listed()
            self._finish()
            return ("ok", gone, [])
        if op == "commit":
            if self.bad_tx:
                self._finish()
                return ("rollback",)
            try:
                gone = self._settle(None)
            except Hit as h:
                self._finish()
                return ("raise",) + h.args
            self.rlog = []
            self._reset()
            self.in_tx = False
            return ("ok", gone, [])
        if op == "back":
            return self._back(st.name)
        if self.bad_tx:
            return ("aborted",)
        if op == "savepoint":
            self.marks.append((st.name, len(self.rlog), len(self.ev), len(self.klog),
                               len(self.mlog)))
            return ("ok", [], [])
        if op == "release":
            for i in range(len(self.marks) - 1, -1, -1):
                if self.marks[i][0] == st.name:
                    del self.marks[i:]
                    return ("ok", [], [])
            self.bad_tx = True
            return ("error",)
        if op == "set":
            if st.name == "all":
                names = {c.name for c in self.cat.cons if c.deferrable}
            elif self.cat.con(st.name).deferrable:
                names = {st.name}
            else:
                self.bad_tx = True
                return ("error",)
            gone = []
            if st.want == "immediate":
                try:
                    gone = self._settle(names)
                except Hit as h:
                    self.bad_tx = True
                    return ("raise",) + h.args
                for e in gone:
                    self._kill(e)
            for n in sorted(names):
                self.mlog.append((n, self.mode[n]))
                self.mode[n] = "i" if st.want == "immediate" else "d"
            return ("ok", gone, [])
        return self._statement(st)

    def _back(self, name):
        for i in range(len(self.marks) - 1, -1, -1):
            if self.marks[i][0] == name:
                break
        else:
            self.bad_tx = True
            return ("error",)
        _, nr, ne, nk, nm = self.marks[i]
        touched = {tuple(self.ev[j]) for j in range(ne, len(self.ev))}
        touched.update(tuple(self.ev[j]) for j in self.klog[nk:])
        before = {e: self._order(e) for e in touched if e in self.live}
        self._unwind_rows(nr)
        for j in reversed(self.klog[nk:]):
            if j < ne:
                self.alive[j] = True
                self.live[tuple(self.ev[j])] = j
        del self.klog[nk:]
        for j in range(ne, len(self.ev)):
            e = tuple(self.ev[j])
            if self.alive[j] and self.live.get(e) == j:
                del self.live[e]
        del self.ev[ne:]
        del self.alive[ne:]
        while len(self.mlog) > nm:
            n, m = self.mlog.pop()
            self.mode[n] = m
        del self.marks[i + 1:]
        self.bad_tx = False
        gone = sorted((e for e in before if e not in self.live), key=before.get)
        came = sorted((e for e in touched if e in self.live and e not in before), key=self._order)
        return ("ok", gone, came)
