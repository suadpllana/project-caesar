"""The trim.

A block that stops being kept is queued the moment it happens, so the list a trim prints is
already in the order they stopped, with the blocks of any one op in allocation order. Once
printed a block is never queued again, because it can never be kept again: taking a block back
into a volume needs a peg that still keeps it.
"""


def trim(a, t):
    a.t = t
    ready = a.q
    a.q = []
    a.out.update(ready)
    return ready
