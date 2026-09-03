OPS = ("add", "sub", "gt", "eq", "pick")


def cut(s):
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c in " ,":
            i += 1
            continue
        if c in "()":
            out.append(c)
            i += 1
            continue
        j = i
        while j < len(s) and s[j] not in " ,()":
            j += 1
        out.append(s[i:j])
        i = j
    return out


def term(tk, i):
    t = tk[i]
    if t in OPS:
        if tk[i + 1] != "(":
            raise ValueError(t)
        args = []
        i += 2
        while tk[i] != ")":
            e, i = term(tk, i)
            args.append(e)
        return (t, tuple(args)), i + 1
    try:
        return ("n", int(t)), i + 1
    except ValueError:
        return ("r", t), i + 1


def expr(s):
    e, i = term(cut(s), 0)
    return e


def parse(text):
    feeds = {}
    gauges = {}
    latch = []
    rounds = []
    order = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        p = ln.split()
        h = p[0]
        if h == "F":
            feeds[p[1]] = int(p[2])
            order.append(p[1])
        elif h == "G":
            gauges[p[1]] = expr(" ".join(p[2:]))
            order.append(p[1])
        elif h == "T":
            wr = []
            for w in p[3:]:
                k, v = w.split("=")
                wr.append((k, int(v)))
            latch.append((p[1], p[2], tuple(wr)))
        elif h == "R":
            wr = []
            for w in p[1:]:
                k, v = w.split("=")
                wr.append((k, int(v)))
            rounds.append(tuple(wr))
        else:
            raise ValueError(h)
    return feeds, gauges, latch, rounds, order
