"""Graded programs generated from a seed drawn after the agent's container is gone.

Every program is a schema, committed rows that satisfy it, and a run of transactions. The
statement language is total - an update or delete of a missing key does nothing, an insert of a
present key raises, a savepoint name that does not exist is an error - so this file never needs
to know what a program will print, and it holds nothing that could compute an answer. It only
decides where programs go.

A random walk over statements hardly ever builds the situations the contract turns on, so
programs are assembled from motifs, each one the smallest run of statements that makes one
interaction happen, padded with ordinary statements around it. Motif rows use fresh keys above
the committed ones, so a motif does what it was built to do however the rest of the program
went. The motifs:

  mend      a child written against a missing key, the key inserted elsewhere, a check later
  behind    a held parent deleted under a noaction key, then the key or its holders moved
  replace   an entry cleared and re-recorded after a savepoint that is then rolled back to,
            with another entry recorded in between, so only its old place decides the order
  order     two deferred constraints owing entries in the reverse of their declaration order
  failset   a check point that raises inside a savepoint, recovered by rolling back to it
  modeback  a mode switched after a savepoint that a rollback then restores
  shadow    two savepoints with one name, releases and repeated rollbacks
  walk      a delete over keys with different actions, two levels deep, with a row check
            (the walk family has its own builder, fam_walk, shaped for the walk readings)
  abort     a raise or an error followed by statements the aborted transaction ignores
  edge      min at its floor and below it, null under min, missing and present keys

Families weight the motifs differently. The two scale families exist for the execution limit:
an executor that copies its rows or its ledger at a savepoint, or scans a table for the rows
holding a key, is exactly correct on them and cannot finish in time.
"""
import random

SMALL = ("lazy", "side", "walk", "order", "rewind", "mode", "abort", "edge", "mix")
FAMILIES = tuple((f, False) for f in SMALL) + (("wrap", True), ("load", True))
BIG_EACH = 3
FRESH = 30          # motif keys start above every committed key


def _w(v):
    return "-" if v is None else str(v)


# --- schemas ---------------------------------------------------------------------------------

class Schema:
    """Tables with value columns, and constraints in declaration order."""

    def __init__(self):
        self.tables = []            # (name, [value columns])
        self.cons = []              # dicts in declaration order

    def names(self):
        return [t for t, _ in self.tables]

    def cols(self, t):
        return dict(self.tables)[t]

    def fks(self):
        return [c for c in self.cons if c["kind"] == "fk"]

    def checks(self):
        return [c for c in self.cons if c["kind"] == "check"]

    def fks_from(self, t):
        return [c for c in self.fks() if c["table"] == t]

    def fks_into(self, t):
        return [c for c in self.fks() if c["parent"] == t]

    def checks_on(self, t):
        return [c for c in self.checks() if c["table"] == t]

    def deferrable(self):
        return [c["name"] for c in self.cons if c["deferrable"]]

    def lines(self):
        out = ["table %s k %s" % (t, " ".join(cs)) for t, cs in self.tables]
        for c in self.cons:
            tail = ""
            if c["deferrable"]:
                tail = " deferrable deferred" if c["deferred"] else " deferrable"
            if c["kind"] == "check":
                test = "notnull" if c["test"] == "notnull" else "min %d" % c["floor"]
                out.append("check %s %s %s %s%s" % (c["name"], c["table"], c["col"], test, tail))
            else:
                out.append("fk %s %s %s %s %s%s" % (c["name"], c["table"], c["col"],
                                                   c["parent"], c["action"], tail))
        return out


def _mode(rng, p_def, p_deferred):
    d = rng.random() < p_def
    return d, d and rng.random() < p_deferred


def schema(rng, ntab=(2, 4), actions=("cascade", "setnull", "restrict", "noaction"),
           p_def=0.6, p_deferred=0.6, nchk=(1, 3), nfk=(1, 4), cycle=0.15, twin=0.25):
    """Foreign keys point from later tables to earlier ones, with at most one pointing back,
    so committed rows can always be built. `twin` is the chance of a second key from one child
    table to the same parent, which is what makes the action walk order matter."""
    s = Schema()
    n = rng.randint(*ntab)
    names = ["t%d" % i for i in range(n)]
    for i, t in enumerate(names):
        s.tables.append((t, list("uvw"[:rng.randint(2, 3) if i else 2])))
    used = set()
    seq = [0]

    def name(prefix):
        seq[0] += 1
        return "%s%d" % (prefix, seq[0])

    def add_fk(child, parent, back=False):
        free = [c for c in s.cols(child) if (child, c) not in used]
        if not free:
            return None
        col = rng.choice(free)
        used.add((child, col))
        pool = [a for a in actions if not (back and a == "restrict")] or ["noaction"]
        act = rng.choice(pool)
        d, dd = _mode(rng, 0.0 if act == "restrict" else p_def, p_deferred)
        c = dict(kind="fk", name=name("f"), table=child, col=col, parent=parent, action=act,
                 deferrable=d, deferred=dd, back=back)
        s.cons.append(c)
        return c

    if n > 1:
        for _ in range(rng.randint(*nfk)):
            child = rng.randrange(1, n)
            f = add_fk(names[child], names[rng.randrange(0, child)])
            if f and rng.random() < twin:
                add_fk(f["table"], f["parent"])
        if rng.random() < cycle:
            parent = rng.randrange(1, n)
            add_fk(names[rng.randrange(0, parent)], names[parent], back=True)
    for _ in range(rng.randint(*nchk)):
        t = rng.choice(names)
        col = rng.choice(s.cols(t))
        back = any(c["back"] and c["table"] == t and c["col"] == col for c in s.fks())
        if rng.random() < 0.5 and not back:
            test, floor = "notnull", None
        else:
            test, floor = "min", rng.randint(0, 3)
        d, dd = _mode(rng, p_def, p_deferred)
        s.cons.append(dict(kind="check", name=name("c"), table=t, col=col, test=test,
                           floor=floor, deferrable=d, deferred=dd))
    rng.shuffle(s.cons)
    return s


def ensure(rng, s, kind, **want):
    """Make sure the schema has a constraint of this shape, adding one if it does not. Only
    called while the schema is being prepared, before any committed row exists."""
    for c in s.cons:
        if c["kind"] == kind and all(c.get(k) == v for k, v in want.items()):
            return c
    names = s.names()
    if kind == "fk":
        if len(names) < 2:
            return None
        parent = want.get("parent")
        if parent is None:
            ci = rng.randrange(1, len(names))
            parent = names[rng.randrange(0, ci)]
        else:
            pi = names.index(parent)
            if pi == len(names) - 1:
                return None
            ci = rng.randrange(pi + 1, len(names))
        child = names[ci]
        busy = {(c["table"], c["col"]) for c in s.fks()}
        free = [c for c in s.cols(child) if (child, c) not in busy]
        if not free:
            s.tables = [(t, cs + ["x%d" % len(cs)] if t == child else cs) for t, cs in s.tables]
            free = [s.cols(child)[-1]]
        action = want.get("action", "noaction")
        deferrable = want.get("deferrable", True) and action != "restrict"
        c = dict(kind="fk", name="f%d" % (90 + len(s.cons)), table=child, col=free[0],
                 parent=parent, action=action, deferrable=deferrable,
                 deferred=deferrable and want.get("deferred", True), back=False)
    else:
        t = want.get("table") or rng.choice(names)
        col = rng.choice(s.cols(t))
        test = want.get("test", rng.choice(("min", "notnull")))
        if any(f["back"] and f["table"] == t and f["col"] == col for f in s.fks()):
            test = "min"
        deferrable = want.get("deferrable", True)
        c = dict(kind="check", name="c%d" % (90 + len(s.cons)), table=t, col=col, test=test,
                 floor=want.get("floor", 1) if test == "min" else None, deferrable=deferrable,
                 deferred=deferrable and want.get("deferred", True))
    s.cons.insert(rng.randrange(0, len(s.cons) + 1), c)
    return c


def prepare(fam, rng, s):
    """Give a family's schema the constraints its motifs need, before any row is built."""
    def some_fk(**want):
        return ensure(rng, s, "fk", **want)

    if fam in ("lazy", "mix"):
        if not any(f["deferrable"] and f["action"] != "restrict" for f in s.fks()):
            some_fk(action=rng.choice(("noaction", "cascade", "setnull")), deferrable=True)
    if fam in ("side", "mix"):
        if not any(f["action"] == "noaction" for f in s.fks()):
            some_fk(action="noaction", deferrable=True, deferred=rng.random() < 0.8)
    if fam in ("order", "rewind", "mode", "mix"):
        if not any(c["deferrable"] for c in s.checks()):
            ensure(rng, s, "check", deferrable=True)
        if len([c for c in s.cons if c["deferrable"]]) < 2:
            some_fk(action=rng.choice(("noaction", "setnull")), deferrable=True)
    if fam in ("abort", "mix"):
        if not s.checks():
            ensure(rng, s, "check", deferrable=False)
    if fam in ("edge", "mix"):
        if not any(c["test"] == "min" for c in s.checks()):
            ensure(rng, s, "check", test="min", floor=rng.randint(1, 3),
                   deferrable=rng.random() < 0.5)
    if fam == "mix":
        top = s.names()[0]
        for _ in range(4):
            if len(s.fks_into(top)) >= 2:
                break
            act = rng.choice(("cascade", "setnull", "restrict", "noaction"))
            f = ensure(rng, s, "fk", parent=top, action=act,
                       deferrable=act != "restrict" and rng.random() < 0.4,
                       deferred=rng.random() < 0.5)
            if f is None:
                break
        mid = s.names()[1] if len(s.names()) > 2 else None
        if mid is not None and not s.fks_into(mid):
            ensure(rng, s, "fk", parent=mid, action=rng.choice(("cascade", "setnull", "noaction")),
                   deferrable=rng.random() < 0.4)
        setnulls = [f for f in s.fks() if f["action"] == "setnull"]
        if setnulls and rng.random() < 0.6:
            f = rng.choice(setnulls)
            if not any(c["table"] == f["table"] and c["col"] == f["col"] for c in s.checks()):
                s.cons.insert(rng.randrange(0, len(s.cons) + 1),
                              dict(kind="check", name="c%d" % (90 + len(s.cons)),
                                   table=f["table"], col=f["col"], test="notnull", floor=None,
                                   deferrable=rng.random() < 0.5, deferred=rng.random() < 0.5))


# --- committed rows ----------------------------------------------------------------------------

def _fits(s, t, col, v):
    for c in s.checks_on(t):
        if c["col"] != col:
            continue
        if c["test"] == "notnull" and v is None:
            return False
        if c["test"] == "min" and v is not None and v < c["floor"]:
            return False
    return True


def committed(rng, s, per=(3, 6), keyspace=12):
    """Rows for every table, parents first, that satisfy every constraint."""
    have = {t: set() for t in s.names()}
    held = {}                       # (fk name, parent key) -> child keys
    lines = []
    for t, cs in s.tables:
        refs = {c["col"]: c for c in s.fks_from(t)}
        for k in sorted(rng.sample(range(1, keyspace + 1), rng.randint(*per))):
            vals = []
            for col in cs:
                c = refs.get(col)
                if c is not None:
                    pool = sorted(have[c["parent"]]) if not c["back"] else []
                    v = rng.choice(pool) if pool and rng.random() < 0.85 else None
                    if v is None and not _fits(s, t, col, None) and pool:
                        v = rng.choice(pool)
                else:
                    v = rng.randint(0, 6)
                vals.append(v)
            if all(_fits(s, t, col, v) for col, v in zip(cs, vals)):
                have[t].add(k)
                for col, v in zip(cs, vals):
                    if col in refs and v is not None:
                        held.setdefault((refs[col]["name"], v), set()).add(k)
                lines.append("row %s %d %s" % (t, k, " ".join(_w(v) for v in vals)))
    return lines, have, held


# --- the writer --------------------------------------------------------------------------------

class Writer:
    """Emits statements, keeps a rough idea of which keys exist (for aim only), and hands out
    fresh keys for motif rows."""

    def __init__(self, rng, s, have, held):
        self.rng, self.s = rng, s
        self.keys = {t: set(ks) for t, ks in have.items()}
        self.held = {k: set(v) for k, v in held.items()}
        self.next = {t: FRESH + rng.randint(0, 5) for t in s.names()}
        self.out = []
        self.sp = []
        self.intx = False

    def emit(self, line):
        self.out.append(line)

    def fresh(self, t):
        self.next[t] += self.rng.randint(1, 3)
        return self.next[t]

    def known(self, t, fallback=True):
        pool = sorted(self.keys[t])
        if pool:
            return self.rng.choice(pool)
        return self.rng.randint(1, 12) if fallback else None

    def good(self, t, col):
        """A value that satisfies every check on the column and points at a key believed to
        exist, or null where null is allowed."""
        rng = self.rng
        ref = next((c for c in self.s.fks_from(t) if c["col"] == col), None)
        if ref is not None:
            if _fits(self.s, t, col, None) and rng.random() < 0.3:
                return None
            k = self.known(ref["parent"], fallback=False)
            if k is not None and _fits(self.s, t, col, k):
                return k
            return None if _fits(self.s, t, col, None) else (k or 1)
        for _ in range(12):
            v = rng.randint(0, 6)
            if _fits(self.s, t, col, v):
                return v
        return 9

    def bad(self, t, col):
        """A value that violates something on the column, if anything can be violated there."""
        ref = next((c for c in self.s.fks_from(t) if c["col"] == col), None)
        chk = [c for c in self.s.checks_on(t) if c["col"] == col]
        opts = []
        if ref is not None:
            opts.append(self.fresh(ref["parent"]) + 1000)
        for c in chk:
            opts.append(None if c["test"] == "notnull" else c["floor"] - 1)
        return self.rng.choice(opts) if opts else self.good(t, col)

    def row(self, t, over=None):
        over = over or {}
        return [over[c] if c in over else self.good(t, c) for c in self.s.cols(t)]

    def insert(self, t, k=None, over=None):
        k = self.fresh(t) if k is None else k
        vals = self.row(t, over)
        self.emit("insert %s %d %s" % (t, k, " ".join(_w(v) for v in vals)))
        self.keys[t].add(k)
        for c in self.s.fks_from(t):
            v = vals[self.s.cols(t).index(c["col"])]
            if v is not None:
                self.held.setdefault((c["name"], v), set()).add(k)
        return k

    def update(self, t, k, col, v):
        self.emit("update %s %d %s %s" % (t, k, col, _w(v)))

    def delete(self, t, k):
        self.emit("delete %s %d" % (t, k))
        self.keys[t].discard(k)

    # ordinary statements between motifs
    def noise(self, n=1):
        rng, s = self.rng, self.s
        for _ in range(n):
            t = rng.choice(s.names())
            r = rng.random()
            if r < 0.4:
                self.insert(t)
            elif r < 0.75:
                k = self.known(t)
                col = rng.choice(s.cols(t))
                if rng.random() < 0.85:
                    self.update(t, k, col, self.good(t, col))
                else:
                    self.guard(lambda: self.update(t, k, col, self.bad(t, col)), keep=0.4)
            else:
                self.guard(lambda: self.delete(t, self.known(t)), keep=0.5)

    def guard(self, body, keep=0.6):
        """Wrap a statement the way a client does: a savepoint, the statement, then either a
        release or a rollback to it, so a raise does not leave the whole transaction dead."""
        name = self.rng.choice(("g", "h"))
        self.emit("savepoint %s" % name)
        body()
        if self.rng.random() < keep:
            self.emit("release %s" % name)
        else:
            self.emit("rollback to %s" % name)

    def savepoint(self, name=None):
        name = name or self.rng.choice("abc")
        self.emit("savepoint %s" % name)
        self.sp.append(name)
        return name

    def _drop_after(self, name, keep):
        if name in self.sp:
            i = len(self.sp) - 1 - self.sp[::-1].index(name)
            del self.sp[i + (1 if keep else 0):]

    def release(self, name):
        self.emit("release %s" % name)
        self._drop_after(name, keep=False)

    def rollback_to(self, name):
        self.emit("rollback to %s" % name)
        self._drop_after(name, keep=True)

    def set(self, target, want):
        self.emit("set %s %s" % (target, want))

    def check_point(self):
        """One of the ways a transaction settles what it owes, usually guarded the way a client
        guards anything that can raise."""
        rng = self.rng
        defer = self.s.deferrable()
        target = "all" if rng.random() < 0.55 or not defer else rng.choice(defer)
        r = rng.random()
        if r < 0.3:
            self.set(target, "immediate")
            return
        name = self.savepoint("q")
        self.set(target, "immediate")
        if r < 0.55:
            self.release(name)
        else:
            self.rollback_to(name)

    def begin(self):
        self.emit("begin")
        self.sp = []

    def end(self, commit=0.75):
        self.emit("commit" if self.rng.random() < commit else "rollback")
        self.sp = []


def _fk(rng, s, **want):
    pool = [c for c in s.fks() if all(c.get(k) == v for k, v in want.items())]
    return rng.choice(pool) if pool else None


def _check(rng, s, **want):
    pool = [c for c in s.checks() if all(c.get(k) == v for k, v in want.items())]
    return rng.choice(pool) if pool else None


def _deferred(w, c):
    """Make sure a deferrable constraint is deferred for what follows."""
    if c["deferrable"] and (not c["deferred"] or w.rng.random() < 0.2):
        w.set(c["name"], "deferred")


# --- motifs ------------------------------------------------------------------------------------

def m_mend(w):
    rng, s = w.rng, w.s
    pool = [f for f in s.fks() if f["deferrable"] and f["action"] != "restrict"]
    if not pool:
        return w.noise(2)
    f = rng.choice(pool)
    _deferred(w, f)
    kp = w.fresh(f["parent"])
    kc = w.insert(f["table"], over={f["col"]: kp})
    w.noise(rng.randint(0, 2))
    w.insert(f["parent"], k=kp)
    w.noise(rng.randint(0, 2))
    r = rng.random()
    if r < 0.25:
        w.update(f["table"], kc, f["col"], kp)
    elif r < 0.75:
        w.check_point()
    elif r < 0.9:
        name = w.savepoint()
        w.set("all", "immediate")
        w.noise(rng.randint(0, 1))
        w.rollback_to(name)


def m_behind(w):
    rng, s = w.rng, w.s
    f = _fk(rng, s, action="noaction")
    if f is None:
        return w.noise(2)
    if f["deferrable"]:
        _deferred(w, f)
    kp = w.insert(f["parent"])
    kids = [w.insert(f["table"], over={f["col"]: kp}) for _ in range(rng.randint(1, 3))]
    w.noise(rng.randint(0, 1))
    w.guard(lambda: w.delete(f["parent"], kp), keep=0.85 if f["deferred"] else 0.3)
    w.noise(rng.randint(0, 2))
    r = rng.random()
    if r < 0.3:
        w.insert(f["parent"], k=kp)
    elif r < 0.6:
        for kc in kids:
            if rng.random() < 0.7:
                w.update(f["table"], kc, f["col"], w.good(f["table"], f["col"]))
    elif r < 0.8:
        for kc in kids:
            w.delete(f["table"], kc)
    if rng.random() < 0.7:
        w.check_point()


def m_replace(w):
    rng, s = w.rng, w.s
    c = _check(rng, s, deferrable=True)
    if c is None:
        return w.noise(2)
    _deferred(w, c)
    t, col = c["table"], c["col"]
    badv = None if c["test"] == "notnull" else c["floor"] - 1
    goodv = w.good(t, col)
    ka = w.insert(t, over={col: badv})
    kb = w.insert(t, over={col: badv})
    name = w.savepoint()
    w.update(t, ka, col, goodv)
    w.noise(rng.randint(0, 1))
    w.update(t, ka, col, badv)
    if rng.random() < 0.5:
        w.update(t, kb, col, goodv)
    w.rollback_to(name)
    r = rng.random()
    if r < 0.5:
        w.set("all", "immediate")
    elif r < 0.8:
        w.set(c["name"], "immediate")
    else:
        w.update(t, kb, col, goodv)
        w.update(t, ka, col, goodv)


def m_order(w):
    rng, s = w.rng, w.s
    cands = [c for c in s.cons if c["deferrable"]]
    if len(cands) < 2:
        return w.noise(2)
    a, b = rng.sample(cands, 2)
    first, later = sorted((a, b), key=s.cons.index)
    for c in (later, first):
        _deferred(w, c)
    for c in (later, first):
        if c["kind"] == "check":
            badv = None if c["test"] == "notnull" else c["floor"] - 1
            w.insert(c["table"], over={c["col"]: badv})
        else:
            w.insert(c["table"], over={c["col"]: w.fresh(c["parent"]) + 1000})
    w.noise(rng.randint(0, 1))
    w.check_point()


def m_failset(w):
    rng, s = w.rng, w.s
    c = _check(rng, s, deferrable=True)
    if c is None:
        return w.noise(2)
    _deferred(w, c)
    # A mended entry of a key declared ahead of the check, so the failing check point passes
    # over a satisfied entry before it reaches the violated one: only a check point that
    # changes nothing when it raises leaves that entry where it was.
    ahead = [f for f in s.fks() if f["deferrable"] and f["action"] != "restrict"
             and s.cons.index(f) < s.cons.index(c)]
    if ahead and rng.random() < 0.8:
        f = rng.choice(ahead)
        _deferred(w, f)
        kp = w.fresh(f["parent"])
        w.insert(f["table"], over={f["col"]: kp})
        w.insert(f["parent"], k=kp)
    badv = None if c["test"] == "notnull" else c["floor"] - 1
    k = w.insert(c["table"], over={c["col"]: badv})
    name = w.savepoint()
    w.set(rng.choice(("all", c["name"])), "immediate")
    w.noise(rng.randint(1, 2))
    w.rollback_to(name)
    w.insert(c["table"], over={c["col"]: badv})
    if rng.random() < 0.5:
        w.update(c["table"], k, c["col"], w.good(c["table"], c["col"]))


def m_modeback(w):
    rng, s = w.rng, w.s
    c = _check(rng, s, deferrable=True) if rng.random() < 0.5 else _fk(rng, s, deferrable=True)
    if c is None:
        return w.noise(2)
    name = w.savepoint()
    w.set(c["name"], rng.choice(("immediate", "deferred")))
    w.noise(rng.randint(0, 1))
    w.rollback_to(name)
    if c["kind"] == "check":
        badv = None if c["test"] == "notnull" else c["floor"] - 1
        w.guard(lambda: w.insert(c["table"], over={c["col"]: badv}), keep=0.7)
    else:
        w.guard(lambda: w.insert(c["table"], over={c["col"]: w.fresh(c["parent"]) + 1000}),
                keep=0.7)


def m_shadow(w):
    rng = w.rng
    w.savepoint("a")
    w.noise(rng.randint(1, 2))
    w.savepoint("a")
    w.noise(rng.randint(1, 2))
    r = rng.random()
    if r < 0.4:
        w.release("a")
        w.noise(1)
        w.rollback_to("a")
    elif r < 0.7:
        w.rollback_to("a")
        w.noise(1)
        w.rollback_to("a")
        w.release("a")
    else:
        w.release("a")
        w.release("a")
        w.emit("rollback to a")


def m_walk(w):
    rng, s = w.rng, w.s
    into = [t for t in s.names() if s.fks_into(t)]
    if not into:
        return w.noise(2)
    top = rng.choice(into)
    kp = w.insert(top)
    for f in s.fks_into(top):
        for _ in range(rng.randint(0, 2)):
            kc = w.insert(f["table"], over={f["col"]: kp})
            for g in s.fks_into(f["table"]):
                if rng.random() < 0.5:
                    w.insert(g["table"], over={g["col"]: kc})
    w.noise(rng.randint(0, 1))
    w.guard(lambda: w.delete(top, kp), keep=0.45)


def m_abort(w):
    rng, s = w.rng, w.s
    r = rng.random()
    t = rng.choice(s.names())
    if r < 0.3:
        k = w.known(t)
        w.emit("insert %s %d %s" % (t, k, " ".join(_w(v) for v in w.row(t))))
    elif r < 0.55:
        c = _check(rng, s)
        if c is not None:
            badv = None if c["test"] == "notnull" else c["floor"] - 1
            w.insert(c["table"], over={c["col"]: badv})
    elif r < 0.75:
        w.emit("rollback to zz")
    else:
        nd = [c["name"] for c in s.cons if not c["deferrable"]]
        w.set(rng.choice(nd) if nd else "all", rng.choice(("deferred", "immediate")))
    w.noise(rng.randint(1, 2))
    if w.sp and rng.random() < 0.6:
        w.rollback_to(w.sp[-1])


def m_edge(w):
    rng, s = w.rng, w.s
    c = _check(rng, s, test="min")
    if c is None:
        return w.noise(2)
    t, col = c["table"], c["col"]
    k = w.insert(t)
    for v in rng.sample([c["floor"], c["floor"] - 1, None, c["floor"] + 1], 3):
        w.guard(lambda v=v: w.update(t, k, col, v), keep=0.7)
    r = rng.random()
    if r < 0.4:
        w.update(t, w.fresh(t) + 2000, col, 1)
    elif r < 0.7:
        w.delete(t, w.fresh(t) + 2000)
    else:
        w.guard(lambda: w.emit("insert %s %d %s" % (t, k, " ".join(_w(v) for v in w.row(t)))))


MOTIFS = {
    "mend": m_mend, "behind": m_behind, "replace": m_replace, "order": m_order,
    "failset": m_failset, "modeback": m_modeback, "shadow": m_shadow, "walk": m_walk,
    "abort": m_abort, "edge": m_edge,
}

WEIGHTS = {
    "lazy": {"mend": 6, "replace": 1, "order": 1, "behind": 1},
    "side": {"behind": 6, "mend": 1, "order": 1},
    "order": {"order": 4, "replace": 4, "mend": 1},
    "rewind": {"shadow": 3, "replace": 3, "failset": 2, "modeback": 1},
    "mode": {"modeback": 4, "failset": 4, "order": 1},
    "abort": {"abort": 5, "failset": 2, "walk": 1},
    "edge": {"edge": 6, "abort": 1},
    "mix": {m: 1 for m in MOTIFS},
}

SHAPES = {
    "lazy": dict(actions=("noaction", "cascade", "setnull"), p_def=0.9, p_deferred=0.8),
    "side": dict(actions=("noaction", "cascade"), p_def=0.85, p_deferred=0.8, nfk=(2, 4)),
    "order": dict(actions=("noaction", "setnull", "cascade"), p_def=1.0, p_deferred=0.9,
                  nchk=(2, 4), nfk=(2, 4)),
    "rewind": dict(p_def=0.8, p_deferred=0.7),
    "mode": dict(p_def=0.7, p_deferred=0.5),
    "abort": dict(p_def=0.4, p_deferred=0.5),
    "edge": dict(p_def=0.5, p_deferred=0.5, nchk=(2, 4)),
    "mix": dict(ntab=(2, 5), p_def=0.6, p_deferred=0.6, nchk=(1, 4), nfk=(1, 5), cycle=0.25),
}


def small(fam, rng):
    s = schema(rng, **SHAPES[fam])
    prepare(fam, rng, s)
    rows, have, held = committed(rng, s)
    w = Writer(rng, s, have, held)
    names, weights = zip(*WEIGHTS[fam].items())
    for _ in range(rng.randint(2, 4)):
        w.begin()
        base = w.savepoint("r") if rng.random() < 0.7 else None
        for _ in range(rng.randint(1, 3)):
            w.noise(rng.randint(0, 2))
            motif = MOTIFS[rng.choices(names, weights=weights)[0]]
            r = rng.random()
            if r < 0.4:
                motif(w)
            else:
                unit = w.savepoint("m")
                motif(w)
                if r < 0.7:
                    w.release(unit)
                else:
                    w.rollback_to(unit)
            if base is not None and rng.random() < 0.15:
                w.rollback_to(base)
        w.noise(rng.randint(0, 2))
        w.end()
    return s.lines() + rows + w.out


# --- the walk family, built around the shapes that separate walk readings ----------------------

def fam_walk(rng):
    """Deletes over a schema made for the action walk. `a` is held by `b` through two keys
    (twins, so one row can be reached twice), `c` sits two levels down with a row check on each
    column a setnull may write, and `d` and `e` hold keys that a delete can leave behind in two
    different tables.

    Each program is built around one of seven configurations, each the smallest schema in which
    one question about the walk has two different answers: depth-first or breadth-first, holders
    listed when each key is reached or once at the start, touch order or key order, a row check
    at the write or at the end, key by key or row by row at the end, restrict at once or at the
    end, noaction at the end or at the delete. Everything else in the schema is drawn freely."""
    d = lambda p: rng.random() < p                                          # noqa: E731
    shape = rng.choice(("depth", "listed", "touch", "write", "keyfirst", "restrict", "noaction"))
    act = {"bx": rng.choice(("cascade", "cascade", "setnull")),
           "by": rng.choice(("restrict", "noaction", "setnull", "cascade")),
           "cz": rng.choice(("setnull", "cascade")),
           "cw": rng.choice(("setnull", "cascade", "noaction"))}
    imm = {}                                    # constraints forced immediate (not deferrable)
    dfr = {}                                    # constraints forced deferred
    first = []                                  # constraints forced ahead in declaration order
    if shape == "depth":
        act.update(bx="cascade", cz="setnull", cw="setnull")
        imm.update(zn=1, wn=1)
        first = ["bx", "cw"]
    elif shape == "listed":
        act.update(bx="cascade", by="restrict")
        first = ["bx", "by"]
    elif shape == "touch":
        act.update(bx="cascade", cz="setnull")
        dfr.update(zn=1)
    elif shape == "write":
        act.update(bx="cascade", cz="setnull", cw="cascade")
        imm.update(zn=1)
        first = ["bx", "cw"]
    elif shape == "keyfirst":
        act.update(bx="cascade")
        imm.update(dv=1, es=1)
        first = ["dv", "es"]
    elif shape == "restrict":
        act.update(bx="cascade", by="restrict")
        first = ["by", "bx"]
    else:
        act.update(bx="cascade", by="noaction")
        imm.update(by=1)
        first = ["by", "bx"]
    cons = [
        dict(kind="fk", name="bx", table="b", col="x", parent="a", action=act["bx"]),
        dict(kind="fk", name="by", table="b", col="y", parent="a", action=act["by"]),
        dict(kind="fk", name="cz", table="c", col="z", parent="b", action=act["cz"]),
        dict(kind="fk", name="cw", table="c", col="w", parent="a", action=act["cw"]),
        dict(kind="fk", name="dv", table="d", col="v", parent="b", action="noaction"),
        dict(kind="fk", name="es", table="e", col="s", parent="a", action="noaction"),
        dict(kind="check", name="zn", table="c", col="z", test="notnull", floor=None),
        dict(kind="check", name="wn", table="c", col="w", test="notnull", floor=None),
        dict(kind="check", name="ym", table="b", col="y", test="min", floor=1),
    ]
    for c in cons:
        name = c["name"]
        if name in imm or (c["kind"] == "fk" and c["action"] == "restrict"):
            c["deferrable"], c["deferred"] = False, False
        elif name in dfr:
            c["deferrable"], c["deferred"] = True, True
        else:
            c["deferrable"] = d(0.55)
            c["deferred"] = c["deferrable"] and d(0.6)
        c["back"] = False
    rng.shuffle(cons)
    if first:
        # keep the pair the configuration needs in the order it needs, wherever they land
        pos = sorted(i for i, c in enumerate(cons) if c["name"] in first)
        picked = {c["name"]: c for c in cons if c["name"] in first}
        for i, name in zip(pos, first):
            cons[i] = picked[name]
    s = Schema()
    s.tables = [("a", ["u"]), ("b", ["x", "y"]), ("c", ["z", "w"]), ("d", ["v"]),
                ("e", ["s"])]
    s.cons = cons
    lines = s.lines()

    akeys = list(range(1, 7))
    bkeys = []
    for k in akeys:
        lines.append("row a %d %d" % (k, rng.randint(0, 5)))
    nb = 0
    for k in akeys:
        for _ in range(rng.randint(1, 3)):
            nb += 1
            lines.append("row b %d %d %d" % (nb, k, k if d(0.4) else rng.choice(akeys)))
            bkeys.append(nb)
    nc = 0
    for b in bkeys:
        for _ in range(rng.randint(0, 2)):
            nc += 1
            lines.append("row c %d %d %d" % (nc, b, rng.choice(akeys)))
    for i, b in enumerate(rng.sample(bkeys, min(3, len(bkeys)))):
        lines.append("row d %d %d" % (i + 1, b))
    for i, a in enumerate(rng.sample(akeys, 2)):
        lines.append("row e %d %d" % (i + 1, a))

    out = []
    fresh = {"a": 20, "b": 40, "c": 200, "d": 20, "e": 20}

    def new(t):
        fresh[t] += rng.randint(1, 2)
        return fresh[t]

    def guard(stmt):
        out.append("savepoint g")
        out.append(stmt)
        out.append("rollback to g" if d(0.5) else "release g")

    def tree():
        """A fresh parent with twins below it, children two levels down whose keys run against
        their parents' order, and holders in d and e, then a guarded delete of the parent."""
        ka = new("a")
        out.append("insert a %d %d" % (ka, rng.randint(0, 5)))
        kbs = []
        for _ in range(rng.randint(2, 3)):
            kb = new("b")
            kbs.append(kb)
            out.append("insert b %d %d %d" % (kb, ka, ka if d(0.7) else rng.choice(akeys)))
        ckeys = sorted((new("c") for _ in range(len(kbs) * 2)), reverse=d(0.7))
        for i, kb in enumerate(kbs):
            for kc in ckeys[2 * i:2 * i + rng.randint(1, 2)]:
                out.append("insert c %d %d %d" % (kc, kb, ka if d(0.7) else rng.choice(akeys)))
        if d(0.6):
            out.append("insert d %d %d" % (new("d"), rng.choice(kbs)))
        if d(0.5):
            out.append("insert e %d %d" % (new("e"), ka))
        guard("delete a %d" % ka)

    for _ in range(rng.randint(2, 3)):
        out.append("begin")
        for _ in range(rng.randint(3, 6)):
            r = rng.random()
            if r < 0.55:
                tree()
            elif r < 0.7:
                guard("delete a %d" % rng.choice(akeys))
            elif r < 0.8:
                guard("delete b %d" % rng.choice(bkeys))
            elif r < 0.9:
                name = rng.choice([c["name"] for c in cons if c["deferrable"]] or ["all"])
                out.append("set %s %s" % (name, rng.choice(("deferred", "immediate"))))
            else:
                out.append("savepoint q")
                out.append("set all immediate")
                out.append("rollback to q")
        out.append("commit" if d(0.6) else "rollback")
    return lines + out


# --- the scale families ------------------------------------------------------------------------

def fam_wrap(rng):
    """Every statement in its own savepoint, released or rolled back, over ~150k rows, with
    deletes that cascade and set null two levels down under noaction keys beside them."""
    np_, cper, gper, units = 6000, 6, 3, 6000
    lines = ["table p k a b", "table c k pk q v", "table g k ck w",
             "check cv c v min 0 deferrable deferred",
             "fk cp c pk p cascade",
             "fk cq c q p noaction deferrable deferred",
             "check gn g ck notnull deferrable deferred",
             "fk gc g ck c setnull deferrable"]
    ck = gk = 0
    for i in range(1, np_ + 1):
        lines.append("row p %d %d %d" % (i, rng.randint(0, 9), rng.randint(0, 9)))
    for i in range(1, np_ + 1):
        for _ in range(cper):
            ck += 1
            q = rng.randint(1, np_) if rng.random() < 0.3 else "-"
            lines.append("row c %d %d %s %d" % (ck, i, q, rng.randint(0, 9)))
            for _ in range(gper):
                gk += 1
                lines.append("row g %d %d %d" % (gk, ck, rng.randint(0, 9)))
    lines.append("begin")
    for u in range(units):
        name = "s%d" % (u % 40)
        lines.append("savepoint %s" % name)
        r = rng.random()
        if r < 0.3:
            lines.append("delete p %d" % rng.randint(1, np_))
        elif r < 0.5:
            ck += 1
            lines.append("insert c %d %d %s %d" % (ck, rng.randint(1, np_),
                                                   rng.choice(["-", str(rng.randint(1, np_))]),
                                                   rng.randint(-2, 9)))
        elif r < 0.75:
            lines.append("update g %d w %s" % (rng.randint(1, gk), rng.choice(["-", "3", "5"])))
        else:
            lines.append("update c %d v %d" % (rng.randint(1, ck), rng.randint(-2, 9)))
        lines.append(("rollback to %s" if rng.random() < 0.25 else "release %s") % name)
    lines.append("set all immediate")
    lines.append("rollback")
    return lines


def fam_load(rng):
    """Children loaded ahead of their parents under a deferred key, one savepoint per insert,
    then the parents, some updates, and a check point over the whole ledger."""
    n = 60000
    lines = ["table p k a", "table c k pk v",
             "fk cp c pk p noaction deferrable deferred",
             "check cv c v min 0 deferrable deferred"]
    lines.append("begin")
    for i in range(1, n + 1):
        lines.append("savepoint s")
        lines.append("insert c %d %d %d" % (i, rng.randint(1, n // 4), rng.randint(0, 9)))
        lines.append("rollback to s" if rng.random() < 0.02 else "release s")
    for j in range(1, n // 4 + 1):
        lines.append("savepoint s")
        lines.append("insert p %d 1" % j)
        lines.append("release s")
    for i in range(1, n + 1, 7):
        lines.append("update c %d v %d" % (i, rng.randint(0, 9)))
    lines.append("set all immediate")
    lines.append("commit")
    return lines


def build(fam, rng):
    if fam == "wrap":
        return fam_wrap(rng)
    if fam == "load":
        return fam_load(rng)
    if fam == "walk":
        return fam_walk(rng)
    return small(fam, rng)


def programs(seed, per):
    """Every generated program for one seed: `per` of each small family and BIG_EACH of each
    scale family, as (family, name, lines)."""
    out = []
    for fam, big in FAMILIES:
        for i in range(BIG_EACH if big else per):
            rng = random.Random("%s|%s|%d" % (seed, fam, i))
            out.append((fam, "%s-%d" % (fam, i), build(fam, rng)))
    return out
