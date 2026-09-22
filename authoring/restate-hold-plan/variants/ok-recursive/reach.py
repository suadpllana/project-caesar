from plan.span import last


def _readers(pp):
    out = {}
    for name in pp.names:
        for kind, src, width in pp.reads.get(name, ()):
            out.setdefault(src, []).append((name, kind, width))
    return out


def _next(pp, src, i, name, kind, width):
    if kind == "same":
        yield i
    elif kind == "day":
        yield i // 24
    elif kind == "win":
        yield from range(i, i + width)
    elif pp.grain[src] == pp.grain[name]:
        yield i + 1
    elif pp.grain[src] == "d":
        yield from range(24 * i + 24, 24 * i + 48)
    elif i % 24 == 23:
        yield i // 24 + 1


def reach(pp):
    rd = _readers(pp)
    seen = {pp.fix}
    stack = [pp.fix]
    while stack:
        src, i = stack.pop()
        for name, kind, width in rd.get(src, ()):
            hi = last(pp, name)
            for j in _next(pp, src, i, name, kind, width):
                if j <= hi and (name, j) not in seen:
                    seen.add((name, j))
                    stack.append((name, j))
    return seen
