from bm import halt
from bm import keep
from bm import pick
from bm import rep
from bm import sc
from bm import say


def one(sp, name, prompt):
    tab = sc.Table(sp.rows)
    lent = rep.Lent()
    pool = keep.Pool(sp.h)
    lines = [say.ask(name)]
    live = [(0, rep.root(prompt, sp.n))]
    step = 0
    while True:
        step += 1
        hit = False
        for raw, path in live:
            if path.length < sp.s:
                continue
            add = tab.stop(path.last)
            if add is None:
                continue
            ln = path.length
            fin = raw + add - sp.p * ln
            lines.append(say.shut(step, ln, fin))
            hit = True
            for old in pool.put(fin, ln, path):
                lines.append(say.gone(step, old[1], -old[0]))
        if hit:
            lent.reset(pool.held())
        cands = []
        for slot, (raw, path) in enumerate(live):
            for tok, add in tab.out(path.last):
                span = rep.span_of(path, sp.n, tok)
                if span is not None and (span in path.held or lent.has(span)):
                    continue
                cands.append((raw + add, slot, tok, path))
        took = pick.take(cands, sp.w)
        best = 0
        for cand in took:
            best = max(best, cand[0])
        stop = halt.why(step, sp.t, took, pool, best, sp.p, tab.top())
        if stop is not None:
            lines.append(say.halt(step, stop))
            break
        live = [(cand[0], rep.grow(cand[3], sp.n, cand[2])) for cand in took]
    for rank, row in enumerate(pool.listing()):
        lines.append(say.hyp(rank, row[0], row[1], row[2].tokens()))
    return lines
