"""The whole engine, written from the rules with nothing clever in it.

This exists to check the reference, not to ship. Every claim of every open transaction is
answered again from scratch at every moment a claim could stop standing, the cover of a read
is never worked out at all, and the changes a read was answered under are found by walking the
transaction's whole change log. It is quadratic and it is the definition of correct that the
fast reference is measured against.
"""
from tx import say


class Txn:
    def __init__(self, tid, base):
        self.tid = tid
        self.base = base
        self.claims = []
        self.chs = []
        self.marks = []
        self.dead = None


class Store:
    def __init__(self):
        self.ver = 0
        self.log = {}

    def at(self, key, ver):
        val = None
        for stamp, one in self.log.get(key, ()):
            if stamp <= ver:
                val = one
        return val

    def after(self, key, base):
        for stamp, _one in self.log.get(key, ()):
            if stamp > base:
                return True
        return False

    def put(self, ch):
        self.ver += 1
        for key in sorted(ch):
            self.log.setdefault(key, []).append((self.ver, ch[key]))


def cover(txn, upto):
    over = {}
    for i, key, val, on in txn.chs:
        if on and i < upto:
            over[key] = val
    return over


def answer(st, txn, c, ver):
    over = cover(txn, c["i"])
    if c["kind"] == "get":
        key = c["key"]
        return over[key] if key in over else st.at(key, ver)
    lo, hi, n = c["lo"], c["hi"], c["n"]
    keys = sorted(set(list(st.log) + list(over)))
    got = []
    for key in keys:
        if key < lo or key > hi:
            continue
        val = over[key] if key in over else st.at(key, ver)
        if val is not None:
            got.append((key, val))
        if len(got) == n:
            break
    return got


def check(st, txn, out):
    if txn.dead is not None:
        return
    low = None
    for c in txn.claims:
        if c["kind"] == "chg":
            bad = c["on"] and st.after(c["key"], txn.base)
        else:
            bad = answer(st, txn, c, st.ver) != c["ans"]
        if bad and (low is None or c["i"] < low):
            low = c["i"]
    if low is not None:
        txn.dead = low
        say.dead(out, txn.tid, low)


def play(ops, out):
    st = Store()
    live = {}
    for op in ops:
        head = op[0]
        if head == "open":
            live[op[1]] = Txn(op[1], st.ver)
            continue
        if head == "look":
            got = []
            for key in sorted(st.log):
                if op[1] <= key <= op[2]:
                    val = st.at(key, st.ver)
                    if val is not None:
                        got.append((key, val))
            say.look(out, got)
            continue
        if head == "drop":
            del live[op[1]]
            continue
        if head == "seal":
            txn = live.pop(op[1])
            if txn.dead is not None:
                say.done(out, txn.tid, txn.dead)
                continue
            st.put(cover(txn, len(txn.claims)))
            say.done(out, txn.tid, None)
            for tid in sorted(live):
                check(st, live[tid], out)
            continue
        txn = live[op[1]]
        if head == "mark":
            txn.marks.append((op[2], len(txn.claims)))
            continue
        if head == "back":
            pos = None
            for j in range(len(txn.marks) - 1, -1, -1):
                if txn.marks[j][0] == op[2]:
                    pos = txn.marks[j][1]
                    del txn.marks[j + 1:]
                    break
            if pos is not None:
                for j, (i, key, val, on) in enumerate(txn.chs):
                    if i >= pos:
                        txn.chs[j] = (i, key, val, False)
                for c in txn.claims:
                    if c["kind"] == "chg" and c["i"] >= pos:
                        c["on"] = False
                check(st, txn, out)
            continue
        i = len(txn.claims)
        if head == "get":
            c = {"i": i, "kind": "get", "key": op[2]}
            txn.claims.append(c)
            c["ans"] = answer(st, txn, c, txn.base)
            say.read(out, txn.tid, op[2], c["ans"])
        elif head == "span":
            c = {"i": i, "kind": "span", "lo": op[2], "hi": op[3], "n": op[4]}
            txn.claims.append(c)
            c["ans"] = answer(st, txn, c, txn.base)
            say.span(out, txn.tid, c["ans"])
        else:
            key = op[2]
            val = op[3] if head == "put" else None
            c = {"i": i, "kind": "chg", "key": key, "val": val, "on": True}
            txn.claims.append(c)
            txn.chs.append((i, key, val, True))
        check(st, txn, out)
