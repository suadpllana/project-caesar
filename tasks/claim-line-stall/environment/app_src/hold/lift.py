from hold import book, name


def raised(h, job, scope, mode):
    u, c = name.cut(scope)
    if c is None:
        return scope, mode
    mine = []
    for one, m in (h.held.get(job) or {}).items():
        if name.cut(one)[1] is not None:
            mine.append((one, m))
    if len(mine) < 4:
        return scope, mode
    out = mode
    for one, m in mine:
        if name.cut(one)[0] == u and m == "w":
            out = "w"
    if (h.held.get(job) or {}).get(u) == "w":
        out = "w"
    for one, _m in book.cells(h, job, u):
        book.lose(h, job, one)
    return u, out
