"""Scenario generation, from a seed and nothing else.

Each family shapes what the two sides do to the same nodes: `plain` keeps them mostly out
of each other's way, `gone` sets removal against change, `clash` drives two nodes at one
name, `knot` crosses moves so folders end up inside each other, and `wide` runs a larger
tree for longer. Operations are generated against the side's own tree as it stands, so
almost all of them apply; the sealed model is stepped between rounds to know that tree.

Nothing here reveals an expected trace: the model is used to advance the two sides, never
to record what the engine should print.
"""
import random

import model

NAMES = ["ab", "cd", "ef", "gh", "kb", "KB", "mn", "pq", "rs",
         "notes.txt", "plan.txt", "log.dat", "old.cfg", "Notes.txt", "a.b.c"]
DIRS = ["src", "doc", "bin", "tmp", "Src", "out"]
BODY = ["%s%d" % (c, d) for c in "vwxyz" for d in range(1, 6)]

FAMILIES = (
    ("plain", 3),
    ("gone", 3),
    ("clash", 3),
    ("knot", 3),
    ("wide", 4),
)

PAIRS = {
    "plain": ("split", "write", "race"),
    "gone": ("killed", "killed", "split", "race"),
    "clash": ("race", "write", "flip", "swap", "renamed"),
    "knot": ("moved", "ring", "swap", "split", "flip"),
    "wide": ("killed", "race", "moved", "write", "flip", "split", "ring"),
}

MIX = {
    "plain": (("ed", 4), ("mv", 3), ("mkf", 3), ("mkd", 1), ("rm", 1)),
    "gone": (("rm", 5), ("ed", 3), ("mv", 3), ("mkf", 1), ("mkd", 1)),
    "clash": (("mkf", 4), ("mv", 4), ("ed", 3), ("mkd", 2), ("rm", 1)),
    "knot": (("mv", 6), ("mkd", 2), ("rm", 2), ("ed", 2), ("mkf", 1)),
    "wide": (("mv", 3), ("ed", 3), ("mkf", 3), ("rm", 2), ("mkd", 2)),
}


def folders(t):
    return [model.ROOT] + [k for k in sorted(t) if k != model.ROOT and t[k][0] == "d"]


def files(t):
    return [k for k in sorted(t) if k != model.ROOT and t[k][0] == "f"]


def subtree(t, k):
    out = [k]
    i = 0
    while i < len(out):
        out += sorted(model.kids(t, out[i]))
        i += 1
    return out


def start(rng, big):
    lines = []
    tree = model.new()
    nid = 1
    tops = rng.sample(DIRS, 3 if big else 2)
    for nm in tops:
        tree[str(nid)] = ("d", model.ROOT, nm, None)
        lines.append("d %d /%s" % (nid, nm))
        nid += 1
    for _ in range(2 if big else 1):
        par = rng.choice(folders(tree)[1:])
        nm = rng.choice(DIRS)
        if model.taken(tree, par, nm, True):
            continue
        tree[str(nid)] = ("d", par, nm, None)
        lines.append("d %d %s" % (nid, model.glue(model.pth(tree, par), nm)))
        nid += 1
    for _ in range(7 if big else 5):
        par = rng.choice(folders(tree))
        nm = rng.choice(NAMES)
        if model.taken(tree, par, nm, True):
            continue
        c = rng.choice(BODY)
        tree[str(nid)] = ("f", par, nm, c)
        lines.append("f %d %s %s" % (nid, model.glue(model.pth(tree, par), nm), c))
        nid += 1
    return lines, tree, nid


CAP = 24
ROOF = 30


def one(rng, t, fold, fam, hot, ops):
    kinds, weights = zip(*MIX[fam])
    kind = rng.choices(kinds, weights=weights)[0]
    if kind in ("mkd", "mkf") and len(t) > CAP:
        kind = "ed"
    fs, ds = files(t), folders(t)
    warm = [k for k in hot if k in t]
    if kind == "ed" and fs:
        k = rng.choice([x for x in warm if t[x][0] == "f"] or fs)
        op = ("ed", model.pth(t, k), rng.choice(BODY))
    elif kind == "mv" and (fs or len(ds) > 1):
        pool = [x for x in warm if x != model.ROOT] or (fs + ds[1:])
        if not pool:
            return
        k = rng.choice(pool)
        par = rng.choice(ds)
        nm = rng.choice(NAMES if t[k][0] == "f" else DIRS)
        if rng.random() < 0.4:
            par = t[k][1]
        op = ("mv", model.pth(t, k), model.glue(model.pth(t, par), nm))
    elif kind == "rm" and (fs or len(ds) > 1):
        pool = [x for x in warm if x != model.ROOT] or (fs + ds[1:])
        if not pool:
            return
        k = rng.choice(pool)
        for j in reversed(subtree(t, k)):
            ops.append(("rm", model.pth(t, j)))
            model.do(t, ops[-1], fold, lambda: "g%d" % rng.randrange(10 ** 9))
        return
    elif kind == "mkd":
        par = rng.choice(ds)
        op = ("mkd", model.glue(model.pth(t, par), rng.choice(DIRS)))
    else:
        par = rng.choice(ds)
        op = ("mkf", model.glue(model.pth(t, par), rng.choice(NAMES)), rng.choice(BODY))
    ops.append(op)
    model.do(t, op, fold, lambda: "g%d" % rng.randrange(10 ** 9))


def elsewhere(rng, t, k):
    out = [d for d in folders(t) if not model.inside(t, d, k)]
    return rng.choice(out) if out else model.ROOT


def pair(rng, kind, lo, ro, hot, lops, rops):
    """One scripted interaction: the two sides act on the same node, deliberately."""
    live = [k for k in hot if k in lo and k in ro]
    if not live:
        return
    k = rng.choice(live)
    lp, rp = model.pth(lo, k), model.pth(ro, k)
    if kind == "killed":
        for j in reversed(subtree(lo, k)):
            lops.append(("rm", model.pth(lo, j)))
            model.do(lo, lops[-1], False, lambda: "x")
        if ro[k][0] == "f":
            rops.append(("ed", rp, rng.choice(BODY)))
        else:
            rops.append(("mv", rp, model.glue(model.pth(ro, elsewhere(rng, ro, k)),
                                              rng.choice(DIRS))))
        model.do(ro, rops[-1], True, lambda: "x")
        return
    if kind == "moved":
        lops.append(("mv", lp, model.glue(model.pth(lo, elsewhere(rng, lo, k)), lo[k][2])))
        rops.append(("mv", rp, model.glue(model.pth(ro, elsewhere(rng, ro, k)), ro[k][2])))
    elif kind == "renamed":
        pool = NAMES if lo[k][0] == "f" else DIRS
        lops.append(("mv", lp, model.glue(model.pth(lo, lo[k][1]), rng.choice(pool))))
        rops.append(("mv", rp, model.glue(model.pth(ro, ro[k][1]), rng.choice(pool))))
    elif kind == "split":
        pool = NAMES if lo[k][0] == "f" else DIRS
        lops.append(("mv", lp, model.glue(model.pth(lo, lo[k][1]), rng.choice(pool))))
        rops.append(("mv", rp, model.glue(model.pth(ro, elsewhere(rng, ro, k)), ro[k][2])))
    elif kind == "write" and lo[k][0] == "f":
        lops.append(("ed", lp, rng.choice(BODY)))
        rops.append(("ed", rp, rng.choice(BODY)))
    elif kind == "race":
        if len(lo) > CAP:
            return
        par = rng.choice(folders(lo))
        nm = rng.choice(NAMES)
        lops.append(("mkf", model.glue(model.pth(lo, par), nm), rng.choice(BODY)))
        par2 = par if par in ro else model.ROOT
        rops.append(("mkf", model.glue(model.pth(ro, par2), nm), rng.choice(BODY)))
    elif kind == "flip":
        nm = lo[k][2]
        flipped = nm.upper() if nm.islower() else nm.lower()
        if flipped == nm:
            return
        lops.append(("mv", lp, model.glue(model.pth(lo, lo[k][1]), flipped)))
    elif kind == "swap":
        sibs = [j for j in model.kids(lo, lo[k][1]) if j != k and lo[j][0] == lo[k][0]]
        if not sibs:
            return
        other = rng.choice(sibs)
        par = model.pth(lo, lo[k][1])
        a, b = lo[k][2], lo[other][2]
        lops.append(("mv", model.glue(par, a), model.glue(par, "hold9")))
        lops.append(("mv", model.glue(par, b), model.glue(par, a)))
        lops.append(("mv", model.glue(par, "hold9"), model.glue(par, b)))
    elif kind == "ring":
        ds = [d for d in folders(lo)[1:] if d in ro]
        if len(ds) < 2:
            return
        rng.shuffle(ds)
        for i in range(len(ds)):
            for j in range(len(ds)):
                if i == j:
                    continue
                a, b = ds[i], ds[j]
                if model.inside(lo, a, b) or model.inside(lo, b, a):
                    continue
                lops.append(("mv", model.pth(lo, a),
                             model.glue(model.pth(lo, b), lo[a][2])))
                rops.append(("mv", model.pth(ro, b),
                             model.glue(model.pth(ro, a), ro[b][2])))
                return
        return


def build(seed, fam, rounds):
    rng = random.Random(seed)
    big = fam == "wide"
    lines, base, nxt = start(rng, big)
    rec = dict(base)
    lo, ro = dict(base), dict(base)
    made = [0]

    def fresh():
        made[0] += 1
        return "s%d" % made[0]

    for _ in range(rounds):
        pool = [k for k in sorted(rec) if k != model.ROOT]
        hot = rng.sample(pool, min(len(pool), 3)) if pool else []
        lops, rops = [], []
        for _ in range(rng.randint(1, 2)):
            before = (len(lops), len(rops))
            pair(rng, rng.choice(PAIRS[fam]), lo, ro, hot, lops, rops)
            for op in lops[before[0]:]:
                model.do(lo, op, False, fresh)
            for op in rops[before[1]:]:
                model.do(ro, op, True, fresh)
        for label, t, fold, box in (("L", lo, False, lops), ("R", ro, True, rops)):
            for _ in range(rng.randint(0, 3 if big else 2)):
                one(rng, t, fold, fam, hot, box)
        for label, box in (("L", lops), ("R", rops)):
            for op in box:
                lines.append(label + " " + " ".join(op))
        lines.append("sync")
        tgt, nxt, ml, mr = model.merge(rec, nxt, lo, ro)
        for cur, m, fold in ((lo, ml, False), (ro, mr, True)):
            for op in model.emit(cur, tgt, m, fold):
                model.do(cur, op, fold, fresh)
        lo = model.rekey(lo, tgt, fresh)
        ro = model.rekey(ro, tgt, fresh)
        rec = tgt
        if len(rec) - 1 > ROOF:
            break
    return "\n".join(lines)


def batch(tag, count):
    out = []
    for fam, rounds in FAMILIES:
        for i in range(count):
            name = "%s-%s-%d" % (fam, tag[:6], i)
            out.append((name, build("%s|%s|%d" % (tag, fam, i), fam, rounds)))
    return out
