from base import tape, wire

from bay import desc, stand


# The pass over what a worker is holding.
#
# Everything a worker has been given stays with it until it goes up. A parcel
# that cannot go up now is not a parcel that is wrong; it is one whose ground has
# not arrived. Dropping it loses a picture that the next take, or the worker's
# own settling of one setting, would have let through, and nothing is going to
# hand it over a second time.
#
# One parcel going up is what lets the next one go up, so the bag is worked to a
# standstill rather than swept once. A picture resting on another picture of the
# same band is the ordinary case here, not a corner: workers publish bands as
# they go, and the bands they publish overlap.
#
# Which of two parcels goes up first does matter, and the belief that it cannot
# is the trap. A shown map only moves onto versions standing after what it shows,
# which makes it tempting to argue that anything able to go up stays able. That
# argument holds for a setting the worker already shows and fails for one it has
# never heard of: putting a version of that setting up where there was nothing
# before puts every parcel carrying the other branch of it out of reach for good.
# Two parcels in one bag can each be ready with only one of them ever going
# anywhere, so the bag is not swept. The earliest one the worker was handed goes
# up, and the whole bag is then read again from the front, because that one
# application is what decides which of the rest are still going anywhere.


def given(st, w, no):
    wire.held(st, w).append(no)


def gate(st, w):
    view = tape.seat(st, w)
    bag = wire.held(st, w)
    got = set()
    moving = True
    while moving:
        moving = False
        for no in list(bag):
            p = st.parc[no - 1]
            if not stand.ripe(st, p, view):
                continue
            bag.remove(no)
            for s in p:
                v = p[s]
                cur = view.get(s, -1)
                if cur < v:
                    view[s] = v
                    got.add(s)
            moving = True
            break
    return got
