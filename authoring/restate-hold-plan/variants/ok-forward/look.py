from plan.keep import there
from plan.span import takes


def groups(pp, name, i):
    """Per read: (roll-up or None, source, parts)."""
    out = []
    for kind, src, parts in takes(pp, name, i):
        roll = pp.roll.get(src) if kind == "day" else None
        if roll == name or (roll is not None and all(there(pp, src, h) for h in parts)):
            roll = None
        out.append((roll, src, parts))
    return out
