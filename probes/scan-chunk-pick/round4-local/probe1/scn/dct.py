"""What a consulted dictionary settles for the i pages of its chunk."""

from scn import rd

UNS = 0
PASS = 1
FAIL = 2

CMP = ("ge", "le", "eq", "ne")


def verdict(cond, dic):
    """FAIL when no entry satisfies the comparison, PASS when every entry
    does (a page must also hold no null for that to pass its rows), UNS
    otherwise. Never settles nn or nu."""
    if cond.kind not in CMP:
        return UNS
    good = 0
    for e in dic:
        if rd.sat(cond, e):
            good += 1
    if good == 0:
        return FAIL
    if good == len(dic):
        return PASS
    return UNS


def settle(cond, dic, u):
    """Status of one i page with u nulls for a comparison."""
    s = verdict(cond, dic)
    if s == PASS and u:
        return UNS
    return s
