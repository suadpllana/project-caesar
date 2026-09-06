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


def transaction(seed, cross):
    rnd = random.Random("construction-" + str(seed))
    rows, life, facs, tag = table(rnd, rnd.randrange(7, 13))
    rows = [(*row, rnd.random() < 0.2) for row in rows]
    nms = sorted(life)
    holders = rnd.sample(nms, 2)
    target = rnd.choice(nms)
    rows = [(nm, lt, deps, [target] if nm in holders else ff, mark, wrap, shut, fail)
            for nm, lt, deps, ff, mark, wrap, shut, fail in rows]
    ops = [("open", rnd.choice(TAGS)), ("resolve", holders[0])]
    depth = 1
    for _ in range(50):
        choice = rnd.random()
        nm = rnd.choice(nms)
        if choice < 0.18:
            ops.append(("fault", nm, rnd.choice(["on", "off"])))
        elif choice < 0.48:
            ops.append(("resolve", nm))
        elif choice < 0.64:
            ops.append(("invoke", target))
        elif choice < 0.80 and depth < 5:
            ops.append(("open", rnd.choice(TAGS + [""])))
            depth += 1
        elif depth > 1:
            ops.append(("close",))
            depth -= 1
        else:
            ops.extend([("fault", nm, "off"), ("resolve", nm),
                        ("fault", nm, "on"), ("resolve", nm)])
    while depth:
        ops.append(("close",))
        depth -= 1

    # A connected failure/retry tail guarantees construction and cache boundaries
    # are exercised even when the random graph rejects most requests at admission.
    prefix = "x" if cross else "z"
    names = [prefix + str(i) for i in rnd.sample(range(100, 999), 10)]
    old, new, mk, pool, bad, root, leaf, skin, flush, crumb = names
    rooted = rnd.choice([True, False])
    rows.extend([
        (old, 1, [], [mk], "", "", "", False),
        (new, 2, [crumb, bad], [mk], "", "", "", False),
        (mk, 1, [pool, root, bad], [], "", skin, "", False),
        (pool, 1, [], [], "job" if cross else "", "", "", False),
        (bad, 2, [crumb], [], "", "", "", True),
        (root, 0 if rooted else 2, [leaf], [], "", "", "", False),
        (leaf, 2, [], [], "job", "", flush, False),
        (skin, 2, [], [], "", "", "", False),
        (flush, 2, [crumb, bad], [], "", "", "", False),
        (crumb, 2, [], [], "", "", "", False),
    ])
    ops.extend([("open", "job"), ("open", ""), ("resolve", old)])
    if rnd.choice([True, False]):
        ops.append(("resolve", pool))
    if rnd.choice([True, False]):
        ops.append(("resolve", root))
    ops.extend([("open", "job"), ("resolve", new), ("invoke", mk),
                ("fault", bad, "off"), ("invoke", mk),
                ("fault", bad, "on"), ("invoke", mk), ("resolve", new),
                ("close",), ("close",), ("close",), ("open", "job"),
                ("invoke", mk), ("close",)])
    return rows, ops
