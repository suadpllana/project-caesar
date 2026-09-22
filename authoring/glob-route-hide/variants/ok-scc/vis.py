

def edge_level(ln, path):
    return 0 if ln.pb else dep(path)


def arriving(src_held, src, dst, lv):
    c = cpd(src, dst)
    got = {}
    for d, bits in src_held.items():
        if d <= c and bits:
            nd = max(d, lv)
            got[nd] = got.get(nd, 0) | bits
    return got


def absorb(into, got):
    changed = False
    for d, bits in got.items():
        wider = 0
        for e, b in into.items():
            if e <= d:
                wider |= b
        fresh = bits & ~wider
        if fresh:
            into[d] = into.get(d, 0) | fresh
            for e in list(into):
                if e > d:
                    into[e] &= ~fresh
                    if not into[e]:
                        del into[e]
            changed = True
    return changed


def dep(path):
    return path.count(".") + 1


def cpd(a, b):
    n = 0
    for x, y in zip(a.split("."), b.split(".")):
        if x != y:
            break
        n += 1
    return n
