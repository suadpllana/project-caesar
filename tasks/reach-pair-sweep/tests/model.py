"""Independent model of the whole runtime, written from the frozen contract.

It shares no code with `environment/app_src`: its own heap, its own op loop, its own collector.
Agreement is therefore between two readings of the contract rather than between two callers of
one function.

Where the independence sits, stated precisely. Both sides index the pair table by key, because
the graded set contains programs where rescanning it cannot finish in the time allowed, so that
axis is closed to both and is not evidence of anything. What differs is everything else: this
walks breadth-first from a deque where the reference walks depth-first from a stack, it carries
membership in one colour dict painted twice where the reference makes two calls with a blocked
set, and it applies the nursery restriction on entry rather than inside the loop. Traversal
order, state shape and where the space test sits are the axes a shared misreading would have to
survive.

Colours: 1 is reached by the collection, 2 is kept only so a queued finalizer can run. Painting 2
never overwrites 1, which is what keeps weak clearing and promotion answering to colour 1 alone.
"""
import collections

NURSERY = "n"
OLD = "o"
PROMOTE_AGE = 2


def _blank():
    return {"objs": {}, "frames": [{}], "globs": {}, "handles": [], "pairs": [],
            "weak": {}, "queue": [], "done": set(), "rset": set()}


def _obj(fin):
    return {"flds": {}, "fin": fin, "space": NURSERY, "age": 0, "pins": 0}


def _index(pairs):
    by = {}
    for k, v in pairs:
        by.setdefault(k, []).append(v)
    return by


def _named(st):
    out = []
    for fr in st["frames"]:
        out.extend(v for v in fr.values() if v is not None and v in st["objs"])
    out.extend(v for v in st["globs"].values() if v is not None and v in st["objs"])
    out.extend(v for v in st["handles"] if v in st["objs"])
    return out


def _roots(st, full):
    objs = st["objs"]
    if full:
        return sorted(set(_named(st)))
    out = [i for i in _named(st) if objs[i]["space"] == NURSERY]
    for src, fld, was in sorted(st["rset"]):
        if src not in objs:
            continue
        val = objs[src]["flds"].get(fld)
        if val is not None and val in objs and objs[val]["space"] == NURSERY:
            out.append(val)
    return sorted(set(out))


def _paint(st, by, seed, shade, col, full):
    objs = st["objs"]
    q = collections.deque()

    def offer(i):
        if i not in objs or col.get(i):
            return
        if not full and objs[i]["space"] == OLD:
            return
        q.append(i)

    for i in seed:
        offer(i)
    if not full:
        # An old key is live for the whole of a minor collection, so its pair is ready before
        # the walk starts and stays ready; the key itself never joins the set.
        for k, vs in by.items():
            if k in objs and objs[k]["space"] == OLD:
                for v in vs:
                    offer(v)
    while q:
        i = q.popleft()
        if col.get(i):
            continue
        col[i] = shade
        for v in objs[i]["flds"].values():
            if v is not None:
                offer(v)
        for v in by.get(i, ()):
            offer(v)


def _collect(st, full, out):
    objs = st["objs"]
    by = _index(st["pairs"])
    col = {}
    _paint(st, by, _roots(st, full), 1, col, full)

    def scope():
        return [i for i in sorted(objs) if full or objs[i]["space"] == NURSERY]

    fresh = [i for i in scope()
             if col.get(i) != 1 and objs[i]["fin"] is not None
             and i not in st["done"] and i not in st["queue"]]

    start = [i for i in st["queue"] if i in objs] + fresh
    if not full:
        start = [i for i in start if objs[i]["space"] == NURSERY]
    _paint(st, by, start, 2, col, full)

    for name in sorted(st["weak"]):
        w = st["weak"][name]
        if w[1]:
            continue
        tgt = w[0]
        if not full and (tgt not in objs or objs[tgt]["space"] != NURSERY):
            continue
        if col.get(tgt) != 1:
            w[1] = True
            out.append("clr " + name)

    for i in sorted(fresh):
        st["queue"].append(i)
        out.append("fin %d" % i)

    gone = [i for i in scope() if not col.get(i)]
    for i in gone:
        del objs[i]
        out.append("rel %d" % i)
    if gone:
        dead = set(gone)
        st["rset"] = {e for e in st["rset"] if e[0] not in dead}
        st["pairs"] = [(k, v) for k, v in st["pairs"] if k not in dead and v not in dead]

    for i in sorted(objs):
        o = objs[i]
        if o["space"] != NURSERY or col.get(i) != 1:
            continue
        o["age"] += 1
        if o["age"] >= PROMOTE_AGE and o["pins"] == 0:
            o["space"] = OLD
            out.append("pro %d" % i)


def _runfin(st, out):
    if not st["queue"]:
        return
    i = st["queue"].pop(0)
    z = st["objs"][i]["fin"] if i in st["objs"] else None
    if z:
        st["frames"][0][z] = i
    st["done"].add(i)
    out.append("ran %d" % i)


def _num(s):
    return None if s == "-" else int(s)


def _run(ops):
    st = _blank()
    out = []
    for op in ops:
        k = op[0]
        if k == "new":
            fin = None if len(op) == 2 else ("" if len(op) == 3 else op[3])
            st["objs"][int(op[1])] = _obj(fin)
        elif k == "set":
            src, fld, val = int(op[1]), op[2], _num(op[3])
            st["objs"][src]["flds"][fld] = val
            if (st["objs"][src]["space"] == OLD and val is not None and val in st["objs"]
                    and st["objs"][val]["space"] == NURSERY):
                st["rset"].add((src, fld, val))
        elif k == "slot":
            st["frames"][-1][op[1]] = _num(op[2])
        elif k == "glob":
            st["globs"][op[1]] = _num(op[2])
        elif k == "push":
            st["frames"].append({})
        elif k == "pop":
            st["frames"].pop()
        elif k == "hold":
            st["handles"].append(int(op[1]))
        elif k == "drop":
            if st["handles"]:
                st["handles"].pop()
        elif k == "pin":
            st["objs"][int(op[1])]["pins"] += 1
        elif k == "unpin":
            o = st["objs"][int(op[1])]
            if o["pins"]:
                o["pins"] -= 1
        elif k == "weak":
            st["weak"][op[1]] = [int(op[2]), False]
        elif k == "pair":
            st["pairs"].append((int(op[1]), int(op[2])))
        elif k == "collect":
            _collect(st, False, out)
        elif k == "collectfull":
            _collect(st, True, out)
        elif k == "runfin":
            _runfin(st, out)
        else:
            raise ValueError(k)
    return out, st


def expect(ops):
    return _run(ops)[0]


def alive(ops):
    return sorted(_run(ops)[1]["objs"])
