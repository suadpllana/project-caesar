from cyc import keep
from rt import hp


def _v(s):
    return None if s == "-" else int(s)


def ex(h, op, out):
    k = op[0]
    if k == "new":
        if len(op) == 2:
            z = None
        elif len(op) == 3:
            z = ""
        else:
            z = op[3]
        h.ob[int(op[1])] = hp.Ob(z)
    elif k == "set":
        h.ob[int(op[1])].fl[op[2]] = _v(op[3])
    elif k == "slot":
        h.fr[-1][op[1]] = _v(op[2])
    elif k == "push":
        h.fr.append({})
    elif k == "pop":
        h.fr.pop()
    elif k == "weak":
        h.wk[op[1]] = hp.Wk(int(op[2]))
    elif k == "pair":
        h.pr.append((int(op[1]), int(op[2])))
    elif k == "collect":
        cl, qd, rl = keep.cycle(h)
        for n in sorted(cl):
            h.wk[n].c = True
            out.append("clr " + n)
        for i in sorted(qd):
            h.qu.append(i)
            out.append("fin %d" % i)
        for i in sorted(rl):
            h.ob.pop(i, None)
            out.append("rel %d" % i)
    elif k == "runfin":
        if h.qu:
            i = h.qu.pop(0)
            z = h.ob[i].fz if i in h.ob else None
            if z:
                h.fr[0][z] = i
            h.rn.add(i)
            out.append("ran %d" % i)
    else:
        raise ValueError(k)
