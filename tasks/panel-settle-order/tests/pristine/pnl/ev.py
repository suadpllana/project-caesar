def run(e, net, seen):
    k = e[0]
    if k == "n":
        return e[1]
    if k == "r":
        seen.add(e[1])
        return net.val[e[1]]
    a = e[1]
    if k == "add":
        return run(a[0], net, seen) + run(a[1], net, seen)
    if k == "sub":
        return run(a[0], net, seen) - run(a[1], net, seen)
    if k == "gt":
        return 1 if run(a[0], net, seen) > run(a[1], net, seen) else 0
    if k == "eq":
        return 1 if run(a[0], net, seen) == run(a[1], net, seen) else 0
    if k == "pick":
        if run(a[0], net, seen) != 0:
            return run(a[1], net, seen)
        return run(a[2], net, seen)
    raise ValueError(k)
