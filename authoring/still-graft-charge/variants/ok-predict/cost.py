"""The charge, kept as a running total rather than counted when it is asked for.

A line's charge only moves when a block's holders change, and the events that can change them
are few and local: a write opens and closes windows on the cells it names, a graft lays down
the cells its origin holds, a lift moves stills between lines, a drop takes one away. Taking a
still moves nothing at all. Every one of those settles the blocks it touched, so the answer is
already there when it is asked for.
"""
from led import hold


def charge(st, name):
    return hold.kit(st).charge.get(name, 0)
