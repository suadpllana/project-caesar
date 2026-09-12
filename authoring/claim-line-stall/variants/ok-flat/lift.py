from hold import book, name


def raised(h, job, scope, mode):
    unit, cell = name.cut(scope)
    if cell is None:
        return scope, mode
    here = book.mine_here(h, job, unit)
    cells = [m for one, m in here.items() if name.cut(one)[1] is not None]
    if len(cells) < 4:
        return scope, mode
    return unit, book.strongest(mode, here.get(unit, "r"), *cells)
