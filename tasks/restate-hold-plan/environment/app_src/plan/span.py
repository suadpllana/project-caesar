def span(pp, name, i):
    if pp.grain[name] == "h":
        return i, i + 1
    return 24 * i, 24 * i + 24


def starts(pp, name, i):
    return span(pp, name, i)[0]


def ends(pp, name, i):
    return span(pp, name, i)[1]


def last(pp, name):
    if pp.grain[name] == "h":
        return pp.now - 1
    return pp.now // 24 - 1


def takes(pp, name, i):
    out = []
    for kind, src, width in pp.reads[name]:
        if kind == "same":
            parts = [i]
        elif kind == "day":
            parts = list(range(24 * i, 24 * i + 24))
        elif kind == "win":
            parts = list(range(i - width + 1, i + 1))
        else:
            begin = starts(pp, name, i)
            parts = [begin - 1] if pp.grain[src] == "h" else [begin // 24 - 1]
        out.append((kind, src, [p for p in parts if p >= 0]))
    return out
