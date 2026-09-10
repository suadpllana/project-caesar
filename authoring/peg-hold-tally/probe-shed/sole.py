"""A tally, worked out when it is asked.

Every run filed under this peg has it as its youngest living peg. Such a run stands for this peg
alone when there is no living peg under it inside the run, and its block counts when that is its
only run and no volume is holding it.
"""
from keep import cover, live


def count(a, p):
    got = a.home.get(p)
    if got is None:
        return 0
    n = 0
    for r in a.hi_at.get(p, ()):
        if not r[live.OK] or a.pn[r[live.V]][r[live.HI]] != p:
            continue
        b = r[live.B]
        if a.nh[b] or len(a.rs[b]) != 1:
            continue
        if cover.under(a, r[live.V], r[live.HI], r[live.T1]) is None:
            n += 1
    return n
