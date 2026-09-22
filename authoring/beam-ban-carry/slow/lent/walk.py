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
    out = [say.ask(name)]
    live = [(0, rep.root(prompt, sp.n))]
    step = 0
    while True:
        step += 1
        for raw, path in live:
            if path.length >= sp.s:
                add = tab.stop(path.last)
                if add is not None:
                    ln = path.length
                    fin = raw + add - sp.p * ln
                    out.append(say.shut(step, ln, fin))
                    for old in pool.put(fin, ln, path):
                        out.append(say.gone(step, old[1], old[0]))
                    lent.reset(pool.paths(), sp.n)
        cands = []
        for slot, (raw, path) in enumerate(live):
            for tok, add in tab.out(path.last):
                span = path.span(sp.n, tok)
                if span is not None and (span in path.held or lent.has(span)):
                    continue
                cands.append((raw + add, slot, tok, path))
        took = pick.take(cands, sp.w)
        best = max([c[0] for c in took] or [0])
        stop = halt.why(step, sp.t, took, pool, best, sp.p, tab.top())
        if stop is not None:
            out.append(say.halt(step, stop))
            break
        live = [(c[0], c[3].grow(sp.n, c[2])) for c in took]
    for rank, one_hyp in enumerate(pool.listing()):
        out.append(say.hyp(rank, one_hyp[0], one_hyp[1], one_hyp[3].tokens()))
    return out
