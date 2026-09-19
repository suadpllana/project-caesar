"""The reach: every row the change touches, and how deep it sits.

Two things make this not a walk. Nothing is applied while it runs, so every match reads the
store as it stood when the change began. And a row's group is the greatest number of links on
any chain reaching it, not the first chain that got there, so a row met again by a longer
route moves down and everything reached through it moves with it.

Relaxing that by hand is unnecessary. Links run from a parent table to a child table and no
table is reachable from itself, so walking the tables in that order settles every row of a
table before the table is expanded: by the time a table is reached, every link into it has
already been followed, and its rows' groups are final.
"""
from keep import meld


def carriers(work, md, grp, name, kind):
    """The rows of one table the change carries on from, with their group and new key."""
    by = md.rows.get(name)
    if not by:
        return None
    hold = {}
    for key, here in by.items():
        if kind == "out":
            if here.gone is not None:
                hold[key] = (grp[(name, key)], None)
        else:
            new = md.newkey(name, key)
            if new is not None:
                hold[key] = (grp[(name, key)], new)
    return hold


def walk(work, kind, tab, key, new):
    st = work.st
    md = meld.Meld()
    grp = {(tab, key): 0}
    bars = []
    if kind == "out":
        md.drop(tab, key, -1)
    else:
        md.col(tab, key, 0, "move", new, -1)
    for name in work.order:
        hold = carriers(work, md, grp, name, kind)
        if not hold:
            continue
        for li, ln in work.fan.get(name, ()):
            act = ln.goes if kind == "out" else ln.moves
            if act == "wait":
                continue
            for ck in work.find.kids(ln, hold):
                if act == "bar":
                    bars.append((li, ln.kid, ck))
                    continue
                pk = st.get(ln.kid, ck)[ln.ci]
                deep = hold[pk][0] + 1
                seat = (ln.kid, ck)
                if deep > grp.get(seat, -1):
                    grp[seat] = deep
                if act == "drop":
                    md.drop(ln.kid, ck, li)
                elif act == "clear":
                    md.col(ln.kid, ck, ln.ci, "clear", None, li)
                else:
                    md.col(ln.kid, ck, ln.ci, "move", hold[pk][1], li)
    return md, grp, bars
