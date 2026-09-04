"""A second reading of the link, sharing no code with the machine or the policy.

The machine drives a book through hooks and asks a policy four questions. This
walks the plan in one pass and keeps its own tables, so agreement between the
two is evidence that the rules pin one answer rather than evidence that one
implementation was copied twice.
"""

WINF = 40
WINL = 120
LAG = 3
THR = 20
IDLE = 7
FLOOR = 12
MINB = 5
LINK = -1


def settle(plan):
    ticks = int(plan["ticks"])
    rows = []
    told = {LINK: []}
    seat = {LINK: WINL}
    snt, tkn, park, last, shut = {}, {}, {}, {}, {}
    lsnt = 0
    ltkn = 0
    gone = 0

    def arm(fd, when):
        snt[fd] = 0
        tkn[fd] = 0
        park[fd] = []
        last[fd] = when
        shut[fd] = None
        seat[fd] = WINF
        told[fd] = []

    def learned(level, when):
        base = WINL if level == LINK else WINF
        out = base
        for at, value in told.get(level, ()):
            if at <= when - LAG:
                out = value
        return out

    for fd in sorted(int(x) for x in plan["feeds"]):
        arm(fd, 0)

    byte = {}
    for item in plan["ev"]:
        byte.setdefault(int(item[0]), []).append(
            (str(item[1]), int(item[2]),
             int(item[3]) if len(item) > 3 else 0))

    for when in range(ticks):
        for op, fd, count in byte.get(when, []):
            if op == "a":
                room = learned(LINK, when)
                if shut.get(fd, 0) is not None:
                    was = shut.get(fd)
                    if was is not None and when - was < LAG and lsnt + count <= room:
                        lsnt += count
                        gone += count
                        rows.append(("late", when, fd, count))
                    else:
                        rows.append(("over", when, fd, count))
                elif snt[fd] + count > learned(fd, when) or lsnt + count > room:
                    rows.append(("over", when, fd, count))
                else:
                    snt[fd] += count
                    lsnt += count
                    park[fd].append(count)
                    last[fd] = when
            elif op == "t":
                if shut.get(fd, 0) is None and park[fd]:
                    got = park[fd].pop(0)
                    tkn[fd] += got
                    ltkn += got
            elif op == "x":
                if shut.get(fd, 0) is None:
                    stuck = sum(park[fd])
                    park[fd] = []
                    shut[fd] = when
                    seat.pop(fd, None)
                    if stuck:
                        gone += stuck
                        rows.append(("drop", when, fd, stuck))
            elif op == "o":
                if shut.get(fd, 0) is not None:
                    arm(fd, when)

        want = []
        for level in [LINK] + [f for f in sorted(shut) if shut[f] is None]:
            if level not in seat:
                continue
            if level == LINK:
                value = ltkn + gone + WINL
                spent = lsnt
            else:
                span = FLOOR if when - last[level] >= IDLE else WINF
                value = tkn[level] + span
                spent = snt[level]
            here = seat[level]
            if value > here:
                due = (learned(level, when) - spent < MINB
                       and value - spent >= MINB)
                if value - here >= THR or due:
                    want.append((level, "grant", value))
            elif value < here:
                want.append((level, "pull", value))
        for level, kind, value in sorted(set(want)):
            seat[level] = value
            told.setdefault(level, []).append((when, value))
            rows.append((kind, when, level, value))

    left = dict((fd, sum(park[fd])) for fd in sorted(shut) if shut[fd] is None)
    return [list(r) for r in rows], left
