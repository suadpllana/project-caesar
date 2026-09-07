from col import age, keep, plan, scan, wipe
from mem import heap, rset, tables


def _v(s):
    return None if s == "-" else int(s)


def _ser(h, i):
    o = h.objs.get(i)
    return o.ser if o is not None else 0


def collect(h, full, out):
    seen = scan.reach(h, plan.roots(h, full), full, frozenset())
    fresh, held = keep.settle(h, seen, full)

    for n in sorted(wipe.wipe(h, seen, full)):
        out.append("clr " + n)

    for i in sorted(fresh):
        h.queue.append(i)
        out.append("fin %d" % i)

    gone = sorted(wipe.release(h, seen, held, full))
    for i in gone:
        del h.objs[i]
        out.append("rel %d" % i)
    rset.forget(h, set(gone))
    h.young.difference_update(gone)

    for i in sorted(age.promote(h, seen, held)):
        out.append("pro %d" % i)


def ex(h, op, out):
    k = op[0]
    if k == "new":
        if len(op) == 2:
            z = None
        elif len(op) == 3:
            z = ""
        else:
            z = op[3]
        i = int(op[1])
        h.stamp += 1
        h.objs[i] = heap.Obj(z, h.stamp)
        h.young.add(i)
    elif k == "set":
        src, fld, val = int(op[1]), op[2], _v(op[3])
        h.objs[src].flds[fld] = val
        rset.note(h, src, fld, val)
    elif k == "slot":
        h.frames[-1][op[1]] = _v(op[2])
    elif k == "glob":
        h.globs[op[1]] = _v(op[2])
    elif k == "push":
        h.frames.append({})
    elif k == "pop":
        h.frames.pop()
    elif k == "hold":
        h.handles.append(int(op[1]))
    elif k == "drop":
        if h.handles:
            h.handles.pop()
    elif k == "pin":
        h.objs[int(op[1])].pins += 1
    elif k == "unpin":
        o = h.objs[int(op[1])]
        if o.pins:
            o.pins -= 1
    elif k == "weak":
        h.weak[op[1]] = tables.Ref(int(op[2]))
    elif k == "pair":
        a = int(op[1])
        h.pairs.append(tables.Pair(a, _ser(h, a), int(op[2])))
    elif k == "collect":
        collect(h, False, out)
    elif k == "collectfull":
        collect(h, True, out)
    elif k == "runfin":
        if h.queue:
            i = h.queue.pop(0)
            o = h.objs.get(i)
            z = o.fin if o is not None else None
            if z:
                h.frames[0][z] = i
            if o is not None:
                h.done.add(o.ser)
            out.append("ran %d" % i)
    else:
        raise ValueError(k)
