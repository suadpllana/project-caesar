"""Shaping the fetches a read issues.

Two holes with only a little covered ground between them cost less as one round trip than as
two, so runs close enough together are fetched as one - which means the fetch covers keys the
cache already had, and installs a stretch over them alongside the one that was already there.
That is not free either way: the run the store reports its last write over is now the wider
one, so the combined fetch is correct from a later version than the two narrow ones would have
been, and it reaches less far back for the reads that follow.

The cap is the same trade taken to its end. A read that would scatter more fetches than the cap
allows takes the whole requested range in one instead, which is wider still, later still, and
sits over everything already held.
"""


def shape(runs, lo, hi, slack, cap):
    if not runs:
        return []
    out = [[runs[0][0], runs[0][1]]]
    for a, b in runs[1:]:
        if a - out[-1][1] - 1 <= slack:
            out[-1][1] = b
        else:
            out.append([a, b])
    if len(out) > cap:
        return [(lo, hi)]
    return [(a, b) for a, b in out]
