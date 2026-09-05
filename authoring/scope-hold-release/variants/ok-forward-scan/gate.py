from wire.reg import SING, SCOPED, cycles, reach


def allow(tbl, st, nm, at):
    r = tbl[nm]
    if cycles(tbl, nm):
        return False
    if r.tag and not any(st.tag(sc) == r.tag for sc in st.upto(at)):
        return False
    if r.life != SING:
        return True
    for d in reach(tbl, nm):
        if d != nm and tbl[d].life == SCOPED:
            return False
    return True
