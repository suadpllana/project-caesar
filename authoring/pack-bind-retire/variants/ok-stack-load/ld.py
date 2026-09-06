from hst import bd, vw


def ld(h, nm, md):
    made = []
    stack = [(nm, md, 0)]
    while stack:
        name, mode, phase = stack.pop()
        if phase == 0:
            r = h.sr(name)
            if r is not None:
                if mode == "open" and r.n not in h.op:
                    h.op.append(r.n)
                continue
            stack.append((name, mode, 1))
            for d in reversed(h.pk[name].nd):
                stack.append((d, "own", 0))
            continue
        if h.sr(name) is not None:
            continue
        p = h.pk[name]
        fx = vw.mk(h, p)
        r = h.mk(p)
        r.fx = fx
        h.sd[name] = r.n
        made.append(r.n)
        if mode == "open":
            h.op.append(r.n)
        for s in p.st:
            bd.us(h, r, s)
    return made
