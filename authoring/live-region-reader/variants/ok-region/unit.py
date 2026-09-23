"""ok-region: where a difference is placed, what holds it, and its unit."""


def place(pg, look, know, k, cur):
    r, n = k
    if cur is not None:
        return cur[1]
    a = know.expect(n, r)[1]
    shown, reg = look.where(a)
    return a if shown and reg == r else None


def path(pg, look, know, k, cur):
    r = k[0]
    s = place(pg, look, know, k, cur)
    if s is None:
        return [r]
    out = [s]
    while out[-1] != r:
        out.append(pg.up(out[-1]))
    return out


def held(pg, look, know, k, cur):
    return any(pg.attr(x, "aria-busy") == "true" for x in path(pg, look, know, k, cur))


def unit(pg, look, know, k, cur):
    if place(pg, look, know, k, cur) is None:
        return None
    for x in path(pg, look, know, k, cur):
        v = pg.attr(x, "aria-atomic")
        if v == "true":
            return x
        if v == "false":
            return None
    return None


def spoken(pg, u):
    words = []
    todo = [u]
    while todo:
        x = todo.pop()
        if pg.is_text(x):
            words.append(pg.text(x))
        elif pg.attr(x, "hidden") is None and pg.attr(x, "aria-hidden") != "true":
            todo.extend(reversed(pg.kids(x)))
    return " ".join(words)
