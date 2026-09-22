from . import look


def unit(pg, r):
    if pg.attr(r, "aria-atomic") == "true":
        return r
    return None


def text_of(pg, u):
    out = []
    todo = [u]
    while todo:
        x = todo.pop()
        if pg.is_text(x):
            out.append(pg.text(x))
            continue
        if look.hides(pg, x):
            continue
        todo.extend(reversed(pg.kids(x)))
    return " ".join(out)
