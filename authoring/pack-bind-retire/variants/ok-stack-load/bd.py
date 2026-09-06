from hst import vw


def us(h, r, nm):
    p = r.p
    if nm not in p.rq and nm not in p.wk:
        return ("bad", 0)
    if nm in r.rc:
        g = r.rc[nm]
    else:
        g = vw.fd(h, r, nm)
        r.rc[nm] = g
    if g:
        return ("res", g)
    return ("none", 0)
