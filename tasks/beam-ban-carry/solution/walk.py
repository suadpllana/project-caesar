from bm import halt
from bm import keep
from bm import pick
from bm import rep
from bm import sc
from bm import say


def one(sp, name, prompt):
    out = [say.ask(name)]
    tab = sc.Table(sp.rows)
    book = rep.Book(sp.n)
    lent = rep.Lent()
    pool = keep.Pool(sp.h)
    g = tab.top()
    beams = [(0, rep.root(book, prompt))]
    step = 0
    while True:
        step += 1
        # Every beam that may stop does so, in slot order, before anything else of this step.
        moved = False
        for raw, path in beams:
            if path.length < sp.s:
                continue
            add = tab.stop(path.last)
            if add is None:
                continue
            ln = path.length
            fin = raw + add - sp.p * ln
            _new, went = pool.put(fin, ln, path)
            out.append(say.shut(step, ln, fin))
            moved = True
            for old in went:
                out.append(say.gone(step, old.ln, old.fin))
        if moved:
            lent.reset(pool.masks())
        # A continuation is refused by the beam's own sequence or by a span the set lends.
        cands = []
        for slot, (raw, path) in enumerate(beams):
            for tok, add in tab.out(path.last):
                bit = rep.reach(book, path, tok)
                if bit >= 0 and (path.holds(bit) or lent.has(bit)):
                    continue
                cands.append((raw + add, slot, tok, path))
        took = pick.take(cands, sp.w)
        best = max((cand[0] for cand in took), default=0)
        reason = halt.why(step, sp.t, took, pool, best, sp.p, g)
        if reason is not None:
            out.append(say.halt(step, reason))
            break
        beams = [(cand[0], rep.grow(book, cand[3], cand[2])) for cand in took]
    for rank, one_hyp in enumerate(pool.listing()):
        out.append(say.hyp(rank, one_hyp.fin, one_hyp.ln, one_hyp.path.tokens()))
    return out
