from bm import halt
from bm import keep
from bm import pick
from bm import rep
from bm import sc
from bm import say


def one(sp, name, prompt):
    out = [say.ask(name)]
    tab = sc.Table(sp.rows)
    lent = rep.Lent()
    pool = keep.Pool(sp.h)
    g = tab.top()
    beams = [(0, rep.root(prompt, sp.n))]
    step = 0
    while True:
        step += 1
        cands = []
        for slot, (raw, path) in enumerate(beams):
            for tok, add in tab.out(path.last):
                span = path.span(tok)
                if span is not None and (path.holds(span) or lent.has(span)):
                    continue
                cands.append((raw + add, slot, tok, path))
        took = pick.take(cands, sp.w)
        for raw, path in beams:
            if path.length < sp.s:
                continue
            add = tab.stop(path.last)
            if add is None:
                continue
            ln = path.length
            fin = raw - sp.p * ln
            one_hyp, went = pool.put(fin, ln, path)
            out.append(say.shut(step, ln, fin))
            lent.take(path)
            for old in went:
                out.append(say.gone(step, old.ln, old.fin))
                lent.give(old.path)
        beams = [(cand[0], cand[3].plus(cand[2])) for cand in took]
        best = max((cand[0] for cand in took), default=0)
        why = halt.why(step, sp.t, took, pool, best, sp.p, g)
        if why is not None:
            out.append(say.halt(step, why))
            break
    for rank, one_hyp in enumerate(pool.listing()):
        out.append(say.hyp(rank, one_hyp.fin, one_hyp.ln, one_hyp.path.tokens()))
    return out
