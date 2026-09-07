"""Correct variant: settle first, then decide what counted as a recomputation.

The rule says a cell is recomputed when one of the values it read is not where that cell
ends up. That is a statement about the settled sheet, not about the order anything was
visited in, so this variant does the opposite of the reference: it keeps every record as
it stood before the edit, brings the affected cells up to date in whatever order the
worklist hands them over - which may recompute a cell on a value that later moves back -
and then reports exactly the cells whose old record disagrees with the settled sheet.

It does more work than the reference and lands on the same answer, which is the point of
having it: the contract is the rule, not one way of obeying it.
"""

from sheet import upd


def edit(eng, ad, hit):
    if not hit:
        return
    pend = set(eng.dp.readers(ad))
    eng.dp.drop(ad)
    # After the drop, so the edited cell has no record to agree with and always counts.
    kept = dict(eng.dp.rec)
    if eng.st.node(ad) is None:
        for t in release(eng, ad):
            pend.update(eng.dp.readers(t))
    else:
        pend.add(ad)
    settle(eng, pend)
    # Anything whose old record disagrees with the settled sheet was visited at least
    # once on the way here, so the over-computed set is where the answer hides.
    visited = sorted(set(eng.seen))
    del eng.seen[:]
    for cell in visited:
        if moved(eng, kept.get(cell)):
            eng.seen.append(cell)


def release(eng, ad):
    st = eng.st
    held = list(eng.ly.fp.get(ad, ()))
    was = dict((t, st.val(t)) for t in held)
    eng.ly.wipe(st, ad)
    return [t for t in held if st.val(t) != was[t]]


def moved(eng, rec):
    if rec is None:
        return True
    st = eng.st
    for k, t, was in rec:
        now = st.own(t) if k == "o" else st.val(t)
        if now != was:
            return True
    return False


def settle(eng, pend):
    for _ in range(64):
        if not pend:
            return
        wave = sorted(pend)
        pend = set()
        for ad in wave:
            if eng.st.node(ad) is None or not eng.dp.stale(eng.st, ad):
                continue
            for t in upd.one(eng, ad):
                pend.update(eng.dp.readers(t))
    raise RuntimeError("the sheet did not settle")
