"""What a claim covers, and whether it still stands.

A point read covers its key. A scan that came back with fewer rows than it asked for covers its
whole range, because anything appearing anywhere in that range would have been returned. A scan
that filled its row limit covers only as far as the last row it returned: the rows up to that
one decide the answer, and nothing past it can reach into a list that is already full unless
something inside the cover moves first, which is caught on its own account.

Standing is judged by value. Answering the read again under the same cover, against the rows
committed now, has to give what it gave - so a key another transaction wrote back to the value
it already held leaves the read standing. A change claim is judged by version instead: it stops
standing when any commit after the base stamped its key, whatever value that commit wrote, and
a change a rollback took back claims nothing at all.

`stands` is the whole test and is used once, when a claim is made, because a read taken at a
base the rows have already moved past is wrong before anything else happens. `moved` is the
same test restricted to a key that has just moved, which is what every later check uses.
"""
from tx import hold, view


def ends(c):
    """The lowest and highest key a claim's answer was drawn from."""
    if c.kind == hold.GET:
        return c.key, c.key
    if len(c.seen) == c.n:
        return c.lo, next(reversed(c.seen))
    return c.lo, c.hi


def differs(st, txn, c, key):
    """Does this claim answer differently at key now than it did when it was made."""
    now = view.one(st, txn, key, c.i, st.ver)
    if c.kind == hold.GET:
        return now != c.val
    return now != c.seen.get(key)


def stands(st, txn, c):
    """The whole test, over every key inside the cover that a commit after the base moved."""
    if c.kind == hold.CHG:
        return not c.on or not st.after(c.key, txn.base)
    lo, hi = ends(c)
    for key in st.span(lo, hi):
        if st.after(key, txn.base) and differs(st, txn, c, key):
            return False
    return True


def moved(st, txn, c, key):
    """The same test restricted to one key that has just moved."""
    if c.kind == hold.CHG:
        return c.on and c.key == key and st.after(key, txn.base)
    lo, hi = ends(c)
    return lo <= key <= hi and differs(st, txn, c, key)
