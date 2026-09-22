"""The sealed model: what every statement of a program has to print. Never shipped to the agent.

This file is the executable form of the frozen contract, written from the rules and not from the
reference solution. It keeps its undo state as one map of first before-images per open level
(the transaction, each savepoint, and the statement being run), which is a different structure
from the sequential journal the reference uses, so the two agreeing is evidence rather than
an echo.

The rules, in the order this file applies them:

  program     `table`, `check` and `fk` lines declare; `row` lines are committed rows; every
              other line is a statement and prints exactly one line.
  predicates  notnull: the column is null. min N: the column is not null and below N.
              fk: a child row violates when its column is not null and the parent has no row
              with that key; a parent key is left behind when no parent row has it and some
              child row holds it in the column.
  key         an insert of a key already present raises `key` on it at once.
  modes       each transaction starts from the declared modes; `set` changes deferrable ones;
              naming a constraint that is not deferrable is an error.
  writes      an insert, an update, or a setnull action writes a row; each write checks the row
              at once against every immediate check of its table, in declaration order.
  delete      removes the row, then goes over the keys referring to its table in declaration
              order, and for each over the rows holding the deleted key at that moment in key
              order: cascade deletes each the same way first, setnull writes null, restrict
              raises on the deleted key, noaction does nothing.
  stmt end    every immediate fk, in declaration order, looks at the rows of its table the
              statement wrote that are still there and at the keys of its parent the statement
              deleted, in first-touch order; the first violation raises. Then every deferred
              constraint, in declaration order, judges the rows of its table the statement
              touched and, for an fk, the keys of its parent the statement deleted or inserted:
              violated and owed nothing gains an entry, not violated and owed loses it.
  raise       a statement that raises leaves nothing behind and aborts the transaction.
  ledger      entries are ordered by declaration, then by when they were recorded.
  checkpoints set ... immediate and commit judge the entries they cover in ledger order; the
              first still violated raises and nothing changes (a commit also rolls back);
              otherwise they are all removed.
  savepoints  rollback to S restores rows, ledger (with every entry's place) and modes as they
              stood when the latest S was made; release S drops S and every later savepoint.
  aborted     only rollback, rollback to and commit act; commit rolls back and says so.
  output      ok lines list the entries removed (in the order they stood) and then the entries
              added (in ledger order); raise names constraint, table and key.
"""

MISSING = object()          # before-image of something that did not exist


class Raise(Exception):
    """A constraint raised: carries the constraint name, the table and the key it names."""

    def __init__(self, con, table, key):
        super().__init__(con, table, key)
        self.con, self.table, self.key = con, table, key


# --- the program ----------------------------------------------------------------------------

class Con:
    """One declared constraint: a check or an fk, with its place in declaration order."""

    def __init__(self, order, words):
        self.order = order
        self.kind = words[0]                          # "check" or "fk"
        self.name = words[1]
        self.table = words[2]
        self.col = words[3]
        rest = words[4:]
        if self.kind == "check":
            self.test = rest[0]                       # "notnull" or "min"
            self.floor = None
            if self.test == "min":
                self.floor = int(rest[1])
                rest = rest[2:]
            else:
                rest = rest[1:]
        else:
            self.parent = rest[0]
            self.action = rest[1]                     # cascade, setnull, restrict, noaction
            rest = rest[2:]
        self.deferrable = bool(rest) and rest[0] == "deferrable"
        self.starts_deferred = self.deferrable and len(rest) > 1 and rest[1] == "deferred"


def _value(word):
    return None if word == "-" else int(word)


def parse(lines):
    """Split a program into declarations, committed rows and statements."""
    tables, cons, rows, stmts = {}, [], [], []
    for line in lines:
        words = line.split()
        if not words:
            continue
        head = words[0]
        if head == "table":
            tables[words[1]] = words[2:]              # column names, key first
        elif head in ("check", "fk"):
            cons.append(Con(len(cons), words))
        elif head == "row":
            rows.append((words[1], int(words[2]), tuple(_value(w) for w in words[3:])))
        else:
            stmts.append(words)
    return tables, cons, rows, stmts


# --- the engine -----------------------------------------------------------------------------

class Level:
    """First before-images of everything changed since this level opened."""

    def __init__(self, name):
        self.name = name
        self.rows = {}          # (table, key) -> tuple of values, or MISSING
        self.owed = {}          # entry -> recording number, or MISSING
        self.modes = {}         # constraint name -> "d" or "i"

    def clear(self):
        self.rows.clear()
        self.owed.clear()
        self.modes.clear()


class Engine:
    def __init__(self, tables, cons, rows):
        self.cols = {t: {c: i for i, c in enumerate(cs[1:])} for t, cs in tables.items()}
        self.cons = cons
        self.by_name = {c.name: c for c in cons}
        self.checks_of = {t: [c for c in cons if c.kind == "check" and c.table == t] for t in tables}
        self.refs_to = {t: [c for c in cons if c.kind == "fk" and c.parent == t] for t in tables}
        self.fks_of = {t: [c for c in cons if c.kind == "fk" and c.table == t] for t in tables}
        self.data = {t: {} for t in tables}
        self.held = {c.name: {} for c in cons if c.kind == "fk"}   # key -> child keys holding it
        for t, k, vals in rows:
            self._raw(t, k, vals)
        self.open = False
        self.aborted = False
        self.levels = []
        self.owed = {}          # (con, table, key) -> recording number
        self.mode = {}
        self.clock = 0
        self.touch = []
        self.flags = {}

    # --- raw state changes, each noting its first before-image in the top level -----------

    def _raw(self, t, k, vals):
        """Set or remove a row and keep the holder index in step. Records nothing."""
        old = self.data[t].get(k)
        for f in self.fks_of[t]:
            i = self.cols[t][f.col]
            if old is not None and old[i] is not None:
                self.held[f.name][old[i]].discard(k)
            if vals is not None and vals[i] is not None:
                self.held[f.name].setdefault(vals[i], set()).add(k)
        if vals is None:
            self.data[t].pop(k, None)
        else:
            self.data[t][k] = vals

    def _put(self, t, k, vals):
        top = self.levels[-1]
        if (t, k) not in top.rows:
            top.rows[(t, k)] = self.data[t].get(k, MISSING)
        self._raw(t, k, vals)

    def _owe(self, entry, number):
        top = self.levels[-1]
        if entry not in top.owed:
            top.owed[entry] = self.owed.get(entry, MISSING)
        if number is None:
            del self.owed[entry]
        else:
            self.owed[entry] = number

    def _set_mode(self, name, m):
        top = self.levels[-1]
        if name not in top.modes:
            top.modes[name] = self.mode[name]
        self.mode[name] = m

    def _undo(self, level):
        """Put back every before-image a level holds, then empty it."""
        for (t, k), vals in level.rows.items():
            self._raw(t, k, None if vals is MISSING else vals)
        for entry, number in level.owed.items():
            if number is MISSING:
                self.owed.pop(entry, None)
            else:
                self.owed[entry] = number
        for name, m in level.modes.items():
            self.mode[name] = m
        level.clear()

    def _fold(self, upper, lower):
        """Hand an upper level's before-images to the one below; the lower keeps its older ones."""
        for key, v in upper.rows.items():
            lower.rows.setdefault(key, v)
        for key, v in upper.owed.items():
            lower.owed.setdefault(key, v)
        for key, v in upper.modes.items():
            lower.modes.setdefault(key, v)

    # --- predicates -------------------------------------------------------------------------

    def _row_bad(self, c, t, k):
        """Does row k of table t violate constraint c (as a check, or as the child of an fk)?"""
        row = self.data[t].get(k)
        if row is None:
            return False
        v = row[self.cols[t][c.col]]
        if c.kind == "check":
            if c.test == "notnull":
                return v is None
            return v is not None and v < c.floor
        return v is not None and v not in self.data[c.parent]

    def _left_behind(self, c, k):
        return k not in self.data[c.parent] and bool(self.held[c.name].get(k))

    def _still_bad(self, entry):
        name, t, k = entry
        c = self.by_name[name]
        if c.kind == "fk" and t == c.parent:
            return self._left_behind(c, k)
        return self._row_bad(c, t, k)

    def _place(self, entry):
        return (self.by_name[entry[0]].order, self.owed[entry])

    # --- one statement's writes -------------------------------------------------------------

    def _mark(self, t, k, flag):
        key = (t, k)
        if key not in self.flags:
            self.flags[key] = set()
            self.touch.append(key)
        self.flags[key].add(flag)

    def _write(self, t, k, vals):
        self._put(t, k, vals)
        self._mark(t, k, "w")
        for c in self.checks_of[t]:
            if self.mode[c.name] == "i" and self._row_bad(c, t, k):
                raise Raise(c.name, t, k)

    def _delete(self, t, k):
        self._put(t, k, None)
        self._mark(t, k, "d")
        for f in self.refs_to[t]:
            holders = sorted(self.held[f.name].get(k, ()))
            if f.action == "restrict":
                if holders:
                    raise Raise(f.name, t, k)
            elif f.action == "cascade":
                for c in holders:
                    if c in self.data[f.table]:
                        self._delete(f.table, c)
            elif f.action == "setnull":
                i = self.cols[f.table][f.col]
                for c in holders:
                    row = self.data[f.table].get(c)
                    if row is not None and row[i] == k:
                        self._write(f.table, c, row[:i] + (None,) + row[i + 1:])

    def _end_immediate(self):
        for f in self.cons:
            if f.kind != "fk" or self.mode[f.name] != "i":
                continue
            for t, k in self.touch:
                flags = self.flags[(t, k)]
                if t == f.table and "w" in flags and k in self.data[t]:
                    if self._row_bad(f, t, k):
                        raise Raise(f.name, t, k)
                elif t == f.parent and "d" in flags:
                    if self._left_behind(f, k):
                        raise Raise(f.name, t, k)

    def _end_deferred(self):
        gone, came = [], []

        def settle(entry, bad):
            if bad and entry not in self.owed:
                self.clock += 1
                self._owe(entry, self.clock)
                came.append(entry)
            elif not bad and entry in self.owed:
                gone.append((self._place(entry), entry))
                self._owe(entry, None)

        for c in self.cons:
            if self.mode[c.name] != "d":
                continue
            for t, k in self.touch:
                flags = self.flags[(t, k)]
                if t == c.table:
                    settle((c.name, t, k), self._row_bad(c, t, k))
                elif c.kind == "fk" and t == c.parent and ("d" in flags or "i" in flags):
                    settle((c.name, t, k), self._left_behind(c, k))
        gone.sort()
        came.sort(key=self._place)
        return [e for _, e in gone], came

    def _dml(self, words):
        self.levels.append(Level("#statement"))
        self.touch, self.flags = [], {}
        try:
            op, t, k = words[0], words[1], int(words[2])
            if op == "insert":
                if k in self.data[t]:
                    raise Raise("key", t, k)
                self._mark(t, k, "i")
                self._write(t, k, tuple(_value(w) for w in words[3:]))
            elif op == "update":
                row = self.data[t].get(k)
                if row is not None:
                    vals = list(row)
                    for i in range(3, len(words), 2):
                        vals[self.cols[t][words[i]]] = _value(words[i + 1])
                    self._write(t, k, tuple(vals))
            else:
                if k in self.data[t]:
                    self._delete(t, k)
            self._end_immediate()
        except Raise as r:
            self._undo(self.levels.pop())
            self.aborted = True
            return "raise %s %s %d" % (r.con, r.table, r.key)
        gone, came = self._end_deferred()
        self._fold(self.levels.pop(), self.levels[-1])
        return _ok(gone, came)

    # --- check points ------------------------------------------------------------------------

    def _settle(self, names):
        """Judge the entries of these constraints in ledger order; raise on the first still bad."""
        mine = sorted((e for e in self.owed if e[0] in names), key=self._place)
        for entry in mine:
            if self._still_bad(entry):
                raise Raise(*entry)
        return mine

    def _set(self, target, want):
        if target == "all":
            names = [c.name for c in self.cons if c.deferrable]
        else:
            c = self.by_name[target]
            if not c.deferrable:
                self.aborted = True
                return "error"
            names = [c.name]
        gone = []
        if want == "immediate":
            try:
                gone = self._settle(set(names))
            except Raise as r:
                self.aborted = True
                return "raise %s %s %d" % (r.con, r.table, r.key)
            for entry in gone:
                self._owe(entry, None)
        for name in names:
            self._set_mode(name, "i" if want == "immediate" else "d")
        return _ok(gone, [])

    def _close(self):
        """Roll every open level back into the committed state and end the transaction."""
        while self.levels:
            self._undo(self.levels.pop())
        self.open = False
        self.aborted = False

    def _find(self, name):
        for i in range(len(self.levels) - 1, 0, -1):
            if self.levels[i].name == name:
                return i
        return None

    # --- one statement --------------------------------------------------------------------------

    def step(self, words):
        op = words[0]
        if op == "begin":
            self.open, self.aborted = True, False
            self.levels = [Level(None)]
            self.owed = {}
            self.mode = {c.name: ("d" if c.starts_deferred else "i") for c in self.cons}
            return "ok"
        if op == "rollback" and len(words) == 1:
            everything = sorted(self.owed, key=self._place)
            self._close()
            return _ok(everything, [])
        if op == "commit":
            if self.aborted:
                self._close()
                return "rollback"
            try:
                everything = self._settle({c.name for c in self.cons})
            except Raise as r:
                self._close()
                return "raise %s %s %d" % (r.con, r.table, r.key)
            self.levels = []
            self.owed = {}
            self.open = False
            return _ok(everything, [])
        if op == "rollback":
            return self._rollback_to(words[2])
        if self.aborted:
            return "aborted"
        if op == "savepoint":
            self.levels.append(Level(words[1]))
            return "ok"
        if op == "release":
            i = self._find(words[1])
            if i is None:
                self.aborted = True
                return "error"
            while len(self.levels) > i:
                self._fold(self.levels.pop(), self.levels[-1])
            return "ok"
        if op == "set":
            return self._set(words[1], words[2])
        return self._dml(words)

    def _rollback_to(self, name):
        i = self._find(name)
        if i is None:
            self.aborted = True
            return "error"
        # Only entries some undone level holds a before-image for can change, so the listing is
        # worked out over those alone: which of them stand now, and where.
        touched = set()
        for level in self.levels[i:]:
            touched.update(level.owed)
        before = {e: self._place(e) for e in touched if e in self.owed}
        while len(self.levels) > i + 1:
            self._undo(self.levels.pop())
        self._undo(self.levels[i])
        self.aborted = False
        gone = sorted((e for e in before if e not in self.owed), key=before.get)
        came = sorted((e for e in touched if e in self.owed and e not in before), key=self._place)
        return _ok(gone, came)


def _ok(gone, came):
    parts = ["ok"]
    parts.extend("-%s %s %d" % e for e in gone)
    parts.extend("+%s %s %d" % e for e in came)
    return " ".join(parts)


def expect(lines):
    """The lines a correct executor prints for one program, given as a list of lines."""
    tables, cons, rows, stmts = parse(lines)
    eng = Engine(tables, cons, rows)
    return [eng.step(words) for words in stmts]
