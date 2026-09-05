"""Sealed independent model for scope-hold-release.

Shares no code with the reference. Where the reference threads a capture
through a driver built on wire.core and settles homes by walking each
instance's pull-in chain upward, this replays the stream with its own
instance tables, settles homes by walking the pull-in forest downward from
the roots of each resolution, and emits every scope's teardown by descending
serial rather than by reversing a list.
"""

SING, SCOPED, TRANS = 0, 1, 2
ROOT = 0


def _reaches(tbl, nm):
    out, stack = set(), [nm]
    while stack:
        cur = stack.pop()
        if cur in out or cur not in tbl:
            continue
        out.add(cur)
        stack.extend(tbl[cur][1])
        if tbl[cur][3]:
            stack.append(tbl[cur][3])
    return out


def _loops(tbl, nm):
    stack = [(nm, ())]
    while stack:
        cur, path = stack.pop()
        if cur in path:
            return True
        if cur not in tbl:
            continue
        nxt = path + (cur,)
        for d in tbl[cur][1]:
            stack.append((d, nxt))
        if tbl[cur][3]:
            stack.append((tbl[cur][3], nxt))
    return False


def play(rows, ops):
    tbl = {}
    for nm, life, deps, facs, tag, wraps, shut in rows:
        tbl[nm] = (life, list(deps), list(facs), wraps, tag, shut)

    live = [ROOT]
    tags = {ROOT: ""}
    nxt = 0
    sng, scp = {}, {}
    serial = 0
    made = {}
    mint = {}
    out = []

    def chain(upto):
        if upto not in live:
            return []
        return live[:live.index(upto) + 1]

    def allowed(nm, at):
        life, deps, _facs, wraps, tag, _shut = tbl[nm]
        del deps, wraps
        if _loops(tbl, nm):
            return False
        if tag and not [s for s in chain(at) if tags.get(s, "") == tag]:
            return False
        if life != SING:
            return True
        for d in sorted(_reaches(tbl, nm)):
            if d != nm and tbl[d][0] == SCOPED:
                return False
        return True

    def pinned(at, tag):
        for s in reversed(chain(at)):
            if tags.get(s, "") == tag:
                return s
        return ROOT

    def grow(nm, at, cause, rooted):
        nonlocal serial
        life, deps, _facs, wraps, tag, _shut = tbl[nm]
        if life == SING and nm in sng:
            return
        if life == SCOPED and (nm, at) in scp:
            return
        serial += 1
        me = serial
        deep = rooted or life == SING
        under = ROOT if life == SING else at
        if wraps:
            grow(wraps, under, cause, deep)
        for d in deps:
            grow(d, under, cause, deep)
        if life == SING:
            sng[nm] = me
        elif life == SCOPED:
            scp[(nm, at)] = me
        if deep:
            home = ROOT
        elif tag:
            home = pinned(at, tag)
        else:
            home = at
        made[me] = (nm, home, cause)

    for op in ops:
        k = op[0]
        top = live[-1]
        if k == "open":
            nxt += 1
            live.append(nxt)
            tags[nxt] = op[1] if len(op) > 1 else ""
        elif k == "close":
            if len(live) == 1:
                out.append(("refused", "close", 0))
                continue
            gone = live.pop()
            for s in sorted([s for s in made if made[s][1] == gone], reverse=True):
                nm = made[s][0]
                out.append(("torn", nm, gone, made[s][2]))
                del made[s]
                shut = tbl[nm][5] if nm in tbl else ""
                if not shut:
                    continue
                landing = live[-1]
                if not allowed(shut, landing):
                    out.append(("refused", shut, landing))
                    continue
                grow(shut, landing, shut, False)
            for key in sorted([k2 for k2 in scp if k2[1] == gone]):
                del scp[key]
        elif k == "resolve":
            nm = op[1]
            if not allowed(nm, top):
                out.append(("refused", nm, top))
                continue
            grow(nm, top, nm, False)
            for f in tbl[nm][2]:
                mint[f] = top
        elif k == "invoke":
            f = op[1]
            if f not in mint:
                out.append(("refused", f, top))
                continue
            at = mint[f]
            if not allowed(f, at):
                out.append(("refused", f, top))
                continue
            grow(f, at, f, False)
    return out
