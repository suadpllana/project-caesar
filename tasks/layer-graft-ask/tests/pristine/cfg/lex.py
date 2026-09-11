import re

SEG = re.compile(r"[a-z][a-z0-9]{0,7}\Z")
INT = re.compile(r"-?[0-9]{1,9}\Z")

MAXSEG = 24


class Ent:
    __slots__ = ("kind", "a", "b", "expr", "guard")

    def __init__(self, kind, a, b, expr, guard):
        self.kind = kind
        self.a = a
        self.b = b
        self.expr = expr
        self.guard = guard


class Qry:
    __slots__ = ("kind", "path", "stop", "shown")

    def __init__(self, kind, path, stop, shown):
        self.kind = kind
        self.path = path
        self.stop = stop
        self.shown = shown


class Plan:
    __slots__ = ("layers", "asks")

    def __init__(self, layers, asks):
        self.layers = layers
        self.asks = asks


def path(tok):
    segs = tok.split(".")
    if not 1 <= len(segs) <= MAXSEG:
        raise ValueError("path %r" % tok)
    for s in segs:
        if not SEG.match(s):
            raise ValueError("path %r" % tok)
    return tuple(segs)


def num(tok):
    if not INT.match(tok):
        raise ValueError("int %r" % tok)
    return int(tok)


def expr(toks, i):
    if i >= len(toks):
        raise ValueError("expression ends early")
    head = toks[i]
    if head == "lit":
        return ("lit", num(toks[i + 1])), i + 2
    if head in ("now", "old"):
        return (head, path(toks[i + 1])), i + 2
    if head in ("sum", "top"):
        a, i = expr(toks, i + 1)
        b, i = expr(toks, i)
        return (head, a, b), i
    if head == "pick":
        p = path(toks[i + 1])
        a, i = expr(toks, i + 2)
        b, i = expr(toks, i)
        return ("pick", p, a, b), i
    raise ValueError("expression %r" % head)


def guard(toks):
    if not toks:
        return None
    if toks[0] == "if" and len(toks) == 3:
        return ("if", path(toks[1]), num(toks[2]))
    if toks[0] == "un" and len(toks) == 2:
        return ("un", path(toks[1]))
    raise ValueError("guard %r" % " ".join(toks))


def parse(text):
    layers = []
    asks = []
    for raw in text.split("\n"):
        if raw == "":
            continue
        toks = raw.split(" ")
        head = toks[0]
        if head == "lay":
            if len(toks) != 1:
                raise ValueError("lay takes no argument")
            if asks:
                raise ValueError("no entry may follow a query")
            layers.append([])
            continue
        if head in ("ask", "tot"):
            if len(toks) == 2:
                stop = None
            elif len(toks) == 3:
                stop = num(toks[2])
                if not 0 <= stop <= len(layers):
                    raise ValueError("stop %d" % stop)
            else:
                raise ValueError("%s takes a path and an optional layer count" % head)
            asks.append(Qry(head, path(toks[1]), stop, toks[1]))
            continue
        if head not in ("put", "cut", "mix"):
            raise ValueError("op %r" % head)
        if asks:
            raise ValueError("no entry may follow a query")
        if not layers:
            raise ValueError("entry before the first lay")
        if head == "put":
            p = path(toks[1])
            e, i = expr(toks, 2)
            layers[-1].append(Ent("put", p, None, e, guard(toks[i:])))
        elif head == "cut":
            p = path(toks[1])
            layers[-1].append(Ent("cut", p, None, None, guard(toks[2:])))
        else:
            a = path(toks[1])
            b = path(toks[2])
            layers[-1].append(Ent("mix", a, b, None, guard(toks[3:])))
    return Plan(layers, asks)
