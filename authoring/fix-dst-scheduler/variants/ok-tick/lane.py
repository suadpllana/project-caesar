from . import due, gate, rec, zt

CLOCK = "clock"


def fresh(plan):
    st = {"jobs": list(plan.jobs), "led": gate.Ledger(), "evs": [], "busy": None,
          "until": None, "hold": {}, "seq": {}, "nxt": {}, "stop": plan.horizon}
    for j in plan.jobs:
        st["hold"][j.jid] = None
        st["seq"][j.jid] = 0
        st["nxt"][j.jid] = due.nom_at(j, 0, None)
    return st


def narrow(st, jobs, stop):
    return {"jobs": jobs, "led": st["led"].copy(), "evs": [], "busy": None, "until": None,
            "hold": {j.jid: st["hold"][j.jid] for j in jobs},
            "seq": {j.jid: st["seq"][j.jid] for j in jobs},
            "nxt": {j.jid: st["nxt"][j.jid] for j in jobs}, "stop": stop}


def bump(st, j, prev):
    if j.mode == CLOCK:
        st["nxt"][j.jid] = due.nom_at(j, st["seq"][j.jid], None)
    elif prev is None:
        st["nxt"][j.jid] = None
    else:
        st["nxt"][j.jid] = due.nom_at(j, st["seq"][j.jid], prev)


def agenda(st, cur):
    pool = []
    if st["busy"] is not None:
        pool.append(st["until"])
    for j in st["jobs"]:
        if st["nxt"][j.jid] is not None:
            pool.append(st["nxt"][j.jid])
        o = st["hold"][j.jid]
        if o is None:
            continue
        pool.append(o.dead)
        if st["busy"] is None and not st["led"].room(j, cur):
            pool.append(zt.next_day(j.pool.zone, cur))
    return [t for t in pool if t > cur]


def in_the_way(st, j, t):
    upper = [h for h in st["jobs"] if h.prio < j.prio]
    if not upper:
        return False
    sub = narrow(st, upper, t + j.dur)
    pick(sub, t)
    cur = t
    while sub["busy"] is None:
        pool = agenda(sub, cur)
        if not pool:
            break
        cur = min(pool)
        if cur >= sub["stop"]:
            break
        tick(sub, cur)
    return any(e.kind == "start" for e in sub["evs"])


def pick(st, now):
    if st["busy"] is not None:
        return
    for j in st["jobs"]:
        o = st["hold"][j.jid]
        if o is None or not st["led"].room(j, now):
            continue
        if in_the_way(st, j, now):
            continue
        st["evs"].append(rec.Ev("start", j, o.k, now))
        st["led"].take(j, now)
        st["hold"][j.jid] = None
        st["busy"] = o
        st["until"] = now + j.dur
        bump(st, j, now)
        return


def tick(st, now):
    if st["busy"] is not None and st["until"] == now:
        st["evs"].append(rec.Ev("end", st["busy"].job, st["busy"].k, now))
        st["busy"] = None
        st["until"] = None
    for j in st["jobs"]:
        while st["nxt"][j.jid] is not None and st["nxt"][j.jid] <= now:
            k = st["seq"][j.jid]
            held = st["hold"][j.jid] is not None or (
                st["busy"] is not None and st["busy"].job is j)
            st["seq"][j.jid] = k + 1
            if held:
                st["evs"].append(rec.Ev("skip", j, k, now))
            else:
                o = rec.Occ(j, k, st["nxt"][j.jid])
                o.dead = gate.dead_at(j, o.nom, st["stop"] + 4320)
                st["hold"][j.jid] = o
            bump(st, j, None)
    for j in st["jobs"]:
        o = st["hold"][j.jid]
        if o is not None and o.dead <= now:
            st["evs"].append(rec.Ev("drop", j, o.k, o.dead))
            st["hold"][j.jid] = None
            bump(st, j, o.dead)
    pick(st, now)


def run(plan):
    gate.SPANS.clear()
    st = fresh(plan)
    cur = -1
    while True:
        pool = agenda(st, cur)
        if not pool:
            break
        now = min(pool)
        if now >= st["stop"]:
            break
        tick(st, now)
        cur = now
    return st["evs"]
