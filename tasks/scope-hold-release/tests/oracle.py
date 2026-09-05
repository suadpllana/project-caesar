"""Sealed independent model for scope-hold-release.

Shares no code with the reference. Where the reference threads a capture
through a driver built on wire.core, this replays the stream with its own
instance tables and settles ownership from a mint register, then emits each
scope's teardown by descending serial rather than by reversing a list.
"""

SING, SCOPED, TRANS = 0, 1, 2
ROOT = 0


def _reaches(tbl, nm):
    out, stack = set(), [nm]
    while stack:
        cur = stack.pop()
        if cur in out:
            continue
        out.add(cur)
        stack.extend(tbl[cur][1])
    return out


def _ok(tbl, nm):
    if tbl[nm][0] != SING:
        return True
    for d in sorted(_reaches(tbl, nm)):
        if d != nm and tbl[d][0] == SCOPED:
            return False
    return True


def play(rows, ops):
    tbl = {}
    for nm, life, deps, facs in rows:
        tbl[nm] = (life, list(deps), list(facs))

    live = [ROOT]
    nxt = 0
    sng, scp = {}, {}
    serial = 0
    made = {}
    mint = {}
    out = []

    def grow(nm, at, cause):
        nonlocal serial
        life = tbl[nm][0]
        if life == SING and nm in sng:
            return
        if life == SCOPED and (nm, at) in scp:
            return
        serial += 1
        me = serial
        under = ROOT if life == SING else at
        for d in tbl[nm][1]:
            grow(d, under, cause)
        if life == SING:
            sng[nm] = me
        elif life == SCOPED:
            scp[(nm, at)] = me
        made[me] = (nm, ROOT if life == SING else at, cause)

    for op in ops:
        k = op[0]
        top = live[-1]
        if k == "open":
            nxt += 1
            live.append(nxt)
        elif k == "close":
            if len(live) == 1:
                out.append(("refused", "close", 0))
                continue
            gone = live.pop()
            mine = sorted([s for s in made if made[s][1] == gone], reverse=True)
            for s in mine:
                out.append(("torn", made[s][0], gone, made[s][2]))
                del made[s]
            for key in sorted([k2 for k2 in scp if k2[1] == gone]):
                del scp[key]
        elif k == "resolve":
            nm = op[1]
            if not _ok(tbl, nm):
                out.append(("refused", nm, top))
                continue
            grow(nm, top, nm)
            for f in tbl[nm][2]:
                mint[f] = top
        elif k == "invoke":
            f = op[1]
            if f not in mint or not _ok(tbl, f):
                out.append(("refused", f, top))
                continue
            grow(f, mint[f], f)
    return out
