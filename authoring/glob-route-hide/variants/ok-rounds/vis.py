

def level(ln, path):
    return 0 if ln.pb else dep(path)


def spread(held_src, src, dst, lv):
    reach = cpd(src, dst)
    out = {}
    for d, bits in enumerate(held_src):
        if not bits or d > reach:
            continue
        nd = d if d > lv else lv
        out[nd] = out.get(nd, 0) | bits
    return out


def settle_depths(acc):
    seen = 0
    for d in range(len(acc)):
        acc[d] &= ~seen
        seen |= acc[d]
    return acc


def dep(path):
    return path.count(".") + 1


def cpd(a, b):
    n = 0
    for x, y in zip(a.split("."), b.split(".")):
        if x != y:
            break
        n += 1
    return n
