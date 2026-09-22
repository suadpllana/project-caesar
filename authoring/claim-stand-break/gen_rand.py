"""Random valid programs, for checking the reference against the naive oracle.

Keys and values come from small pools on purpose: restores, same-value rewrites and scans that
land exactly on their row limit are what separate the readings, and a wide alphabet never
produces them.
"""
import random

HEAD = ("get", "span", "put", "del", "mark", "back", "seal", "drop", "look", "open")


def program(seed, ops=40, keys=10, vals=3, live=4):
    rng = random.Random(seed)
    out = []
    nxt = 1
    open_ids = []
    marks = {}
    for _ in range(ops):
        if not open_ids or (len(open_ids) < live and rng.random() < 0.25):
            tid = nxt
            nxt += 1
            open_ids.append(tid)
            marks[tid] = []
            out.append("open %d" % tid)
            continue
        tid = rng.choice(open_ids)
        pick = rng.random()
        if pick < 0.20:
            out.append("get %d %d" % (tid, rng.randrange(keys)))
        elif pick < 0.40:
            lo = rng.randrange(keys)
            hi = min(keys - 1, lo + rng.randrange(1, keys))
            out.append("span %d %d %d %d" % (tid, lo, hi, rng.randrange(1, 4)))
        elif pick < 0.58:
            out.append("put %d %d %d" % (tid, rng.randrange(keys), rng.randrange(vals)))
        elif pick < 0.68:
            out.append("del %d %d" % (tid, rng.randrange(keys)))
        elif pick < 0.76:
            name = rng.choice("abc")
            marks[tid].append(name)
            out.append("mark %d %s" % (tid, name))
        elif pick < 0.84:
            if marks[tid]:
                out.append("back %d %s" % (tid, rng.choice(marks[tid])))
        elif pick < 0.94:
            open_ids.remove(tid)
            marks.pop(tid)
            out.append("seal %d" % tid)
        elif pick < 0.97:
            open_ids.remove(tid)
            marks.pop(tid)
            out.append("drop %d" % tid)
        else:
            lo = rng.randrange(keys)
            out.append("look %d %d" % (lo, min(keys - 1, lo + rng.randrange(1, keys))))
    for tid in list(open_ids):
        out.append("seal %d" % tid)
    out.append("look 0 %d" % (keys - 1))
    return "\n".join(out) + "\n"
