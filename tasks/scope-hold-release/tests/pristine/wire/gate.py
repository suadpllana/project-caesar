from wire.reg import SING, SCOPED


def allow(tbl, st, nm, at):
    r = tbl[nm]
    if r.tag and not any(st.tag(sc) == r.tag for sc in st.upto(st.top())):
        return False
    if r.life != SING:
        return True
    for d in r.deps:
        if tbl[d].life == SCOPED:
            return False
    return True
