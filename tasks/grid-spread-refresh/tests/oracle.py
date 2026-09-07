"""Sealed model of the recalculation contract.

Written against the same stated rules as the shipped runtime and deliberately not against
its code. The differences are structural, so a shared implementation slip cannot hide:

  * formulas are compiled once into closures over a lookup object, instead of being kept
    as a tuple tree walked at every evaluation;
  * an edit first builds the cone of cells the edit could possibly reach - readers by the
    inverted index, plus every cell under a block-valued formula in its column - and only
    then evaluates that cone in a per-edit topological order, instead of picking a ready
    cell out of a pending set as the runtime does;
  * the cell that supplies an address is found by bisecting a per-column list of
    block-valued formulas, instead of by a coverage dictionary;
  * displayed-value changes come from a touch map recorded by the setter, and the
    recomputed set is collected as evaluations happen.

The rules themselves, in one place:

  * a formula cell is recomputed when one of the reads its last evaluation performed would
    now give a different answer, and only then; a read is either the displayed value of a
    cell or whether a cell holds its own content;
  * a block-valued formula probes every cell it would occupy, inside the sheet, and does
    not fit if one of them holds its own content, if the block would run off the sheet, or
    if it would occupy a cell the formula itself read; a block that does not fit shows
    #BLK and occupies nothing;
  * a block that gives a cell up leaves it empty unless that cell has since been given its
    own content;
  * a cell that stops carrying a formula gives up its block and its read record;
  * nothing is recomputed on a value that moves and comes back: a cell is looked at only
    once everything it read has stopped moving.
"""

import bisect

BLK = "#BLK"


def pa(s):
    i = s.index("c")
    return (int(s[1:i]), int(s[i + 1:]))


def fa(t):
    return "r%dc%d" % t


def area(a, b):
    lo, hi = sorted((a[0], b[0])), sorted((a[1], b[1]))
    return [(r, c) for r in range(lo[0], lo[1] + 1) for c in range(hi[0], hi[1] + 1)]


# --------------------------------------------------------------- formula compilation

def tokens(s):
    out = []
    i, n = 0, len(s)
    while i < n:
        ch = s[i]
        if ch in " \t":
            i += 1
            continue
        if ch in "+-*(),:":
            out.append((ch, None))
            i += 1
            continue
        if ch.isdigit():
            j = i
            while j < n and s[j].isdigit():
                j += 1
            out.append(("k", int(s[i:j])))
            i = j
            continue
        if ch == "r" and i + 1 < n and s[i + 1].isdigit():
            j = i + 1
            while j < n and s[j].isdigit():
                j += 1
            if j >= n or s[j] != "c":
                raise ValueError(s)
            j += 1
            m = j
            while j < n and s[j].isdigit():
                j += 1
            if j == m:
                raise ValueError(s)
            out.append(("a", pa(s[i:j])))
            i = j
            continue
        if ch.isalpha():
            j = i
            while j < n and s[j].isalpha():
                j += 1
            out.append(("w", s[i:j]))
            i = j
            continue
        raise ValueError(s)
    out.append(("$", None))
    return out


class Reader:
    """Recursive descent over the token list, producing the same shapes as the runtime's
    grammar: literals, addresses, spans, binary operators and calls."""

    def __init__(self, ts):
        self.ts = ts
        self.at = 0

    def kind(self):
        return self.ts[self.at][0]

    def pop(self):
        t = self.ts[self.at]
        self.at += 1
        return t

    def expect(self, k):
        if self.pop()[0] != k:
            raise ValueError(k)

    def expr(self):
        left = self.prod()
        while self.kind() in ("+", "-"):
            op = self.pop()[0]
            left = ("op", op, left, self.prod())
        return left

    def prod(self):
        left = self.unit()
        while self.kind() == "*":
            self.pop()
            left = ("op", "*", left, self.unit())
        return left

    def unit(self):
        k, v = self.pop()
        if k == "k":
            return ("lit", v)
        if k == "a":
            if self.kind() == ":":
                self.pop()
                t = self.pop()
                if t[0] != "a":
                    raise ValueError("span")
                return ("span", v, t[1])
            return ("ref", v)
        if k == "w":
            self.expect("(")
            args = [self.expr()]
            while self.kind() == ",":
                self.pop()
                args.append(self.expr())
            self.expect(")")
            return ("call", v, args)
        if k == "(":
            e = self.expr()
            self.expect(")")
            return e
        raise ValueError(k)


def tree(text):
    r = Reader(tokens(text))
    node = r.expr()
    if r.kind() != "$":
        raise ValueError(text)
    return node


def mentions(node, out):
    k = node[0]
    if k == "ref":
        out.append(node[1])
    elif k == "span":
        out.extend(area(node[1], node[2]))
    elif k == "op":
        mentions(node[2], out)
        mentions(node[3], out)
    elif k == "call":
        for a in node[2]:
            mentions(a, out)


def sums(ads):
    """Read a span and return (total, count) or None when any cell in it shows #BLK."""
    def go(lk):
        tot = 0
        cnt = 0
        bad = False
        for ad in ads:
            v = lk.val(ad)
            if v is None:
                continue
            if v == BLK:
                bad = True
            else:
                tot += v
                cnt += 1
        return None if bad else (tot, cnt)
    return go


def picks(ads):
    def go(lk):
        out = []
        bad = False
        for ad in ads:
            v = lk.val(ad)
            if v is None:
                continue
            if v == BLK:
                bad = True
            else:
                out.append(v)
        return None if bad else out
    return go


def scalar(node):
    k = node[0]
    if k == "lit":
        v = node[1]
        return lambda lk: v
    if k == "ref":
        ad = node[1]

        def one(lk):
            v = lk.val(ad)
            return 0 if v is None else v
        return one
    if k == "op":
        op = node[1]
        left, right = scalar(node[2]), scalar(node[3])

        def two(lk):
            x = left(lk)
            y = right(lk)
            if x == BLK or y == BLK:
                return BLK
            if op == "+":
                return x + y
            if op == "-":
                return x - y
            return x * y
        return two
    if k == "call":
        nm = node[1]
        if nm in ("SUM", "CNT"):
            f = sums(area(node[2][0][1], node[2][0][2]))
            want = 0 if nm == "SUM" else 1

            def agg(lk):
                r = f(lk)
                return BLK if r is None else r[want]
            return agg
        if nm == "IFZ":
            test, yes, no = (scalar(node[2][0]), scalar(node[2][1]), scalar(node[2][2]))

            def branch(lk):
                x = test(lk)
                if x == BLK:
                    return BLK
                return yes(lk) if x == 0 else no(lk)
            return branch
    raise ValueError(node)


def spread(node):
    nm = node[1]
    if nm == "RUN":
        lo, hi = scalar(node[2][0]), scalar(node[2][1])

        def walk(lk):
            a = lo(lk)
            b = hi(lk)
            if a == BLK or b == BLK:
                return BLK
            return list(range(a, b + 1))
        return walk
    f = picks(area(node[2][0][1], node[2][0][2]))
    if nm == "LIST":
        def keep(lk):
            r = f(lk)
            return BLK if r is None else r
        return keep
    many = scalar(node[2][1])

    def best(lk):
        r = f(lk)
        if r is None:
            return BLK
        n = many(lk)
        if n == BLK:
            return BLK
        r.sort(reverse=True)
        return r[:max(0, n)]
    return best


def build(text):
    node = tree(text)
    refs = []
    mentions(node, refs)
    if node[0] == "call" and node[1] in ("RUN", "LIST", "TOP"):
        return "v", spread(node), refs
    return "s", scalar(node), refs


# --------------------------------------------------------------- the sheet

class Look:
    def __init__(self, m):
        self.m = m
        self.rd = []

    def val(self, ad):
        v = self.m.dv.get(ad)
        self.rd.append((0, ad, v))
        return v

    def own(self, ad):
        b = ad in self.m.ow
        self.rd.append((1, ad, b))
        return b


class Model:
    def __init__(self, nr):
        self.nr = nr
        self.ow = {}
        self.dv = {}
        self.rec = {}
        self.idx = {}
        self.held = {}
        self.src = {}
        self.rows = {}
        self.tch = {}
        self.hit = set()

    # ---- displayed values -------------------------------------------------

    def put(self, ad, v):
        if ad not in self.tch:
            self.tch[ad] = self.dv.get(ad)
        if v is None:
            self.dv.pop(ad, None)
        else:
            self.dv[ad] = v

    # ---- the record and its inverse ---------------------------------------

    def keep(self, ad, rd):
        self.forget(ad)
        self.rec[ad] = rd
        for _, t, _ in rd:
            self.idx.setdefault(t, set()).add(ad)

    def forget(self, ad):
        for _, t, _ in self.rec.pop(ad, ()):
            s = self.idx.get(t)
            if s is not None:
                s.discard(ad)
                if not s:
                    del self.idx[t]

    def inputs(self, ad):
        r = self.rec.get(ad)
        if r is not None:
            return [t for _, t, _ in r]
        e = self.ow.get(ad)
        return e[3] if e is not None and e[0] == "f" else ()

    def stale(self, ad):
        r = self.rec.get(ad)
        if r is None:
            return True
        for k, t, was in r:
            now = (t in self.ow) if k else self.dv.get(t)
            if now != was:
                return True
        return False

    # ---- who supplies an address ------------------------------------------

    def mark(self, ad, on):
        rows = self.rows.setdefault(ad[1], [])
        i = bisect.bisect_left(rows, ad[0])
        there = i < len(rows) and rows[i] == ad[0]
        if on and not there:
            rows.insert(i, ad[0])
        elif there and not on:
            rows.pop(i)

    def makers(self, ad):
        out = []
        e = self.ow.get(ad)
        if e is not None and e[0] == "f":
            out.append(ad)
        rows = self.rows.get(ad[1])
        if rows:
            for r in rows[:bisect.bisect_left(rows, ad[0])]:
                out.append((r, ad[1]))
        return out

    # ---- one recomputation -------------------------------------------------

    def calc(self, ad):
        self.hit.add(ad)
        e = self.ow[ad]
        lk = Look(self)
        res = e[2](lk)
        tgt = None
        if e[1] == "v" and res != BLK:
            tgt = self.room(ad, res, lk)
        if e[1] == "v" and res != BLK and tgt is not None:
            self.lay(ad, res, tgt)
            self.put(ad, res[0] if res else None)
        else:
            self.lay(ad, None, [])
            self.put(ad, BLK if e[1] == "v" else res)
        self.keep(ad, lk.rd)

    def room(self, ad, vals, lk):
        r, c = ad
        want = [(r + i, c) for i in range(1, len(vals))]
        fits = True
        for t in want:
            if t[0] > self.nr:
                fits = False
            elif lk.own(t):
                fits = False
        if not fits:
            return None
        touched = set(t for k, t, _ in lk.rd if not k)
        for t in want:
            if t in touched:
                return None
        return want

    def lay(self, ad, vals, tgt):
        keep = set(tgt)
        for t in self.held.get(ad, ()):
            if t not in keep and self.src.get(t) == ad:
                del self.src[t]
                if t not in self.ow:
                    self.put(t, None)
        for i, t in enumerate(tgt):
            self.src[t] = ad
            self.put(t, vals[i + 1])
        if tgt:
            self.held[ad] = tgt
        else:
            self.held.pop(ad, None)

    # ---- settling ----------------------------------------------------------

    def cone(self, seed):
        out = set()
        stack = [seed]
        while stack:
            a = stack.pop()
            if a in out:
                continue
            out.add(a)
            for y in self.idx.get(a, ()):
                if y not in out:
                    stack.append(y)
            e = self.ow.get(a)
            if (e is not None and e[0] == "f" and e[1] == "v") or a in self.held:
                for r in range(a[0] + 1, self.nr + 1):
                    t = (r, a[1])
                    if t not in out:
                        stack.append(t)
        return out

    def sorted_cone(self, cone):
        state = {}
        out = []
        for start in sorted(cone):
            if state.get(start) == 2:
                continue
            stack = [(start, 0)]
            while stack:
                a, phase = stack.pop()
                if phase:
                    state[a] = 2
                    out.append(a)
                    continue
                if state.get(a):
                    continue
                state[a] = 1
                stack.append((a, 1))
                for t in self.inputs(a):
                    for p in self.makers(t):
                        if p != a and p in cone and state.get(p) is None:
                            stack.append((p, 0))
        return out

    def settle(self, seeds):
        cone = set()
        fresh = set(seeds)
        while fresh:
            for s in fresh:
                cone |= self.cone(s)
            while True:
                moved = False
                for a in self.sorted_cone(cone):
                    e = self.ow.get(a)
                    if e is None or e[0] != "f":
                        continue
                    if self.stale(a):
                        self.calc(a)
                        moved = True
                if not moved:
                    break
            fresh = set(t for t in self.tch if t not in cone)

    # ---- edits -------------------------------------------------------------

    def apply(self, line):
        self.tch = {}
        self.hit = set()
        t = line.split(None, 2)
        ad = pa(t[1])
        if t[0] == "clr":
            gone = self.ow.pop(ad, None)
            if gone is None:
                return
            if gone[0] == "f":
                self.mark(ad, False)
            self.put(ad, None)
        else:
            body = t[2].strip()
            was = self.ow.get(ad)
            if was is not None and was[0] == "f":
                self.mark(ad, False)
            if body.startswith("="):
                kind, fn, refs = build(body[1:])
                self.ow[ad] = ("f", kind, fn, refs)
                if kind == "v":
                    self.mark(ad, True)
                self.put(ad, None)
            else:
                self.ow[ad] = ("n", int(body))
                self.put(ad, int(body))
        self.forget(ad)
        e = self.ow.get(ad)
        if e is None or e[0] != "f":
            self.lay(ad, None, [])
        self.settle(set(self.tch) | set([ad]))

    def report(self):
        seen = " ".join(fa(a) for a in sorted(self.hit)) or "-"
        moves = []
        for a in sorted(self.tch):
            now = self.dv.get(a)
            if self.tch[a] != now:
                moves.append("%s=%s" % (fa(a), "-" if now is None else str(now)))
        return seen, " ".join(moves) or "-"


def solve(text):
    m = None
    live = False
    k = 0
    out = []
    for raw in text.split("\n"):
        s = raw.strip()
        if not s:
            continue
        t = s.split(None, 2)
        if t[0] == "size":
            m = Model(int(t[1]))
            continue
        if t[0] == "go":
            live = True
            continue
        m.apply(s)
        if not live:
            continue
        k += 1
        seen, moves = m.report()
        out.append("rc %d %s" % (k, seen))
        out.append("dv %d %s" % (k, moves))
    return out
