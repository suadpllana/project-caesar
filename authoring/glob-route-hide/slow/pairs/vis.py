"""Visibility as a region depth.

A candidate that a module M holds is always seen from M itself, so the region it can be seen
from is either every module or the subtree of one of M's ancestors (M included). That makes the
region a single number relative to M: 0 for every module, d >= 1 for the subtree of M's
ancestor at depth d. Along a chain of lines the region only ever shrinks, and across routes the
widest one counts, so for any one candidate the regions it arrives with are totally ordered.

A module's holdings are kept as cumulative sets: cs[t] is every binding the module holds that
is seen from a region of depth t or wider. cs[dep(M)] is everything the module holds.
"""


def lvl(ln, path):
    """Region depth of what line `ln` of module `path` passes on: every module, or its own subtree."""
    return 0 if ln.pb else dep(path)


def take(cs, src, dst, lv, top):
    """What module `dst` receives through a line of level `lv` from `src`'s cumulative sets.

    A binding held at `src` with region depth d is seen from `dst` exactly when d is no deeper
    than the common prefix of the two paths, and it arrives with the narrower of its own region
    and the line's: depth max(d, lv). So for every t no shallower than `lv`, the bindings
    reaching `dst` at depth t or wider are those `src` holds at depth min(t, common prefix),
    and nothing reaches `dst` at a depth shallower than `lv`.
    """
    c = cpd(src, dst)
    out = [0] * (top + 1)
    for t in range(lv, top + 1):
        out[t] = cs[t if t < c else c]
    return out


def dep(path):
    return path.count(".") + 1


def cpd(a, b):
    n = 0
    for x, y in zip(a.split("."), b.split(".")):
        if x != y:
            break
        n += 1
    return n
