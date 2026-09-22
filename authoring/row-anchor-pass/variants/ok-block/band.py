"""The pinned group and how much of its header the pane actually shows.

Two rules, and the second is the one the shipped pane has never had. The pinned group is the
last one whose header top has reached the offset, found by descending the group tops rather
than walking them. Its header is shown whole only while there is room for it: the next group's
header arrives from below and pushes it off, so the band is the smaller of the header height
and the distance from the offset to the next header. That distance is what makes the band move
when a row inside the pinned group is measured, which is why the band cannot be settled once
per frame.
"""


def pinned(gm, off):
    lo = 0
    hi = gm.ngroups() - 1
    gi = 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if gm.gtop(mid) <= off:
            gi = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return gi


def band(gm, off):
    gi = pinned(gm, off)
    if gi + 1 < gm.ngroups():
        nxt = gm.gtop(gi + 1)
    else:
        nxt = gm.total()
    hh = gm.ghh(gi)
    room = nxt - off
    return gi, hh if hh < room else room
