from plan.keep import there
from plan.span import takes


def plan_reads(pp, name, i, roll_ok):
    """Yield ('roll', r, d), ('have', s, p), ('make', s, p) or ('none', s, p)."""
    for kind, src, parts in takes(pp, name, i):
        r = pp.roll.get(src)
        if kind == "day" and r is not None and r != name:
            if any(not there(pp, src, h) for h in parts) and there(pp, r, i) and roll_ok(r, i):
                yield ("roll", r, i)
                continue
        for p in parts:
            if there(pp, src, p):
                yield ("have", src, p)
            elif src in pp.reads:
                yield ("make", src, p)
            else:
                yield ("none", src, p)
