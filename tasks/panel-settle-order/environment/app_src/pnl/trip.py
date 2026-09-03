def due(pl, net, ph, rno, g, moved):
    if ph != "run":
        return ()
    seen = pl.setdefault("tr", set())
    out = []
    for nm, tgt, wr in net.lat:
        if tgt == g and (rno, nm) not in seen:
            seen.add((rno, nm))
            out.append(nm)
    return tuple(out)


def sched(pl, net, fired):
    out = []
    for nm in fired:
        for lnm, tgt, wr in net.lat:
            if lnm == nm:
                out.extend(wr)
    return tuple(out)
