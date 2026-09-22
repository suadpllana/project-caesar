from . import log, read


def report(eng):
    out = []
    for tid in eng.order:
        t = eng.txns[tid]
        out.append(log.tx(tid, t.state, list(t.held.items())))
    for res in sorted(eng.ents, key=read.split_res):
        e = eng.ents[res]
        if e.waiting():
            out.append(log.q(res, [(it.tid, it.m) for it in e.queued()]))
    out.append(log.cov(eng.cov))
    return out
