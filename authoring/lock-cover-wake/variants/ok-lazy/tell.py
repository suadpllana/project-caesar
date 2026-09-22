from . import log, read


def report(eng):
    out = []
    for tid in eng.order:
        t = eng.txns[tid]
        out.append(log.tx(tid, t.state, [(r, t.held[r]) for r in t.held]))
    rest = [(read.split_res(res), res) for res, e in eng.ents.items() if e.waiting()]
    rest.sort()
    for _k, res in rest:
        out.append(log.q(res, [(it.tid, it.m) for it in eng.ents[res].queued()]))
    out.append(log.cov(eng.cov))
    return out
