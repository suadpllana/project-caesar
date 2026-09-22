from . import hole


def at(tb, lo, hi, s, now):
    usable = []
    for st in tb.items:
        if now - st.mark <= s:
            usable.append(st)
    if hole.runs(usable, lo, hi):
        return None
    return now
