from hst import vw


def kp(h):
    held = set()
    q = []
    for n in h.sd.values():
        if n in h.rs and n not in held:
            held.add(n)
            q.append(n)
    while q:
        r = h.rs[q.pop()]
        for nm in r.p.rq:
            if nm in r.rc:
                g = r.rc[nm]
            else:
                g = vw.pick(h, r, nm)
            if g and g in h.rs and g not in held:
                held.add(g)
                q.append(g)
    return held
