"""Straightforward engine: keep the work list, re-derive it whenever anything moves.

This is the implementation the spec asks for read literally, and it is exactly correct.
It is the naive-but-correct family the resource gate is aimed at: every re-take of a basis
re-derives the whole work list, and every section a failing condition drops re-derives it
again.

Work entries:
    ("p", k, n)   put      value at k becomes n
    ("a", k, n)   add      value at k becomes the value just before, plus n
    ("c", k, j)   cpy      value at k becomes the value at j just before
    ("f", k, v)   fixed    a read fixed the value at k to v
    ("k", k, n)   check    condition: the value at k here is n
    ("m",)        mark
"""


def replay(work, take, stop=None):
    """Values the work produces from the bases, up to (not including) index `stop`."""
    vals = dict(take)
    end = len(work) if stop is None else stop
    for i in range(end):
        e = work[i]
        tag = e[0]
        if tag == "p":
            vals[e[1]] = e[2]
        elif tag == "a":
            vals[e[1]] = vals[e[1]] + e[2]
        elif tag == "c":
            vals[e[1]] = vals[e[2]]
        elif tag == "r":
            vals[e[1]] = take[e[2]]
        elif tag == "f":
            vals[e[1]] = e[2]
    return vals


def written(work):
    return {e[1] for e in work if e[0] in ("p", "a", "c", "r")}


class Txn:
    def __init__(self, num):
        self.num = num
        self.take = {}
        self.work = []
        self.vals = {}

    def touch(self, cur, keys):
        moved = False
        for k in keys:
            if k not in self.take:
                self.take[k] = cur[k]
                self.vals[k] = cur[k]
            elif self.take[k] != cur[k]:
                self.take[k] = cur[k]
                moved = True
        if moved:
            self.vals = replay(self.work, self.take)


def run(text):
    out = []
    cur = {}
    txs = {}
    for line in text.splitlines():
        p = line.split()
        if not p:
            continue
        op = p[0]
        if op == "cfg":
            cur = {k: 0 for k in range(int(p[1]))}
            continue
        if op == "tx":
            txs[int(p[1])] = Txn(int(p[1]))
            continue
        t = txs[int(p[1])]
        if op == "rd":
            k = int(p[2])
            t.touch(cur, (k,))
            out.append("rd %s %d %d" % (p[1], k, t.vals[k]))
            t.work.append(("f", k, t.vals[k]))
        elif op == "put":
            k, n = int(p[2]), int(p[3])
            t.touch(cur, (k,))
            t.work.append(("p", k, n))
            t.vals[k] = n
        elif op == "add":
            k, n = int(p[2]), int(p[3])
            t.touch(cur, (k,))
            t.work.append(("a", k, n))
            t.vals[k] = t.vals[k] + n
        elif op == "cpy":
            k, j = int(p[2]), int(p[3])
            t.touch(cur, (k, j))
            t.work.append(("c", k, j))
            t.vals[k] = t.vals[j]
        elif op == "raw":
            k, j = int(p[2]), int(p[3])
            t.touch(cur, (k, j))
            t.work.append(("r", k, j))
            t.vals[k] = t.take[j]
        elif op == "bmp":
            lo, hi, n = int(p[2]), int(p[3]), int(p[4])
            t.touch(cur, tuple(range(lo, hi)))
            for k in range(lo, hi):
                t.work.append(("a", k, n))
                t.vals[k] = t.vals[k] + n
        elif op == "chk":
            k, n = int(p[2]), int(p[3])
            t.touch(cur, (k,))
            t.work.append(("k", k, n))
        elif op == "lim":
            k, n = int(p[2]), int(p[3])
            t.touch(cur, (k,))
            t.work.append(("l", k, n))
        elif op == "mk":
            t.work.append(("m",))
        elif op == "un":
            cutback(t)
        elif op == "drp":
            del txs[int(p[1])]
        elif op == "fin":
            out.append(close(t, cur))
            del txs[int(p[1])]
    return out


def cutback(t):
    """Throw away the work since the last standing mark, and that mark with it."""
    at = None
    for i in range(len(t.work) - 1, -1, -1):
        if t.work[i][0] == "m":
            at = i
            break
    t.work = t.work[:at] if at is not None else []
    t.vals = replay(t.work, t.take)


def close(t, cur):
    for k in list(t.take):
        if t.take[k] != cur[k]:
            t.take[k] = cur[k]
    work = t.work
    while True:
        vals = dict(t.take)
        bad = None
        for i, e in enumerate(work):
            tag = e[0]
            if tag == "p":
                vals[e[1]] = e[2]
            elif tag == "a":
                vals[e[1]] = vals[e[1]] + e[2]
            elif tag == "c":
                vals[e[1]] = vals[e[2]]
            elif tag == "r":
                vals[e[1]] = t.take[e[2]]
            elif tag == "f":
                vals[e[1]] = e[2]
            elif tag == "k":
                if vals[e[1]] != e[2]:
                    bad = i
                    break
            elif tag == "l":
                if vals[e[1]] < e[2]:
                    bad = i
                    break
        if bad is None:
            break
        at = None
        for i in range(bad - 1, -1, -1):
            if work[i][0] == "m":
                at = i
                break
        if at is None:
            return "fin %d no" % t.num
        work = work[:at] + work[bad + 1:]
    t.work = work
    keys = sorted(written(work))
    vals = replay(work, t.take)
    for k in keys:
        cur[k] = vals[k]
    parts = ["fin %d ok" % t.num] + ["%d=%d" % (k, vals[k]) for k in keys]
    return " ".join(parts)
