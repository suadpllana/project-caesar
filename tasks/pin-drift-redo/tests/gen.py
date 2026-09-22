"""The nonce population: programs built from a seed drawn after the agent's container is gone.

Nothing here knows what a program prints. The families are shaped at the rules rather than
sampled uniformly, because an unshaped population barely exercises a mechanism: each one puts
pressure on one decision while the others keep running.

  plain   nothing ever moves under an open transaction - the must-still-work side
  move    commits landing under an open transaction, on keys it has taken
  read    reads placed either side of those commits, so some numbers are fixed and some owed
  sect    marks and undos while the transaction runs, with commits in between
  cond    conditions recorded early and tested at the close, after a commit has moved them
  nest    marks several deep, so a failing condition cuts an inner section and the next one
          sees what the cut left
  chain   one key copied along a chain of keys, then moved
  many    four to six transactions open at once
  late    a commit landing immediately before a close, with no op of that transaction between
  wide    one long transaction under a stream of closes (the re-take scale family)
  deep    one transaction of many conditional sections (the cut scale family)

`wide` and `deep` are fixed at three programs each; the rest take the per-family count the
runner passes in.
"""
import random

FAMILIES = (
    ("plain", False),
    ("move", False),
    ("read", False),
    ("sect", False),
    ("cond", False),
    ("nest", False),
    ("chain", False),
    ("many", False),
    ("late", False),
    ("wide", True),
    ("deep", True),
)

BIG = 3


def programs(seed, per):
    out = []
    for fam, big in FAMILIES:
        for i in range(BIG if big else per):
            r = random.Random("%s|%s|%d" % (seed, fam, i))
            out.append((fam, "%s-%d" % (fam, i), BUILD[fam](r)))
    return out


# --- shared shapes --------------------------------------------------------------------

def work_op(r, t, keys, hot=None):
    """One ordinary op for transaction t. `hot` biases which key it names."""
    k = hot if hot is not None and r.random() < 0.45 else r.randrange(keys)
    pick = r.random()
    if pick < 0.30:
        return "add %d %d %d" % (t, k, r.randint(-9, 9))
    if pick < 0.48:
        return "cpy %d %d %d" % (t, k, r.randrange(keys))
    if pick < 0.60:
        return "raw %d %d %d" % (t, k, r.randrange(keys))
    if pick < 0.72:
        return "rd %d %d" % (t, k)
    if pick < 0.84:
        return "put %d %d %d" % (t, k, r.randint(0, 40))
    lo = r.randrange(keys)
    return "bmp %d %d %d %d" % (t, lo, r.randint(lo + 1, keys), r.randint(-5, 5))


def mover(r, t, keys, hot=None):
    """A whole short transaction that commits one key, moving it under whoever holds it."""
    k = hot if hot is not None and r.random() < 0.6 else r.randrange(keys)
    body = ["tx %d" % t]
    if r.random() < 0.35:
        body.append("add %d %d %d" % (t, k, r.randint(1, 20)))
    else:
        body.append("put %d %d %d" % (t, k, r.randint(0, 60)))
    body.append("fin %d" % t)
    return body


def cond_op(r, t, keys, anchor=True):
    """A condition. Anchored ones put a number in first, so they stand unless something moves."""
    k = r.randrange(keys)
    if anchor and r.random() < 0.5:
        v = r.randint(0, 30)
        kind = "chk" if r.random() < 0.6 else "lim"
        return ["put %d %d %d" % (t, k, v),
                "%s %d %d %d" % (kind, t, k, v if kind == "chk" else v - r.randint(0, 3))]
    if r.random() < 0.45:
        return ["chk %d %d %d" % (t, k, r.randint(-2, 12))]
    return ["lim %d %d %d" % (t, k, r.randint(-12, 12))]


# --- the families ---------------------------------------------------------------------

def build_plain(r):
    keys = r.randint(4, 9)
    out = ["cfg %d" % keys]
    t = 1
    for _ in range(r.randint(2, 4)):
        out.append("tx %d" % t)
        for _ in range(r.randint(4, 10)):
            pick = r.random()
            if pick < 0.62:
                out.append(work_op(r, t, keys))
            elif pick < 0.74:
                out.append("mk %d" % t)
            elif pick < 0.82:
                out.append("un %d" % t)
            else:
                out += cond_op(r, t, keys)
        out.append("fin %d" % t if r.random() < 0.85 else "drp %d" % t)
        t += 1
    return out


def build_move(r):
    keys = r.randint(5, 10)
    hot = r.randrange(keys)
    out = ["cfg %d" % keys, "tx 1"]
    t = 2
    for _ in range(r.randint(3, 6)):
        for _ in range(r.randint(1, 4)):
            out.append(work_op(r, 1, keys, hot))
        out += mover(r, t, keys, hot)
        t += 1
    for _ in range(r.randint(1, 4)):
        out.append(work_op(r, 1, keys, hot))
    out.append("fin 1")
    return out


def build_read(r):
    keys = r.randint(4, 8)
    hot = r.randrange(keys)
    out = ["cfg %d" % keys, "tx 1"]
    t = 2
    for _ in range(r.randint(3, 5)):
        out.append("add 1 %d %d" % (hot, r.randint(-6, 6)))
        if r.random() < 0.6:
            out.append("rd 1 %d" % hot)
        out.append(work_op(r, 1, keys, hot))
        out += mover(r, t, keys, hot)
        t += 1
        if r.random() < 0.6:
            out.append("rd 1 %d" % hot)
        out.append(work_op(r, 1, keys, hot))
    out.append("fin 1")
    return out


def build_sect(r):
    keys = r.randint(4, 9)
    hot = r.randrange(keys)
    out = ["cfg %d" % keys, "tx 1"]
    t = 2
    depth = 0
    for _ in range(r.randint(4, 8)):
        if r.random() < 0.5:
            out.append("mk 1")
            depth += 1
        for _ in range(r.randint(1, 3)):
            out.append(work_op(r, 1, keys, hot))
        if r.random() < 0.5:
            out += mover(r, t, keys, hot)
            t += 1
        if depth and r.random() < 0.55:
            out.append("un 1")
            depth -= 1
            if r.random() < 0.7:
                out.append("add 1 %d 0" % hot)
                out.append("rd 1 %d" % r.randrange(keys))
        elif r.random() < 0.2:
            out.append("un 1")
    for _ in range(r.randint(1, 3)):
        out.append(work_op(r, 1, keys, hot))
    out.append("fin 1")
    return out


def build_cond(r):
    keys = r.randint(4, 8)
    hot = r.randrange(keys)
    out = ["cfg %d" % keys, "tx 1"]
    t = 2
    for _ in range(r.randint(3, 6)):
        if r.random() < 0.7:
            out.append("mk 1")
        for _ in range(r.randint(1, 3)):
            out.append(work_op(r, 1, keys, hot))
        out += cond_op(r, 1, keys)
        if r.random() < 0.5:
            out += mover(r, t, keys, hot)
            t += 1
    out.append("fin 1")
    return out


def build_nest(r):
    keys = r.randint(4, 7)
    hot = r.randrange(keys)
    out = ["cfg %d" % keys, "tx 1"]
    t = 2
    depth = 0
    for _ in range(r.randint(5, 9)):
        if depth < 4 and r.random() < 0.6:
            out.append("mk 1")
            depth += 1
        out.append(work_op(r, 1, keys, hot))
        if r.random() < 0.7:
            out += cond_op(r, 1, keys, anchor=r.random() < 0.5)
        if r.random() < 0.3:
            out += mover(r, t, keys, hot)
            t += 1
    out.append("fin 1")
    return out


def build_chain(r):
    keys = r.randint(5, 9)
    root = r.randrange(keys)
    out = ["cfg %d" % keys, "tx 1"]
    link = root
    owed = []
    for k in range(keys):
        if k == root:
            continue
        if link == root:
            owed.append(k)
        out.append("%s 1 %d %d" % ("cpy" if r.random() < 0.6 else "raw", k, link))
        if r.random() < 0.5:
            out.append("add 1 %d %d" % (k, r.randint(-4, 4)))
        if r.random() < 0.4:
            link = k
    out += mover(r, 2, keys, root)
    if owed and r.random() < 0.7:
        out.append("bmp 1 %d %d %d" % (root, min(root + 3, keys), r.randint(-3, 3)))
        out.append("rd 1 %d" % r.choice(owed))
    if r.random() < 0.5:
        out.append("rd 1 %d" % root)
    if r.random() < 0.6:
        out.append("rd 1 %d" % r.randrange(keys))
    if r.random() < 0.6:
        out.append(work_op(r, 1, keys, root))
    out.append("fin 1")
    return out


def build_many(r):
    keys = r.randint(5, 10)
    live = list(range(1, r.randint(4, 6) + 1))
    out = ["cfg %d" % keys] + ["tx %d" % t for t in live]
    nxt = len(live) + 1
    for _ in range(r.randint(14, 26)):
        t = r.choice(live)
        pick = r.random()
        if pick < 0.58:
            out.append(work_op(r, t, keys))
        elif pick < 0.68:
            out.append("mk %d" % t)
        elif pick < 0.74:
            out.append("un %d" % t)
        elif pick < 0.82:
            out += cond_op(r, t, keys)
        elif pick < 0.92:
            out.append("fin %d" % t)
            live.remove(t)
            live.append(nxt)
            out.append("tx %d" % nxt)
            nxt += 1
        else:
            out.append("drp %d" % t)
            live.remove(t)
            live.append(nxt)
            out.append("tx %d" % nxt)
            nxt += 1
    for t in live:
        out.append("fin %d" % t)
    return out


def build_late(r):
    keys = r.randint(4, 8)
    out = ["cfg %d" % keys]
    live = [1, 2]
    out += ["tx 1", "tx 2"]
    hot = r.randrange(keys)
    for _ in range(r.randint(3, 6)):
        out.append(work_op(r, 1, keys, hot))
        out.append(work_op(r, 2, keys, hot))
    if r.random() < 0.6:
        out += cond_op(r, 1, keys)
    out.append("fin 2")
    out.append("fin 1")
    return out


def build_wide(r):
    keys = 12
    ops, commits = 60000, 12000
    out = ["cfg %d" % keys, "tx 1"]
    nxt = 2
    per = ops // commits
    for i in range(ops):
        k = r.randrange(keys)
        pick = r.random()
        if pick < 0.50:
            out.append("add 1 %d %d" % (k, r.randint(-5, 5)))
        elif pick < 0.80:
            out.append("cpy 1 %d %d" % (k, r.randrange(keys)))
        elif pick < 0.90:
            out.append("rd 1 %d" % k)
        else:
            out.append("put 1 %d %d" % (k, r.randint(0, 50)))
        if i % per == per - 1:
            j = r.randrange(keys)
            out += ["tx %d" % nxt, "put %d %d %d" % (nxt, j, r.randint(0, 99)), "fin %d" % nxt]
            nxt += 1
    out.append("fin 1")
    return out


def build_deep(r):
    keys, sections = 24, 20000
    out = ["cfg %d" % keys, "tx 1"]
    for _ in range(sections):
        out.append("mk 1")
        k = r.randrange(keys)
        v = r.randint(0, 40)
        out.append("put 1 %d %d" % (k, v))
        for _ in range(2):
            kk = r.randrange(keys)
            while kk == k:
                kk = r.randrange(keys)
            if r.random() < 0.6:
                out.append("add 1 %d %d" % (kk, r.randint(-4, 4)))
            else:
                out.append("cpy 1 %d %d" % (kk, r.randrange(keys)))
        out.append("chk 1 %d %d" % (k, v + (r.randint(1, 5) if r.random() < 0.35 else 0)))
    out.append("fin 1")
    return out


BUILD = {
    "plain": build_plain,
    "move": build_move,
    "read": build_read,
    "sect": build_sect,
    "cond": build_cond,
    "nest": build_nest,
    "chain": build_chain,
    "many": build_many,
    "late": build_late,
    "wide": build_wide,
    "deep": build_deep,
}
