from sheet import adr, store

BLK = store.BLK
BLOCKY = ("RUN", "LIST", "TOP")


def lex(s):
    out = []
    i, n = 0, len(s)
    while i < n:
        ch = s[i]
        if ch in " \t":
            i += 1
        elif ch in "+-*(),:":
            out.append((ch, None))
            i += 1
        elif ch.isdigit():
            j = i
            while j < n and s[j].isdigit():
                j += 1
            out.append(("k", int(s[i:j])))
            i = j
        elif ch == "r" and i + 1 < n and s[i + 1].isdigit():
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
            out.append(("a", adr.pa(s[i:j])))
            i = j
        elif ch.isalpha():
            j = i
            while j < n and s[j].isalpha():
                j += 1
            out.append(("f", s[i:j]))
            i = j
        else:
            raise ValueError(s)
    out.append(("$", None))
    return out


class P:
    def __init__(self, ts):
        self.ts = ts
        self.i = 0

    def peek(self):
        return self.ts[self.i][0]

    def take(self):
        t = self.ts[self.i]
        self.i += 1
        return t

    def want(self, k):
        if self.take()[0] != k:
            raise ValueError(k)

    def add(self):
        node = self.mul()
        while self.peek() in ("+", "-"):
            op = self.take()[0]
            node = ("b", op, node, self.mul())
        return node

    def mul(self):
        node = self.atom()
        while self.peek() == "*":
            self.take()
            node = ("b", "*", node, self.atom())
        return node

    def atom(self):
        k, v = self.take()
        if k == "k":
            return ("k", v)
        if k == "a":
            if self.peek() == ":":
                self.take()
                t = self.take()
                if t[0] != "a":
                    raise ValueError("range")
                return ("g", v, t[1])
            return ("a", v)
        if k == "f":
            self.want("(")
            args = [self.add()]
            while self.peek() == ",":
                self.take()
                args.append(self.add())
            self.want(")")
            return ("c", v, args)
        if k == "(":
            node = self.add()
            self.want(")")
            return node
        raise ValueError(k)


def parse(s):
    p = P(lex(s))
    node = p.add()
    if p.peek() != "$":
        raise ValueError(s)
    return node


def gather(node, look):
    if node[0] != "g":
        raise ValueError(node)
    out = []
    bad = False
    for ad in adr.span(node[1], node[2]):
        v = look.val(ad)
        if v is None:
            continue
        if v == BLK:
            bad = True
        else:
            out.append(v)
    return None if bad else out


def sc(node, look):
    t = node[0]
    if t == "k":
        return node[1]
    if t == "a":
        v = look.val(node[1])
        return 0 if v is None else v
    if t == "b":
        x = sc(node[2], look)
        y = sc(node[3], look)
        if x == BLK or y == BLK:
            return BLK
        if node[1] == "+":
            return x + y
        if node[1] == "-":
            return x - y
        return x * y
    if t == "c":
        nm = node[1]
        if nm in ("SUM", "CNT"):
            vs = gather(node[2][0], look)
            if vs is None:
                return BLK
            return sum(vs) if nm == "SUM" else len(vs)
        if nm == "IFZ":
            x = sc(node[2][0], look)
            if x == BLK:
                return BLK
            return sc(node[2][1] if x == 0 else node[2][2], look)
    raise ValueError(node)


def blk(node, look):
    nm = node[1]
    if nm == "RUN":
        a = sc(node[2][0], look)
        b = sc(node[2][1], look)
        if a == BLK or b == BLK:
            return ("s", BLK)
        return ("v", list(range(a, b + 1)))
    vs = gather(node[2][0], look)
    if vs is None:
        return ("s", BLK)
    if nm == "LIST":
        return ("v", vs)
    n = sc(node[2][1], look)
    if n == BLK:
        return ("s", BLK)
    return ("v", sorted(vs, reverse=True)[:max(0, n)])


def run(node, look):
    if node[0] == "c" and node[1] in BLOCKY:
        return blk(node, look)
    return ("s", sc(node, look))
