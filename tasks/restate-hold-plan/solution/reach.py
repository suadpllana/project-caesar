"""What the correction reaches.

The corrected partition, and every partition of a step that has ended by now and reads a reached
partition by its declared reads - whether or not the partitions in between still exist, because
a partition that has expired still stood between its inputs and its readers when they were built.

Every read looks back in time, so nothing ending before the corrected partition can be reached:
the walk starts at the fix and inverts each read arithmetically rather than indexing every
partition from hour 0, which on two years of hourly history is what does not fit the clock.
"""
from plan.span import last


def fed_by(pp, src, i, name, kind, width):
    """The partitions of `name` whose `kind` read of `src` names partition i of src."""
    if kind == "same":
        return [i]
    if kind == "day":
        return [i // 24]
    if kind == "win":
        return range(i, i + width)
    if pp.grain[src] == pp.grain[name]:
        return [i + 1]
    if pp.grain[src] == "d":
        # an hourly step reads the day before its own: all 24 hours of the next day
        return range(24 * (i + 1), 24 * (i + 2))
    # a daily step reads the last hour of the day before its own
    return [(i + 1) // 24] if (i + 1) % 24 == 0 else []


def reach(pp):
    readers = {}
    for name in pp.names:
        for kind, src, width in pp.reads.get(name, ()):
            readers.setdefault(src, []).append((name, kind, width))
    got = {pp.fix}
    todo = [pp.fix]
    while todo:
        src, i = todo.pop()
        for name, kind, width in readers.get(src, ()):
            top = last(pp, name)
            for j in fed_by(pp, src, i, name, kind, width):
                if 0 <= j <= top and (name, j) not in got:
                    got.add((name, j))
                    todo.append((name, j))
    return got
