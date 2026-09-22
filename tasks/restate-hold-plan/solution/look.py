"""How a computation reads its inputs.

Every computation - a rerun of a partition that exists, or a partition computed for the plan
because it no longer exists - reads what its step declares. Each partition it names is read from
storage if it exists; if it does not, it is computed for the plan from its own reads, unless it
belongs to a source, whose missing partitions nobody can bring back.

A daily step reading an hourly dataset by the day is the one exception. When the hourly dataset
has a roll-up and any hour of that day is missing, the roll-up's partition for the day is read in
place of all 24 hours - provided it exists and agrees with the corrected source once settled. A
published roll-up the correction reached does not agree, so the readers of the hours refuse it
while its own readers read it as published. The roll-up never stands in for its own computation.
"""
from plan.keep import there
from plan.span import takes


def rank_of(pp):
    """The order datasets are settled in within one end hour.

    Each dataset after the ones it reads, and each roll-up before every step that reads its hours
    by the day, because a reader has to know whether the roll-up agrees before it can use it.
    Declaration order breaks ties; it is not the order the plan prints in.
    """
    before = {name: set() for name in pp.names}
    for name in pp.names:
        for kind, src, _width in pp.reads.get(name, ()):
            if src != name:
                before[name].add(src)
            roll = pp.roll.get(src) if kind == "day" else None
            if roll is not None and roll != name:
                before[name].add(roll)
    rank, placed = {}, set()
    while len(placed) < len(pp.names):
        name = next(n for n in pp.names if n not in placed and before[n] <= placed)
        rank[name] = len(placed)
        placed.add(name)
    return rank


def named(pp, name, i):
    """Every partition the declared reads of (name, i) name, roll-ups aside."""
    for _kind, src, parts in takes(pp, name, i):
        for p in parts:
            yield src, p


def reads(pp, name, i, agrees):
    """What (name, i) reads: [(src, p, how)] with how in stored, temp, gone; and whether a
    roll-up stood in. `agrees(src, p)` answers for a partition that exists and was settled."""
    out, rolled = [], False
    for kind, src, parts in takes(pp, name, i):
        roll = pp.roll.get(src) if kind == "day" else None
        if roll is not None and roll != name \
                and not all(there(pp, src, h) for h in parts) \
                and there(pp, roll, i) and agrees(roll, i):
            out.append((roll, i, "stored"))
            rolled = True
            continue
        for p in parts:
            if there(pp, src, p):
                out.append((src, p, "stored"))
            elif src not in pp.reads:
                out.append((src, p, "gone"))
            else:
                out.append((src, p, "temp"))
    return out, rolled
