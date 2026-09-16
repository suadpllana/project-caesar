INSIDE = ("ask",)


def walk(lines):
    open_at = None
    for at, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        w = tuple(line.split())
        if open_at is not None:
            if w[0] == "end":
                open_at = None
                yield w
                continue
            if w[0] not in INSIDE:
                raise ValueError("line %d: %s is not allowed inside a block" % (at, w[0]))
        elif w[0] == "end":
            raise ValueError("line %d: end with no block open" % at)
        elif w[0] == "try":
            open_at = at
        yield w
    if open_at is not None:
        raise ValueError("line %d: block never closed" % open_at)


def read(path):
    with open(path, encoding="utf-8") as fh:
        for w in walk(fh):
            yield w
