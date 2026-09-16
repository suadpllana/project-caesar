from . import due, gate, rec, zt


def run(plan):
    gate.SPANS.clear()
    led = gate.Ledger()
    evs = []
    jobs = plan.jobs
    hold = {j.jid: None for j in jobs}
    seq = {j.jid: 0 for j in jobs}
    nxt = {j.jid: due.nom_at(j, 0, None) for j in jobs}
    busy = [None, None]
    cur = -1

    def bump(j, prev):
        if j.mode == "clock":
            nxt[j.jid] = due.nom_at(j, seq[j.jid], None)
        elif prev is None:
            nxt[j.jid] = None
        else:
            nxt[j.jid] = due.nom_at(j, seq[j.jid], prev)

    while True:
        pool = []
        if busy[0] is not None:
            pool.append(busy[1])
        for j in jobs:
            if nxt[j.jid] is not None:
                pool.append(nxt[j.jid])
            o = hold[j.jid]
            if o is None:
                continue
            pool.append(o.dead)
            if busy[0] is None and not led.room(j, cur):
                pool.append(zt.next_day(j.pool.zone, cur))
        pool = [t for t in pool if t > cur]
        if not pool:
            break
        now = min(pool)
        if now >= plan.horizon:
            break

        if busy[0] is not None and busy[1] == now:
            evs.append(rec.Ev("end", busy[0].job, busy[0].k, now))
            busy[0] = None
            busy[1] = None

        for j in jobs:
            while nxt[j.jid] is not None and nxt[j.jid] <= now:
                k = seq[j.jid]
                held = hold[j.jid] is not None or (
                    busy[0] is not None and busy[0].job is j)
                seq[j.jid] = k + 1
                if held:
                    evs.append(rec.Ev("skip", j, k, now))
                else:
                    o = rec.Occ(j, k, nxt[j.jid])
                    o.dead = gate.dead_at(j, o.nom, plan.horizon)
                    hold[j.jid] = o
                bump(j, None)

        for j in jobs:
            o = hold[j.jid]
            if o is not None and o.dead <= now:
                evs.append(rec.Ev("drop", j, o.k, o.dead))
                hold[j.jid] = None
                bump(j, o.dead)

        if busy[0] is None:
            for j in jobs:
                o = hold[j.jid]
                if o is None or not led.room(j, now):
                    continue
                evs.append(rec.Ev("start", j, o.k, now))
                led.take(j, now)
                hold[j.jid] = None
                busy[0] = o
                busy[1] = now + j.dur
                bump(j, now)
                break
        cur = now
    return evs
