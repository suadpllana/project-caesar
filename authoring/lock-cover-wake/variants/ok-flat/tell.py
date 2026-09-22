from . import log, read


def key(res):
    tbl, row = read.split_res(res)
    return (tbl, row)


def report(eng):
    lines = []
    for tid in eng.order:
        t = eng.txns[tid]
        pairs = []
        for res, m in t.held.items():
            pairs.append((res, m))
        lines.append(log.tx(tid, t.state, pairs))
    waiting = [res for res, e in eng.ents.items() if e.waiting()]
    for res in sorted(waiting, key=key):
        e = eng.ents[res]
        lines.append(log.q(res, [(it.tid, it.m) for it in e.queued()]))
    lines.append(log.cov(eng.cov))
    return lines
