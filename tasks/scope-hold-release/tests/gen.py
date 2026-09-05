import random

LIVES = ["sing", "scoped", "trans"]
TAGS = ["job", "call"]


def tbl_deps(deps, nm, seen=None):
    if seen is None:
        seen = set()
    if nm in seen:
        return seen
    seen.add(nm)
    for d in deps.get(nm, []):
        tbl_deps(deps, d, seen)
    return seen


def table(rnd, n):
    nms = ["n%d" % i for i in range(n)]
    life = {}
    for m in nms:
        life[m] = rnd.choice(LIVES)
    deps = {}
    for i, m in enumerate(nms):
        d = []
        for j in range(i + 1, len(nms)):
            if rnd.random() < 0.26:
                d.append(nms[j])
        deps[m] = d
    wraps = {}
    for i, m in enumerate(nms):
        wraps[m] = ""
        if rnd.random() < 0.18 and i + 1 < len(nms):
            wraps[m] = nms[rnd.randrange(i + 1, len(nms))]
    tag = {}
    for m in nms:
        tag[m] = rnd.choice(TAGS) if (life[m] != "sing" and rnd.random() < 0.22) else ""
    shut = {}
    for m in nms:
        shut[m] = ""
    trans = sorted([m for m in nms if life[m] == "trans" and not tag[m] and not wraps[m]])
    for m in nms:
        if trans and life[m] != "sing" and rnd.random() < 0.16:
            pick = rnd.choice(trans)
            if pick != m:
                shut[m] = pick

    facs = {}
    for m in nms:
        facs[m] = []
    holders = sorted([m for m in nms if life[m] != "sing"])
    if holders:
        h = rnd.choice(holders)
        pool = sorted([m for m in nms if m != h and life[m] == "scoped"])
        if pool:
            f = rnd.choice(pool)
            facs[h] = [f]
            if rnd.random() < 0.55:
                tag[f] = rnd.choice(TAGS)
            deep = sorted([d for d in tbl_deps(deps, f) if d != f and life[d] != "sing"])
            if deep and rnd.random() < 0.45:
                tag[rnd.choice(deep)] = rnd.choice(TAGS)

    rows = []
    for m in nms:
        rows.append((m, LIVES.index(life[m]), sorted(deps[m]), sorted(facs[m]),
                     tag[m], wraps[m], shut[m]))
    return rows, life, facs, tag


def stream(seed, cross):
    rnd = random.Random(seed)
    rows, life, facs, tag = table(rnd, rnd.randrange(5, 9))
    nms = sorted(life)
    hold = sorted([m for m in nms if facs[m]])
    ops = []
    depth = 0
    ops.append(("open", rnd.choice(TAGS)))
    depth += 1
    if hold:
        ops.append(("resolve", hold[0]))
        if cross:
            ops.append(("open", rnd.choice(TAGS + TAGS + [""])))
            depth += 1
            ops.append(("invoke", facs[hold[0]][0]))
    for _ in range(rnd.randrange(4, 10)):
        r = rnd.random()
        if r < 0.24 and depth < 4:
            ops.append(("open", rnd.choice(TAGS + [""])))
            depth += 1
        elif r < 0.42 and depth > 1:
            ops.append(("close",))
            depth -= 1
        elif r < 0.66 and hold:
            ops.append(("invoke", facs[hold[0]][0]))
        else:
            ops.append(("resolve", rnd.choice(nms)))
    while depth > 0:
        ops.append(("close",))
        depth -= 1
    return rows, ops
