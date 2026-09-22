"""The pinned group and how much of its header the pane shows.

The pinned group is the last one whose header top has reached the offset. Its header is shown
whole only while there is room for it: the next group's header arrives from below and pushes it
off, so the band is the smaller of the header height and the distance from the offset to the
next header. Under a carried height that distance moves whenever a row is remembered or
forgotten anywhere between the two, which is why the band is worked out again on every pass.
"""


def band(gm, off):
    gi = gm.pinned(off)
    if gi + 1 < gm.ngroups():
        nxt = gm.gtop(gi + 1)
    else:
        nxt = gm.total()
    hh = gm.ghh(gi)
    room = nxt - off
    return gi, hh if hh < room else room
