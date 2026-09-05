from wire.reg import SING, SCOPED, reach


def allow(tbl, nm):
    r = tbl[nm]
    if r.life != SING:
        return True
    for d in reach(tbl, nm):
        if d != nm and tbl[d].life == SCOPED:
            return False
    return True
