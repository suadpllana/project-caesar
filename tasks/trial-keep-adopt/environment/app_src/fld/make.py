from fld import keep


def body(f, name, want):
    kind = f.kind[name]
    a = f.args[name]
    if kind == "sum":
        v = 0
        for one in a:
            v += want(f, one)
    elif kind == "cap":
        v = min(want(f, a[0]), int(a[1]))
    elif kind == "pick":
        one = want(f, a[1])
        two = want(f, a[2])
        v = one if want(f, a[0]) else two
    else:
        arm = want(f, a[1])
        v = arm if want(f, a[0]) else 0
    keep.put(f, name, v)
    return v
