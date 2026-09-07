"""Independent model of the whole runtime, written from the frozen contract.

It shares no code with `environment/app_src`: its own heap, its own op loop, its own collector.
Agreement is therefore between two readings of the contract rather than between two callers of
one function.

Where the independence sits, stated precisely. Three axes are closed to both sides because the
graded set contains programs that neither could otherwise finish in the time allowed, so
agreement on them is not evidence of anything: both index the pair table by key, both keep the
nursery as a set rather than filtering the whole heap, and both drop remembered-set entries whose
field has stopped naming a nursery object. What differs is everything else: this walks
breadth-first from a deque where the reference walks depth-first from a stack, it carries
membership in one colour dict painted twice where the reference makes two calls with a blocked
set, it applies the nursery restriction on entry rather than inside the loop, and it holds every
object as a plain dict rather than a slotted class. Traversal order, state shape and where the
space test sits are the axes a shared misreading would have to survive.

Colours: 1 is reached by the collection, 2 is kept only so a queued finalizer can run. Painting 2
never overwrites 1, which is what keeps weak clearing and promotion answering to colour 1 alone.

A number is not an object. `new` hands out a serial that never repeats, and every record the
runtime keeps of an object that may outlive it carries that serial: the finished-finalizer set,
and the key of every pair table row. A record whose serial no longer matches the object now
standing at that number is about an object that is gone, and says nothing about the one there
now. A row's value end carries no serial because it needs none - a value cannot be released while
the object at its key survives, so a freed value number always comes with a freed key number.
"""
import collections

NURSERY = "n"
OLD = "o"
PROMOTE_AGE = 2


def _blank():
    return {"objs": {}, "frames": [{}], "globs": {}, "handles": [], "pairs": [],
            "weak": {}, "queue": [], "done": set(), "rset": set(), "young": set(),
            "stamp": 0}


def _obj(fin, ser):
    return {"flds": {}, "fin": fin, "space": NURSERY, "age": 0, "pins": 0, "ser": ser}


def _index(st):
    """Pair rows keyed by key id, skipping every row whose key number has been handed out again."""
    objs = st["objs"]
    by = {}
    for key, kser, val in st["pairs"]:
        k = objs.get(key)
        if k is None or k["ser"] != kser:
            continue
        by.setdefault(key, []).append(val)
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
    # Collapse to one entry per field first: the recorded value is never the answer, so entries
    # sharing a source and a field ask the same question and only one of them need be kept.
    fields = {}
    for entry in st["rset"]:
        fields.setdefault((entry[0], entry[1]), entry)
    keep = set()
    for (src, fld), entry in fields.items():
        owner = objs.get(src)
        now = owner["flds"].get(fld) if owner is not None else None
        target = objs.get(now) if now is not None else None
        # An entry whose field has stopped naming a nursery object cannot become interesting
        # again by itself: a later store that would make it so re-records through the barrier.
        if target is not None and target["space"] == NURSERY:
            out.append(now)
            keep.add(entry)
    st["rset"] = keep
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
            if objs[k]["space"] == OLD:
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
    by = _index(st)
    col = {}
    _paint(st, by, _roots(st, full), 1, col, full)

    scope = sorted(objs) if full else sorted(st["young"])

    queued = set(st["queue"])
    fresh = [i for i in scope
             if col.get(i) != 1 and objs[i]["fin"] is not None
             and objs[i]["ser"] not in st["done"] and i not in queued]

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

    gone = [i for i in scope if not col.get(i)]
    for i in gone:
        del objs[i]
        out.append("rel %d" % i)
    if gone:
        dead = set(gone)
        st["rset"] = {e for e in st["rset"] if e[0] not in dead}
        st["young"] -= dead

    for i in sorted(st["young"]):
        o = objs[i]
        if col.get(i) != 1:
            continue
        o["age"] += 1
        if o["age"] >= PROMOTE_AGE and o["pins"] == 0:
            o["space"] = OLD
            st["young"].discard(i)
            for fld, val in sorted(o["flds"].items()):
                if val is not None and val in objs and objs[val]["space"] == NURSERY:
                    st["rset"].add((i, fld, val))
            out.append("pro %d" % i)


def _runfin(st, out):
    if not st["queue"]:
        return
    i = st["queue"].pop(0)
    o = st["objs"].get(i)
    z = o["fin"] if o is not None else None
    if z:
        st["frames"][0][z] = i
    if o is not None:
        st["done"].add(o["ser"])
    out.append("ran %d" % i)


def _num(s):
    return None if s == "-" else int(s)


def _ser(st, i):
    o = st["objs"].get(i)
    return o["ser"] if o is not None else 0


def _run(ops):
    st = _blank()
    out = []
    for op in ops:
        k = op[0]
        if k == "new":
            fin = None if len(op) == 2 else ("" if len(op) == 3 else op[3])
            i = int(op[1])
            st["stamp"] += 1
            st["objs"][i] = _obj(fin, st["stamp"])
            st["young"].add(i)
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
            a = int(op[1])
            st["pairs"].append((a, _ser(st, a), int(op[2])))
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
