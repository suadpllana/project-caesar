from hst import vw


def kp(h):
    keep = set()
    for n in h.sd.values():
        if n in h.rs:
            keep.add(n)
    grew = True
    while grew:
        grew = False
        for n in sorted(keep):
            r = h.rs[n]
            for nm in r.p.rq:
                if nm in r.rc:
                    g = r.rc[nm]
                else:
                    g = vw.fd(h, r, nm)
                if g and g in h.rs and g not in keep:
                    keep.add(g)
                    grew = True
                    break
            if grew:
                break
    return keep
