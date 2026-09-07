from mem import heap


def wipe(h, seen, full):
    out = []
    for name in sorted(h.weak):
        w = h.weak[name]
        if w.wiped:
            continue
        if w.tgt not in seen:
            w.wiped = True
            out.append(name)
    return out


def release(h, seen, held, full):
    scope = sorted(h.objs) if full else sorted(h.young)
    return [i for i in scope if i not in seen and i not in held]
