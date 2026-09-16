from fld import keep, say


def body(f, name, want, seen):
    kind = f.kind[name]
    a = f.args[name]
    reads = []

    def rd(one):
        v = want(f, one, seen)
        reads.append((one, v))
        return v

    if kind == "sum":
        v = 0
        for one in a:
            v += rd(one)
    elif kind == "cap":
        v = min(rd(a[0]), int(a[1]))
    elif kind == "pick":
        v = rd(a[1]) if rd(a[0]) else rd(a[2])
    else:
        v = rd(a[1]) if rd(a[0]) else 0
    say.ran(f, name)
    keep.put(f, name, v, tuple(reads))
    return v
