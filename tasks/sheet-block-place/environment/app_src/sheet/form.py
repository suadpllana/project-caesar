from . import addr

FNS = ("SUM", "CNT", "MAX", "AT", "LEN", "RUN", "REP", "ROW", "KEEP", "GROW")


class Bad(Exception):
    pass


def chop(text):
    out = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        if ch.isdigit():
            j = i
            while j < n and text[j].isdigit():
                j += 1
            out.append(("n", int(text[i:j])))
            i = j
            continue
        if ch.isalpha():
            j = i
            while j < n and (text[j].isalnum()):
                j += 1
            word = text[i:j]
            if word.isupper():
                out.append(("f", word))
            else:
                out.append(("a", word))
            i = j
            continue
        if ch in "+-*(),:":
            out.append((ch, ch))
            i += 1
            continue
        raise Bad(ch)
    out.append(("$", "$"))
    return out


class Read:
    def __init__(self, toks):
        self.t = toks
        self.i = 0

    def peek(self):
        return self.t[self.i][0]

    def take(self):
        v = self.t[self.i]
        self.i += 1
        return v

    def want(self, k):
        if self.peek() != k:
            raise Bad(k)
        return self.take()


def expr(rd):
    node = term(rd)
    while rd.peek() in ("+", "-"):
        op = rd.take()[0]
        node = ("bin", op, node, term(rd))
    return node


def term(rd):
    node = atom(rd)
    while rd.peek() == "*":
        rd.take()
        node = ("bin", "*", node, atom(rd))
    return node


def atom(rd):
    k, v = rd.peek(), None
    if k == "-":
        rd.take()
        return ("bin", "-", ("num", 0), atom(rd))
    if k == "n":
        return ("num", rd.take()[1])
    if k == "(":
        rd.take()
        node = expr(rd)
        rd.want(")")
        return node
    if k == "f":
        nm = rd.take()[1]
        if nm not in FNS:
            raise Bad(nm)
        rd.want("(")
        args = []
        if rd.peek() != ")":
            args.append(expr(rd))
            while rd.peek() == ",":
                rd.take()
                args.append(expr(rd))
        rd.want(")")
        return ("fn", nm, args)
    if k == "a":
        one = addr.parse(rd.take()[1])
        if one is None:
            raise Bad("addr")
        if rd.peek() == ":":
            rd.take()
            tk = rd.want("a")
            two = addr.parse(tk[1])
            if two is None:
                raise Bad("addr")
            return ("rng", one, two)
        return ("ref", one)
    raise Bad(k or "?")


def build(text):
    rd = Read(chop(text))
    node = expr(rd)
    rd.want("$")
    return node


def refs(node):
    out = []
    stack = [node]
    while stack:
        nd = stack.pop()
        if nd[0] == "ref":
            out.append(nd[1])
        elif nd[0] == "rng":
            lo, hi = nd[1], nd[2]
            for r in range(min(lo[0], hi[0]), max(lo[0], hi[0]) + 1):
                for c in range(min(lo[1], hi[1]), max(lo[1], hi[1]) + 1):
                    out.append((r, c))
        elif nd[0] == "bin":
            stack.append(nd[2])
            stack.append(nd[3])
        elif nd[0] == "fn":
            stack.extend(nd[2])
    return out
