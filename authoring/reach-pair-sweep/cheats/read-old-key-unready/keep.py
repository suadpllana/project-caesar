"""Objects kept only so a queued finalizer can run, and the queue itself.

The queue is settled against what the collection reached, before any of this keeping is granted.
Settle it afterwards and an object reachable only from another finalizable object looks like it
is being kept rather than like garbage, and never gets finalized at all.

What a queued finalizer keeps is its object and everything that object reaches, by the same walk
and the same pair rule, blocked from anything already reached so the two sets stay apart. They
have to stay apart: weak clearing and promotion both ask about the first set, and an object kept
only to run a finalizer is in neither.

Scope follows the collection kind. A minor collection can only queue and only keep nursery
objects; an old object with an unrun finalizer is not garbage yet, because nothing this
collection did could show that it was.
"""
from col import scan
from mem import heap


def _scope(h, full):
    return [i for i in sorted(h.objs) if full or h.objs[i].space == heap.NURSERY]


def settle(h, seen, full):
    fresh = [i for i in _scope(h, full)
             if i not in seen and h.objs[i].fin is not None
             and i not in h.done and i not in h.queue]

    start = [i for i in h.queue if i in h.objs] + fresh
    if not full:
        start = [i for i in start if h.objs[i].space == heap.NURSERY]
    held = scan.reach(h, start, full, frozenset(seen)) if start else set()
    return fresh, held
