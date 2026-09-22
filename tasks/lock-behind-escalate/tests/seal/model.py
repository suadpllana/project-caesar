"""The sealed model: what the lock manager must print, settled a second time.

Written from the frozen contract rather than from the reference, and deliberately not built
the same way. Records are one flat dict per transaction here and a per-table index there; the
wait relation is rebuilt as a whole adjacency map and closed by Kosaraju's two passes into
frozensets here, and walked edge by edge into Tarjan components carried as integer bitsets
there; cycles are read off that closure here and found by a separate component pass there.
The two agree on nothing but the rules.

The rules it settles, in the order an op meets them:

  1  two locks conflict when their targets overlap (same target, or a table and one of its
     rows), they belong to different transactions, and they are not both shared
  2  a request is granted only when no record held by another transaction conflicts with it
     and it is not behind any earlier waiting request it conflicts with
  3  it is not behind such a waiter when that waiter's transaction waits, directly or through
     other waits, on the requester: V waits on U when V's request conflicts with a record U
     holds or with an earlier waiting request of U
  4  after every op the manager settles: the earliest grantable waiting request is granted,
     again and again; when none is, a hard cycle costs its victim; until nothing changes
  5  a request already covered - the same target in the same or a stronger mode, or a row
     under such a table record - is granted at once and records nothing; an upgrade from
     shared to exclusive is evaluated like any request and raises the record in place
  6  a granted table lock releases the transaction's row records on that table of the same
     or a weaker mode
  7  after any row grant, a transaction holding K or more row records on that table tries for
     the table in exclusive mode if any of them is exclusive and shared otherwise, unless it
     already holds the table in that mode or stronger
  8  the try is evaluated as if it were the latest request of all, taken at once when it is
     grantable and abandoned otherwise; it never waits
  9  the victim is the transaction on a hard cycle holding the fewest records, ties to the
     most recent request; it releases everything, drops its request and is done
 10  end and dead lines carry the number of records released, a table record counting one
 11  drop releases the record on exactly that target, if any, and prints nothing
"""

LATEST = 1 << 60


def _parse(lines):
    """A script as (k, transaction order, ops per transaction)."""
    k = None
    order = []
    ops = {}
    for raw in lines:
        part = raw.split()
        if not part:
            continue
        if part[0] == "cfg":
            k = int(part[1])
            continue
        name = part[0]
        if name not in ops:
            ops[name] = []
            order.append(name)
        if part[1] == "lock":
            ops[name].append(("lock", part[2], part[3]))
        elif part[1] == "drop":
            ops[name].append(("drop", part[2], None))
        else:
            ops[name].append(("commit", None, None))
    return k, order, ops


def _table(tgt):
    return tgt.split(".", 1)[0]


class _State:
    def __init__(self, k, say):
        self.k = k
        self.say = say
        self.recs = {}        # txn -> {target: mode}
        self.by = ({}, {})    # records by target, and row records by table: see _index()
        self.wq = ({}, {})    # waiting requests by (target, mode) and by (table, mode)
        self.queue = []       # waiting requests [seq, txn, target, mode], seq ascending
        self.seq = 0
        self.gone = set()     # committed or dead

    # --- rules 1 to 3: what blocks a request -----------------------------------------

    def _index(self):
        """Records and waiting requests grouped by what they can conflict with, rebuilt from
        scratch whenever asked: records by exact target and, for rows, by table; requests by
        target and mode, and row requests by table and mode."""
        on = {}
        rows = {}
        for u, rs in self.recs.items():
            for t, m in rs.items():
                on.setdefault(t, []).append((u, m))
                if "." in t:
                    rows.setdefault(_table(t), []).append((u, m))
        self.by = (on, rows)
        at = {}
        under = {}
        for req in self.queue:
            at.setdefault((req[2], req[3]), []).append(req)
            if "." in req[2]:
                under.setdefault((_table(req[2]), req[3]), []).append(req)
        self.wq = (at, under)

    def _holders(self, txn, tgt, mode):
        """Rule 1: the other transactions holding a record that conflicts with (tgt, mode) -
        a record on the same target, on the table of a row, or on a row of a table, whose
        mode or the requested mode is exclusive."""
        on, rows = self.by
        found = set()
        pool = list(on.get(tgt, ()))
        if "." in tgt:
            pool += on.get(_table(tgt), ())
        else:
            pool += rows.get(tgt, ())
        for u, m in pool:
            if u != txn and (mode == "x" or m == "x"):
                found.add(u)
        return found

    def _holder_blocks(self, txn, tgt, mode):
        return bool(self._holders(txn, tgt, mode))

    def _earlier(self, seq, txn, tgt, mode):
        """The waiting requests before seq that conflict with (tgt, mode)."""
        at, under = self.wq
        table = _table(tgt)
        pool = list(at.get((tgt, "x"), ()))
        if mode == "x":
            pool += at.get((tgt, "s"), ())
        if "." in tgt:
            pool += at.get((table, "x"), ())
            if mode == "x":
                pool += at.get((table, "s"), ())
        else:
            pool += under.get((tgt, "x"), ())
            if mode == "x":
                pool += under.get((tgt, "s"), ())
        return [req for req in pool if req[1] != txn and req[0] < seq]

    def _relation(self):
        """Every waiting transaction to the transactions it waits on, hard and soft alike."""
        out = {}
        for seq, v, tgt, mode in self.queue:
            on = self._holders(v, tgt, mode)
            for req in self._earlier(seq, v, tgt, mode):
                on.add(req[1])
            out[v] = on
        return out

    @staticmethod
    def _closure(rel):
        """Everything each waiting transaction reaches, by Kosaraju's two passes.

        The first pass orders the waiting transactions by finishing time; the second walks
        the reversed relation in that order, which peels the strongly connected components
        off from the sources. Components come out in topological order, so each one is
        reached only by components already assigned, and a reversed accumulation gives every
        member the union of what its successors reach plus the successors themselves.
        """
        order = []
        seen = set()
        for start in rel:
            if start in seen:
                continue
            seen.add(start)
            todo = [(start, iter(rel[start]))]
            while todo:
                v, it = todo[-1]
                for u in it:
                    if u in rel and u not in seen:
                        seen.add(u)
                        todo.append((u, iter(rel[u])))
                        break
                else:
                    order.append(v)
                    todo.pop()
        back = {}
        for v, outs in rel.items():
            for u in outs:
                if u in rel:
                    back.setdefault(u, []).append(v)
        comp = {}
        comps = []
        for start in reversed(order):
            if start in comp:
                continue
            members = []
            todo = [start]
            comp[start] = len(comps)
            while todo:
                v = todo.pop()
                members.append(v)
                for u in back.get(v, ()):
                    if u not in comp:
                        comp[u] = len(comps)
                        todo.append(u)
            comps.append(members)
        reach = {}
        for members in reversed(comps):
            got = set(members) if len(members) > 1 else set()
            for v in members:
                for u in rel[v]:
                    got.add(u)
                    got |= reach.get(u, frozenset())
            for v in members:
                reach[v] = frozenset(got)
        return reach

    def _grantable(self, txn, tgt, mode, seq, reach=None):
        if self._holder_blocks(txn, tgt, mode):
            return False
        for _seq2, u, _t2, _m2 in self._earlier(seq, txn, tgt, mode):
            if reach is None:
                reach = self._closure(self._relation())
            if txn not in reach.get(u, ()):
                return False
        return True

    # --- rules 5 and 6: what a grant does to the records ---------------------------------

    def _covered(self, txn, tgt, mode):
        rs = self.recs[txn]
        for t in (tgt, _table(tgt)):
            m = rs.get(t)
            if m is not None and (m == "x" or mode == "s"):
                return True
        return False

    def _take(self, txn, tgt, mode):
        rs = self.recs[txn]
        if rs.get(tgt) != "x":
            rs[tgt] = mode
        if "." not in tgt:
            for t in [t for t in rs if "." in t and _table(t) == tgt]:
                if mode == "x" or rs[t] == "s":
                    del rs[t]

    # --- rules 7 and 8: escalation ---------------------------------------------------------

    def _escalate(self, txn, table):
        rs = self.recs[txn]
        rows = [m for t, m in rs.items() if "." in t and _table(t) == table]
        if len(rows) < self.k:
            return
        mode = "x" if "x" in rows else "s"
        have = rs.get(table)
        if have is not None and (have == "x" or mode == "s"):
            return
        self._index()
        if self._grantable(txn, table, mode, LATEST):
            self._take(txn, table, mode)
            self.say("esc %s %s %s" % (txn, table, mode))

    def _granted(self, txn, tgt, mode):
        self.say("grant %s %s %s" % (txn, tgt, mode))
        self._take(txn, tgt, mode)
        if "." in tgt:
            self._escalate(txn, _table(tgt))

    # --- rule 9: the victim ------------------------------------------------------------------

    def _victim(self):
        hard = {}
        for seq, v, tgt, mode in self.queue:
            hard[v] = self._holders(v, tgt, mode)
        reach = self._closure(hard)
        on_cycle = [v for v in hard if v in reach[v]]
        if not on_cycle:
            return None
        seq_of = {v: seq for seq, v, _t, _m in self.queue}
        return min(on_cycle, key=lambda v: (len(self.recs[v]), -seq_of[v]))

    def _finish(self, txn, word):
        n = len(self.recs[txn])
        self.say("%s %s %d" % (word, txn, n))
        self.recs[txn] = {}
        self.queue = [r for r in self.queue if r[1] != txn]
        self.gone.add(txn)

    # --- the ops, and rule 4 ---------------------------------------------------------------

    def lock(self, txn, tgt, mode):
        self.seq += 1
        self._index()
        if self._covered(txn, tgt, mode):
            self.say("grant %s %s %s" % (txn, tgt, mode))
            if "." in tgt:
                self._escalate(txn, _table(tgt))
        elif self._grantable(txn, tgt, mode, self.seq):
            self._granted(txn, tgt, mode)
        else:
            self.say("wait %s %s %s" % (txn, tgt, mode))
            self.queue.append([self.seq, txn, tgt, mode])

    def drop(self, txn, tgt):
        self.recs[txn].pop(tgt, None)

    def commit(self, txn):
        self._finish(txn, "end")

    def settle(self):
        while True:
            self._index()
            reach = None
            hit = None
            for req in self.queue:
                if self._holder_blocks(req[1], req[2], req[3]):
                    continue
                if reach is None:
                    reach = self._closure(self._relation())
                if self._grantable(req[1], req[2], req[3], req[0], reach):
                    hit = req
                    break
            if hit is not None:
                self.queue.remove(hit)
                self._granted(hit[1], hit[2], hit[3])
                continue
            v = self._victim()
            if v is None:
                return
            self._finish(v, "dead")

    def waiting(self, txn):
        return any(r[1] == txn for r in self.queue)


def expect(lines):
    """The whole trace of a script, as a list of lines."""
    k, order, ops = _parse(lines)
    out = []
    st = _State(k, out.append)
    for name in order:
        st.recs[name] = {}
    at = {name: 0 for name in order}
    while True:
        acted = False
        for name in order:
            if name in st.gone or st.waiting(name) or at[name] >= len(ops[name]):
                continue
            kind, tgt, mode = ops[name][at[name]]
            at[name] += 1
            if kind == "lock":
                st.lock(name, tgt, mode)
            elif kind == "drop":
                st.drop(name, tgt)
            else:
                st.commit(name)
            st.settle()
            acted = True
        if not acted:
            return out
