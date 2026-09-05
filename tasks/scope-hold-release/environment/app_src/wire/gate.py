from wire.reg import SING, SCOPED


def allow(tbl, nm):
    r = tbl[nm]
    if r.life != SING:
        return True
    for d in r.deps:
        if tbl[d].life == SCOPED:
            return False
    return True
