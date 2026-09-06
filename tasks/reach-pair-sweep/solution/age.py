"""Ageing and promotion.

A nursery object that came through a collection gets a year older, and at `PROMOTE_AGE` it moves
to old space. Being kept so a finalizer can run is not coming through a collection: those objects
do not age, so an object waiting on its finalizer cannot promote out of the nursery while it
waits. If its finalizer stores it back somewhere live it starts ageing again from the next
collection, like anything else that survived.

A pinned object cannot move, so it stays in the nursery and keeps the age it has reached. It does
not lose the age and it does not promote late in a rush once unpinned - it promotes at the first
collection it survives after the pin comes off.
"""
from mem import heap


def promote(h, seen, held):
    moved = []
    for i in sorted(h.objs):
        o = h.objs[i]
        if o.space != heap.NURSERY:
            continue
        if i not in seen or i in held:
            continue
        o.age += 1
        if o.age >= heap.PROMOTE_AGE and o.pins == 0:
            o.space = heap.OLD
            moved.append(i)
    return moved
