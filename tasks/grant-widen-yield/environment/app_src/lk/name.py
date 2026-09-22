def depth(res):
    return res.count(".")


def up(res):
    i = res.rfind(".")
    return res[:i] if i >= 0 else None


def chain(res):
    out = []
    cur = res
    while cur is not None:
        out.append(cur)
        cur = up(cur)
    out.reverse()
    return out


def key(res):
    return tuple(int(p[1:]) for p in res.split("."))


def deep(res):
    return (-depth(res), key(res))
