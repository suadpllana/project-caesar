import random

LIVES = ["sing", "scoped", "trans"]


def table(rnd, n):
    nms = ["n%d" % i for i in range(n)]
    life = {}
    for m in nms:
        life[m] = rnd.choice(LIVES)
    deps = {}
    for i, m in enumerate(nms):
        d = []
        for j in range(i + 1, len(nms)):
            if rnd.random() < 0.28:
                d.append(nms[j])
        deps[m] = d
    for m in nms:
        if life[m] == "sing":
            deps[m] = [d for d in deps[m] if life[d] != "scoped"]
    bad = True
    while bad:
        bad = False
        for m in nms:
            if life[m] != "sing":
                continue
            for d in list(deps[m]):
                if life[d] == "sing" and any(life[e] == "scoped" for e in deps[d]):
                    deps[m].remove(d)
                    bad = True
    facs = {}
    for m in nms:
        facs[m] = []
    holders = [m for m in nms if life[m] != "sing"]
    if holders:
        h = rnd.choice(holders)
        pool = [m for m in nms if m != h and life[m] == "scoped"]
        if pool:
            facs[h] = [rnd.choice(pool)]
    rows = []
    for m in nms:
        rows.append((m, LIVES.index(life[m]), sorted(deps[m]), sorted(facs[m])))
    return rows, life, facs


def stream(seed, cross):
    rnd = random.Random(seed)
    rows, life, facs = table(rnd, rnd.randrange(4, 8))
    nms = sorted(life)
    hold = [m for m in nms if facs[m]]
    ops = []
    depth = 0
    ops.append(("open",))
    depth += 1
    if hold:
        ops.append(("resolve", hold[0]))
        if cross:
            ops.append(("open",))
            depth += 1
            ops.append(("invoke", facs[hold[0]][0]))
    for _ in range(rnd.randrange(3, 9)):
        r = rnd.random()
        if r < 0.24 and depth < 4:
            ops.append(("open",))
            depth += 1
        elif r < 0.42 and depth > 1:
            ops.append(("close",))
            depth -= 1
        elif r < 0.70 and hold:
            ops.append(("invoke", facs[hold[0]][0]))
        else:
            ops.append(("resolve", rnd.choice(nms)))
    while depth > 0:
        ops.append(("close",))
        depth -= 1
    return rows, ops
