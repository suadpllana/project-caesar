from scr.pin import CONTEXT, script, reading


def spans(before, after):
    walk = reading(before, after, script(before, after))
    out = []
    cur = None
    pend = []
    since = CONTEXT
    for kind, i, j in walk:
        if kind == "K":
            since += 1
            if cur is not None:
                if since >= CONTEXT:
                    out.append(cur)
                    cur = None
                    pend = []
                else:
                    pend.append(j)
            continue
        if cur is None:
            cur = set()
        else:
            cur.update(pend)
        pend = []
        since = 0
        if kind == "A":
            cur.add(j)
    if cur is not None:
        out.append(cur)
    return [g for g in out if g]
