"""Sealed independent model of the calculation engine.

This file never imports the agent's tree. It re-derives the printed grid from the script
text alone, and it is written to disagree structurally with the reference policy:

  * its own tokeniser and parser, producing dict nodes rather than tuples;
  * values are tagged dicts ({"k": "num"} / "gap" / "err" / "box"), not tuples;
  * coverage is answered by `holder`, which walks a per-row index of owner addresses,
    where the reference re-scans the whole owner list for each cell;
  * placement keeps an explicit decided/undecided table rather than one memo shared with
    the value query.

What it must reproduce exactly is the contract: a cell's face is decided by the first
owner at or before it, in address order, whose block reaches it; an owner's block is
refused when any cell of its rectangle other than its own is held or already taken, or
when the rectangle leaves the sheet; and a value query that re-enters itself makes the
re-entered cell and every cell asked after it a loop.
"""

COLW = 10
ROWH = 20
LETTERS = "abcdefghij"
FNS = ("SUM", "CNT", "MAX", "AT", "LEN", "RUN", "REP", "ROW", "KEEP", "GROW")

GAP = {"k": "gap"}
CYC = {"k": "err", "t": "#cyc"}
REF = {"k": "err", "t": "#ref"}
BLK = {"k": "err", "t": "#blk"}


def num(n):
    return {"k": "num", "n": n}


def box(h, w, cells):
    return {"k": "box", "h": h, "w": w, "cells": list(cells)}


def spread(h, w, cells):
    return {"k": "spread", "h": h, "w": w, "cells": list(cells)}


def kind(v):
    return v["k"]


def cells_of(v):
    if v["k"] in ("box", "spread"):
        return v["cells"]
    return [v]


def dims(v):
    if v["k"] in ("box", "spread"):
        return v["h"], v["w"]
    return 1, 1


# ----------------------------------------------------------------- addresses


def where(tok):
    if not tok or tok[0] not in LETTERS:
        return None
    if not tok[1:].isdigit():
        return None
    row = int(tok[1:])
    if row < 1 or row > ROWH:
        return None
    return (row, LETTERS.index(tok[0]))


def label(spot):
    return "%s%d" % (LETTERS[spot[1]], spot[0])


# ----------------------------------------------------------------- parsing


class Snag(Exception):
    pass


def slice_up(text):
    out = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == " " or ch == "\t":
            i += 1
        elif ch.isdigit():
            j = i
            while j < len(text) and text[j].isdigit():
                j += 1
            out.append(["n", int(text[i:j])])
            i = j
        elif ch.isalpha():
            j = i
            while j < len(text) and text[j].isalnum():
                j += 1
            word = text[i:j]
            out.append(["f" if word.isupper() else "a", word])
            i = j
        elif ch in "+-*(),:":
            out.append([ch, ch])
            i += 1
        else:
            raise Snag(ch)
    out.append(["$", "$"])
    return out


class Feed:
    def __init__(self, toks):
        self.toks = toks
        self.at = 0

    def kind(self):
        return self.toks[self.at][0]

    def pop(self):
        self.at += 1
        return self.toks[self.at - 1]

    def eat(self, k):
        if self.kind() != k:
            raise Snag(k)
        return self.pop()


def p_sum(fd):
    node = p_mul(fd)
    while fd.kind() in ("+", "-"):
        op = fd.pop()[0]
        node = {"t": "op", "op": op, "l": node, "r": p_mul(fd)}
    return node


def p_mul(fd):
    node = p_leaf(fd)
    while fd.kind() == "*":
        fd.pop()
        node = {"t": "op", "op": "*", "l": node, "r": p_leaf(fd)}
    return node


def p_leaf(fd):
    k = fd.kind()
    if k == "-":
        fd.pop()
        return {"t": "op", "op": "-", "l": {"t": "lit", "v": 0}, "r": p_leaf(fd)}
    if k == "n":
        return {"t": "lit", "v": fd.pop()[1]}
    if k == "(":
        fd.pop()
        node = p_sum(fd)
        fd.eat(")")
        return node
    if k == "f":
        nm = fd.pop()[1]
        if nm not in FNS:
            raise Snag(nm)
        fd.eat("(")
        kids = []
        if fd.kind() != ")":
            kids.append(p_sum(fd))
            while fd.kind() == ",":
                fd.pop()
                kids.append(p_sum(fd))
        fd.eat(")")
        return {"t": "call", "nm": nm, "kids": kids}
    if k == "a":
        one = where(fd.pop()[1])
        if one is None:
            raise Snag("addr")
        if fd.kind() == ":":
            fd.pop()
            two = where(fd.eat("a")[1])
            if two is None:
                raise Snag("addr")
            return {"t": "band", "a": one, "b": two}
        return {"t": "spot", "a": one}
    raise Snag(k)


def parse(text):
    fd = Feed(slice_up(text))
    node = p_sum(fd)
    fd.eat("$")
    return node


# ----------------------------------------------------------------- the model


class Model:
    def __init__(self, held):
        self.held = held
        self.rows = {}
        for spot in held:
            self.rows.setdefault(spot[0], []).append(spot)
        for r in self.rows:
            self.rows[r].sort()
        self.value = {}
        self.shape = {}
        self.chain = []
        self.live = set()

    # -- owners at or before a cell, in address order
    def earlier(self, spot):
        out = []
        for r in sorted(self.rows):
            if r > spot[0]:
                break
            for o in self.rows[r]:
                if o[1] <= spot[1]:
                    out.append(o)
        return out

    # -- the block an owner actually occupies, or None
    def block(self, owner):
        if owner in self.shape:
            return self.shape[owner]
        got = self.settle(owner)
        self.shape[owner] = got
        return got

    def settle(self, owner):
        v = self.ask(owner)
        if kind(v) != "box":
            return None
        h, w = v["h"], v["w"]
        if owner[0] + h - 1 > ROWH or owner[1] + w - 1 >= COLW:
            return None
        for dr in range(h):
            for dc in range(w):
                if dr == 0 and dc == 0:
                    continue
                spot = (owner[0] + dr, owner[1] + dc)
                if spot in self.held:
                    return None
                if self.holder(spot, owner) is not None:
                    return None
        return (h, w)

    # -- the first owner strictly before `stop` whose block reaches `spot`
    def holder(self, spot, stop=None):
        for o in self.earlier(spot):
            if stop is not None and not o < stop:
                break
            got = self.block(o)
            if got is None:
                continue
            if spot[0] < o[0] + got[0] and spot[1] < o[1] + got[1]:
                return o
        return None

    # -- what a reader sees in a cell
    def face(self, spot):
        o = self.holder(spot)
        if o is not None:
            h, w = self.block(o)
            return self.ask(o)["cells"][(spot[0] - o[0]) * w + (spot[1] - o[1])]
        if spot not in self.held:
            return GAP
        v = self.ask(spot)
        if kind(v) == "box":
            return BLK
        if kind(v) == "spread":
            return REF
        return v

    # -- a cell's own value, memoised, with the loop rule
    def ask(self, spot):
        if spot in self.value:
            return self.value[spot]
        if spot in self.live:
            cut = self.chain.index(spot)
            for other in self.chain[cut:]:
                self.value[other] = CYC
            return CYC
        if spot not in self.held:
            return GAP
        self.chain.append(spot)
        self.live.add(spot)
        try:
            out = self.walk(self.held[spot])
        finally:
            self.chain.pop()
            self.live.discard(spot)
        return self.value.setdefault(spot, out)

    # -- expression walk
    def walk(self, node):
        t = node["t"]
        if t == "lit":
            return num(node["v"])
        if t == "spot":
            return self.face(node["a"])
        if t == "band":
            lo, hi = node["a"], node["b"]
            r0, r1 = min(lo[0], hi[0]), max(lo[0], hi[0])
            c0, c1 = min(lo[1], hi[1]), max(lo[1], hi[1])
            pool = []
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    pool.append(self.face((r, c)))
            return spread(r1 - r0 + 1, c1 - c0 + 1, pool)
        if t == "op":
            return self.pair(node)
        return self.apply(node["nm"], [self.walk(k) for k in node["kids"]])

    def pair(self, node):
        left = self.walk(node["l"])
        right = self.walk(node["r"])
        for side in (left, right):
            if kind(side) in ("box", "spread"):
                return REF
        if kind(left) == "err":
            return left
        if kind(right) == "err":
            return right
        a = 0 if kind(left) == "gap" else left["n"]
        b = 0 if kind(right) == "gap" else right["n"]
        if node["op"] == "+":
            return num(a + b)
        if node["op"] == "-":
            return num(a - b)
        return num(a * b)

    def apply(self, nm, args):
        for a in args:
            for e in cells_of(a):
                if e is CYC or (kind(e) == "err" and e["t"] == "#cyc"):
                    return CYC
        if nm in ("SUM", "MAX", "CNT"):
            return self.tally(nm, args)
        if nm == "LEN":
            if len(args) != 1:
                return REF
            h, w = dims(args[0])
            return num(h * w)
        if nm == "AT":
            return self.pick(args)
        if nm in ("RUN", "REP", "ROW", "KEEP"):
            return self.make(nm, args)
        if nm == "GROW":
            if len(args) != 1:
                return REF
            h, w = dims(args[0])
            out = []
            for e in cells_of(args[0]):
                if kind(e) in ("gap", "err"):
                    out.append(e)
                else:
                    out.append(num(e["n"] + 1))
            return box(h, w, out)
        return REF

    def tally(self, nm, args):
        got = []
        full = 0
        for a in args:
            for e in cells_of(a):
                if kind(e) == "gap":
                    continue
                full += 1
                if kind(e) != "err":
                    got.append(e["n"])
        if nm == "CNT":
            return num(full)
        if nm == "SUM":
            return num(sum(got))
        return num(max(got)) if got else REF

    def pick(self, args):
        if len(args) != 2:
            return REF
        if kind(args[1]) == "err":
            return args[1]
        k = self.tick(args[1])
        if k is None:
            return REF
        pool = cells_of(args[0])
        if k > len(pool):
            return REF
        return pool[k - 1]

    def tick(self, v):
        if kind(v) != "num":
            return None
        if v["n"] < 1 or v["n"] > ROWH:
            return None
        return v["n"]

    def make(self, nm, args):
        want = 1 if nm == "RUN" else 2
        if len(args) != want:
            return REF
        last = args[-1]
        if kind(last) == "err":
            return last
        k = self.tick(last)
        if k is None:
            return REF
        if nm == "RUN":
            return box(k, 1, [num(i) for i in range(1, k + 1)])
        if nm == "KEEP":
            pool = cells_of(args[0])
            if k > len(pool):
                return REF
            return box(k, 1, pool[:k])
        seed = args[0]
        if kind(seed) in ("box", "spread"):
            return REF
        if nm == "REP":
            return box(k, 1, [seed] * k)
        if k > COLW:
            return REF
        return box(1, k, [seed] * k)


def render(v):
    if kind(v) == "num":
        return str(v["n"])
    if kind(v) == "err":
        return v["t"]
    return ""


def solve(text):
    held = {}
    out = []
    step = 0
    for raw in text.split("\n"):
        toks = raw.split()
        if not toks:
            continue
        step += 1
        verb = toks[0]
        spot = where(toks[1])
        if verb == "put":
            held[spot] = parse(" ".join(toks[2:]))
        elif verb == "clr":
            held.pop(spot, None)
        else:
            raise Snag(verb)
        model = Model(dict(held))
        shown = []
        for r in range(1, ROWH + 1):
            for c in range(COLW):
                txt = render(model.face((r, c)))
                if txt:
                    shown.append("%s=%s" % (label((r, c)), txt))
        out.append("%d %s %s | %s" % (step, verb, toks[1], " ".join(shown)))
    return out
