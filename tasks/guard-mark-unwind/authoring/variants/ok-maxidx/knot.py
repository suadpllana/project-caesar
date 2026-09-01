"""Band bookkeeping: what a failed child does to its siblings, and what leaves the band.

reap is unchanged from the shipped version. A child that ends carrying anything other
than a cut hands its payloads to the band and the band's own guard is marked, which is
what stops the siblings.

wait is the first correction. A fiber standing at the close of a band with children still
running cannot leave, whatever mark has reached it. The shipped version raises there and
walks out of the band while its children are still alive. Holding costs nothing and gains
the property the whole thing turns on: the fiber is asked again when the last child ends,
so the answer is recomputed against the marks that stand at that moment rather than the
ones that stood when it first tried to leave.

snag is the second. A fiber unwinding into a band it still owns marks the band's guard,
so the children stop instead of running to completion under an exception that is already
travelling.

shut is the third and it is the ordering rule. Three outcomes, tested in this order. A
mark on a guard enclosing the band outranks everything the children collected, and the
cut leaves alone - the fiber is being torn down and what its children failed at is not
reported. Otherwise the collected payloads leave as a bundle, ordered by when each child
ended and then by the order the children were made, which is not the order they were
made whenever a child spawned later ends earlier. Otherwise, if the mark that reached the
fiber is the band's own, the band closing is what that mark was for and nothing leaves.
"""


def reap(bd, fid, t, pay):
    for p in pay:
        bd.errs.append((t, fid, p))
    return True


def wait(bd, g, left):
    return "hold"


def snag(bd, left):
    return True


def shut(bd, ch, g):
    if g is not None and g is not bd.gd:
        return ("cut", g)
    if bd.errs:
        return ("bun", [e[2] for e in sorted(bd.errs, key=lambda e: (e[0], e[1]))])
    return None
