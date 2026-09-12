from hold import book, name


def raised(h, job, scope, mode):
    unit, cell = name.cut(scope)
    if cell is None:
        return scope, mode
    mine = h.byjob.get(job) or {}
    cells = [m for one, m in mine.items()
             if name.cut(one)[1] is not None and name.cut(one)[0] == unit]
    if len(cells) < 4:
        return scope, mode
    return unit, book.strongest(mode, mine.get(unit, "r"), *cells)
