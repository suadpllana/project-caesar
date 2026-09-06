from hst import bd, ld, od, rt, sc
from hst.reg import Hs


def go(name, path, rows):
    pks, evs = sc.rd(path)
    h = Hs(pks)
    i = 0
    for e in evs:
        i += 1
        if e[0] == "ld":
            made = ld.ld(h, e[1], e[2])
            rows.append("%s %d ld %s %s" % (name, i, e[1], " ".join(str(n) for n in made) if made else "-"))
        elif e[0] == "us":
            r = h.sr(e[1])
            if r is None:
                rows.append("%s %d us %s %s off" % (name, i, e[1], e[2][0]))
            else:
                for nm in e[2]:
                    k, v = bd.us(h, r, nm)
                    if k != "res":
                        rows.append("%s %d us %s %s %s" % (name, i, r.p.nm, nm, k))
                        break
                    rows.append("%s %d us %s %s %d" % (name, i, r.p.nm, nm, v))
                    nxt = h.rs.get(v)
                    if nxt is None:
                        break
                    r = nxt
        else:
            n = od.dp(h, e[1])
            rows.append("%s %d dp %s %s" % (name, i, e[1], n if n else "bad"))
        keep = rt.kp(h)
        gone = [n for n in h.rs if n not in keep]
        for n in gone:
            del h.rs[n]
        rows.append("%s %d rl %s" % (name, i, " ".join(str(n) for n in od.od(gone)) if gone else "-"))
