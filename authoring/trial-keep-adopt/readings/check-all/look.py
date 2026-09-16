"""Does a kept result still stand?

The reads the last evaluation took are demanded again in the order it took them and compared with
the value each returned then. The walk stops at the first read that comes back different: the
later reads are not demanded at all, because the evaluation that is about to happen may not read
them, and demanding them would force evaluations of fields this one has stopped depending on.

Nothing here asks what changed. A publication is not propagated anywhere; it is found, or not
found, by this walk running downwards from whatever was asked for.
"""


def stands(f, rec, want, seen):
    ok = True
    for dep, was in rec[1]:
        if want(f, dep, seen) != was:
            ok = False
    return ok
