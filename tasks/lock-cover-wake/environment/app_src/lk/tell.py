from . import log


def report(eng):
    out = []
    for tid in eng.order:
        t = eng.txns[tid]
        state = t.state if t.state in ("cut", "done") else "run"
        out.append(log.tx(tid, state, sorted(t.held.items())))
    for res in sorted(eng.ents):
        e = eng.ents[res]
        if e.waiting():
            out.append(log.q(res, [(it.tid, it.m) for it in e.queued()]))
    out.append(log.cov(eng.cov))
    return out
