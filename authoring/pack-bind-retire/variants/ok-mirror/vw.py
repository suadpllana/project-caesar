def build(h, p):
    seq = []
    seen = set()
    q = list(p.nd)
    while q:
        nm = q.pop(0)
        r = h.sr(nm)
        if r is None or r.n in seen:
            continue
        seen.add(r.n)
        seq.append(r.n)
        q.extend(r.p.nd)
    return seq


def chain(h, r):
    seq = [r.n]
    seen = {r.n}
    for n in r.zz:
        if n in h.rs and n not in seen:
            seen.add(n)
            seq.append(n)
    for n in h.op:
        if n in h.rs and n not in seen:
            seen.add(n)
            seq.append(n)
    return seq


def pick(h, r, nm):
    for n in chain(h, r):
        if nm in h.rs[n].p.pv:
            return n
    return 0
