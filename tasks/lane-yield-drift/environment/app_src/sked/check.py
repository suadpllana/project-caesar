def bad(what):
    raise ValueError(what)


def zones(plan):
    for z in plan.zones.values():
        last = None
        for at, _ in z.shifts:
            if at < 1:
                bad("shift at %d" % at)
            if last is not None and at <= last:
                bad("shift order %s" % z.name)
            last = at


def pools(plan):
    for p in plan.pools.values():
        if p.cap < 1:
            bad("cap %s" % p.name)


def jobs(plan):
    seen = set()
    for j in plan.jobs:
        if j.prio in seen:
            bad("priority %d" % j.prio)
        seen.add(j.prio)
        if j.mode not in ("clock", "follow"):
            bad("mode %s" % j.mode)
        if not 0 <= j.opn < j.shut <= 1440:
            bad("window %s" % j.jid)
        if j.shut - j.opn > 1320:
            bad("window span %s" % j.jid)
        if j.dur < 1:
            bad("duration %s" % j.jid)
        if j.step < 1:
            bad("step %s" % j.jid)
        if j.mode == "follow" and j.step <= j.dur:
            bad("follow step %s" % j.jid)
        if j.anchor < 0:
            bad("anchor %s" % j.jid)
        top = max([j.zone.base] + [o for _, o in j.zone.shifts])
        if j.anchor < top:
            bad("anchor before the epoch %s" % j.jid)


def plan(p):
    if p.horizon < 1:
        bad("horizon")
    if not p.jobs:
        bad("jobs")
    zones(p)
    pools(p)
    jobs(p)
    return p
