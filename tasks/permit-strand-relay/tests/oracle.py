"""A second reading of the link, sharing no code with the machine or the policy.

The machine drives a book through hooks and asks a policy four questions. This
walks the plan in one pass and keeps its own tables, so agreement between the
two is evidence that the rules pin one answer rather than evidence that one
implementation was copied twice. It has to finish a wide stream too, so it
keeps a heap of idle deadlines and looks up what a producer has learned by
bisection rather than by walking the whole record.
"""

import bisect
import heapq

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
    told_at = {LINK: []}
    told_of = {LINK: []}
    seat = {LINK: WINL}
    snt, tkn, park, last, shut = {}, {}, {}, {}, {}
    clock = []
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
        told_at[fd] = []
        told_of[fd] = []
        heapq.heappush(clock, (when + IDLE, fd))

    def learned(level, when):
        base = WINL if level == LINK else WINF
        ats = told_at.get(level)
        if not ats:
            return base
        idx = bisect.bisect_right(ats, when - LAG)
        return base if idx == 0 else told_of[level][idx - 1]

    for fd in sorted(int(x) for x in plan["feeds"]):
        arm(fd, 0)

    byte = {}
    for item in plan["ev"]:
        byte.setdefault(int(item[0]), []).append(
            (str(item[1]), int(item[2]),
             int(item[3]) if len(item) > 3 else 0))

    for when in range(ticks):
        poke = set()
        for op, fd, count in byte.get(when, []):
            if op == "a":
                room = learned(LINK, when)
                if shut.get(fd, 0) is not None:
                    was = shut.get(fd)
                    if was is not None and when - was < LAG and lsnt + count <= room:
                        lsnt += count
                        gone += count
                        poke.add(LINK)
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
                    heapq.heappush(clock, (when + IDLE, fd))
                    poke.add(fd)
                    poke.add(LINK)
            elif op == "t":
                if shut.get(fd, 0) is None and park[fd]:
                    got = park[fd].pop(0)
                    tkn[fd] += got
                    ltkn += got
                    poke.add(fd)
                    poke.add(LINK)
            elif op == "x":
                if shut.get(fd, 0) is None:
                    stuck = sum(park[fd])
                    park[fd] = []
                    shut[fd] = when
                    seat.pop(fd, None)
                    if stuck:
                        gone += stuck
                        poke.add(LINK)
                        rows.append(("drop", when, fd, stuck))
            elif op == "o":
                if shut.get(fd, 0) is not None:
                    arm(fd, when)
                    poke.add(fd)

        while clock and clock[0][0] <= when:
            poke.add(heapq.heappop(clock)[1])

        want = []
        for level in poke:
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
                due = here - spent < MINB and value - spent >= MINB
                if value - here >= THR or due:
                    want.append((level, "grant", value))
            elif value < here:
                want.append((level, "pull", value))
        for level, kind, value in sorted(set(want)):
            seat[level] = value
            told_at[level].append(when)
            told_of[level].append(value)
            rows.append((kind, when, level, value))

    left = dict((fd, sum(park[fd])) for fd in sorted(shut) if shut[fd] is None)
    return [list(r) for r in rows], left
