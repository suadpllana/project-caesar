from tx import hold, view


def ends(c):
    if c.kind == hold.GET:
        return c.key, c.key
    return c.lo, c.hi


def differs(st, txn, c, key):
    now = view.one(st, txn, key, st.ver)
    if c.kind == hold.GET:
        return now != c.val
    return now != c.seen.get(key)


def stands(st, txn, c):
    if c.kind == hold.CHG:
        return not c.on or not st.after(c.key, txn.base)
    lo, hi = ends(c)
    for key in st.span(lo, hi):
        if st.after(key, txn.base) and differs(st, txn, c, key):
            return False
    return True
