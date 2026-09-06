"""Independent model of the whole runtime, written from the frozen contract.

This file deliberately shares no code with `environment/app_src`. It reimplements the heap, the
op loop and the collector, so agreement is between two readings of the contract rather than
between two callers of one function.

Where the independence sits, stated precisely, because it is narrower than it once was. Both
sides index the pair table by key: the graded set contains programs where rescanning it cannot
finish in the time allowed, so that axis is closed to both and is not evidence of anything. What
differs is everything else - this walks breadth-first from a deque where the reference walks
depth-first from a stack, and it separates the two retained sets by painting one colour dict
twice where the reference makes two calls with a blocked set. Traversal order and state shape are
the axes a shared misreading would have to survive.

Colours: 1 is reached from the open frames, 2 is kept only so a queued finalizer can run.
Uncoloured objects are released. Painting 2 cannot overwrite 1, which is what keeps weak
clearing and the finalizable set answering to colour 1 alone.
"""
import collections


def _index(pairs):
    by = {}
    for k, v in pairs:
        by.setdefault(k, []).append(v)
    return by


def _paint(obj, bykey, seed, colour, col):
    work = collections.deque(seed)
    while work:
        i = work.popleft()
        if i not in obj or col.get(i):
            continue
        col[i] = colour
        for v in obj[i]["fl"].values():
            if v is not None and v in obj and not col.get(v):
                work.append(v)
        for v in bykey.get(i, ()):
            if v in obj and not col.get(v):
                work.append(v)


def _collect(st, out):
    obj, bykey = st["obj"], _index(st["pairs"])
    col = {}

    roots = set()
    for fr in st["frames"]:
        for v in fr.values():
            if v is not None and v in obj:
                roots.add(v)
    _paint(obj, bykey, roots, 1, col)

    # cleared against colour 1 only: being kept for a finalizer is not being reached
    for name in sorted(st["weak"]):
        w = st["weak"][name]
        if not w[1] and col.get(w[0]) != 1:
            w[1] = True
            out.append("clr " + name)

    # the queue is settled before any keeping is granted, so colour 2 does not exist yet
    fresh = sorted(i for i in obj
                   if col.get(i) != 1 and obj[i]["fz"] is not None
                   and i not in st["ran"] and i not in st["queue"])
    for i in fresh:
        st["queue"].append(i)
        out.append("fin %d" % i)

    _paint(obj, bykey, set(st["queue"]), 2, col)

    for i in sorted(obj):
        if not col.get(i):
            out.append("rel %d" % i)
    for i in [i for i in obj if not col.get(i)]:
        del obj[i]


def _runfin(st, out):
    if not st["queue"]:
        return
    i = st["queue"].pop(0)
    z = st["obj"][i]["fz"] if i in st["obj"] else None
    if z:
        st["frames"][0][z] = i
    st["ran"].add(i)
    out.append("ran %d" % i)


def _run(ops):
    st = {"obj": {}, "frames": [{}], "weak": {}, "pairs": [], "queue": [], "ran": set()}
    out = []
    for op in ops:
        k = op[0]
        if k == "new":
            if len(op) == 2:
                z = None
            elif len(op) == 3:
                z = ""
            else:
                z = op[3]
            st["obj"][int(op[1])] = {"fl": {}, "fz": z}
        elif k == "set":
            st["obj"][int(op[1])]["fl"][op[2]] = None if op[3] == "-" else int(op[3])
        elif k == "slot":
            st["frames"][-1][op[1]] = None if op[2] == "-" else int(op[2])
        elif k == "push":
            st["frames"].append({})
        elif k == "pop":
            st["frames"].pop()
        elif k == "weak":
            st["weak"][op[1]] = [int(op[2]), False]
        elif k == "pair":
            st["pairs"].append((int(op[1]), int(op[2])))
        elif k == "collect":
            _collect(st, out)
        elif k == "runfin":
            _runfin(st, out)
        else:
            raise ValueError(k)
    return out, st


def expect(ops):
    return _run(ops)[0]


def alive(ops):
    return sorted(_run(ops)[1]["obj"])
