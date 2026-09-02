"""A second implementation of the stage machine, written from the specification.

It shares no code with the tree under /app and it is built the other way round on
purpose, so that agreement between the two is evidence about the specification
rather than about one author's habits.

  The plan is read into flat records - a list of node triples, a list of edge
  triples and a list of scheduled events - instead of the adjacency dictionaries
  the runtime keeps.

  The machine is a set of functions over one mutable dictionary rather than a
  class holding its own state.

  The bound is computed once for the whole graph per sweep, by seeding every
  node's account at the same time and relaxing every edge until nothing moves,
  where the runtime asks the question one node at a time and lets the caller take
  the smallest answer. The two agree because the rewrites are monotone and the
  merge at every node is a minimum, so a relaxation seeded from all the accounts
  at once settles at the pointwise minimum of the relaxations seeded from each of
  them alone. That equality is the reason this file is worth having: it is the
  same requirement reached by a different route.

Everything the machine grades comes out of `play`: the ordered trace and, for
each sink, the stamps it took in order.
"""

CAP = 4000


def rd(text):
    hz = 0
    kind, par = {}, {}
    order, edge, sched = [], [], []
    for raw in text.splitlines():
        body = raw.split("#", 1)[0].strip()
        if not body:
            continue
        w = body.split()
        if w[0] == "hz":
            hz = int(w[1])
        elif w[0] == "node":
            order.append(w[1])
            kind[w[1]] = w[2]
            par[w[1]] = int(w[3]) if len(w) > 3 else 0
        elif w[0] == "wire":
            edge.append((w[1], w[2], int(w[3])))
        elif w[0] == "put":
            sched.append((int(w[1]), "put", w[2], int(w[3])))
        elif w[0] == "low":
            sched.append((int(w[1]), "low", w[2], int(w[3])))
        elif w[0] == "shut":
            sched.append((int(w[1]), "shut", w[2], 0))
        else:
            raise ValueError(body)
    edge.sort(key=lambda e: (e[0], e[1], e[2]))
    return {"hz": hz, "kind": kind, "par": par, "order": order,
            "edge": edge, "sched": sorted(sched, key=lambda r: r[0])}


def fresh(m):
    return {"t": 0, "i": 0, "row": [],
            "box": dict((n, []) for n in m["order"]),
            "buk": dict((n, {}) for n in m["order"]),
            "cut": dict((n, set()) for n in m["order"]),
            "low": dict((n, 0) for n in m["order"]),
            "off": dict((n, False) for n in m["order"])}


def top(m, n, b):
    return (b + 1) * m["par"][n] - 1


def free(m, s, n, b):
    while b in s["cut"][n]:
        b += 1
    return b


def account(m, s, n):
    k = m["kind"][n]
    if k == "src":
        return None if s["off"][n] else s["low"][n]
    if k == "sink":
        return None
    held = s["box"][n]
    if k == "relay":
        return min(held) if held else None
    if k == "lift":
        if not held:
            return None
        return max(min(held), m["par"][n])
    if k == "gather":
        seen = [top(m, n, b) for b in s["buk"][n]]
        seen += [top(m, n, free(m, s, n, x // m["par"][n])) for x in held]
        return min(seen) if seen else None
    return None


def rewrite(m, s, n, y):
    k = m["kind"][n]
    if k == "relay":
        return y
    if k == "lift":
        return max(y, m["par"][n])
    if k == "gather":
        return top(m, n, free(m, s, n, y // m["par"][n]))
    return None


def reach(m, s):
    hz = m["hz"]
    emit, land = {}, {}
    for n in m["order"]:
        v = account(m, s, n)
        if v is not None and v < hz:
            emit[n] = v
    moving = True
    while moving:
        moving = False
        for a, b, lag in m["edge"]:
            if a not in emit:
                continue
            y = emit[a] + lag
            if y >= hz:
                continue
            if b not in land or y < land[b]:
                land[b] = y
                moving = True
            e = rewrite(m, s, b, y)
            if e is None or e >= hz:
                continue
            if b not in emit or e < emit[b]:
                emit[b] = e
                moving = True
    return land


def say(s, row):
    s["row"].append(row)


def push(m, s, n, x):
    for a, b, lag in m["edge"]:
        if a != n:
            continue
        y = x + lag
        if y >= m["hz"]:
            say(s, ["hz", s["t"], b, y])
        else:
            s["box"][b].append(y)


def take(m, s, n, x):
    k = m["kind"][n]
    if k == "relay":
        push(m, s, n, x)
    elif k == "lift":
        push(m, s, n, max(x, m["par"][n]))
    elif k == "sink":
        say(s, ["sk", s["t"], n, x])
    elif k == "gather":
        b = x // m["par"][n]
        if b in s["cut"][n]:
            say(s, ["ls", s["t"], n, b, x])
            return
        if b not in s["buk"][n]:
            s["buk"][n][b] = []
            say(s, ["op", s["t"], n, b])
        s["buk"][n][b].append(x)
        say(s, ["in", s["t"], n, b, x])
    else:
        raise ValueError(n)


def clock(m, s):
    while s["i"] < len(m["sched"]) and m["sched"][s["i"]][0] <= s["t"]:
        _, op, n, val = m["sched"][s["i"]]
        s["i"] += 1
        if m["kind"][n] != "src":
            raise ValueError(n)
        if op == "put":
            if s["off"][n] or val < s["low"][n]:
                raise ValueError(n)
            say(s, ["pt", s["t"], n, val])
            push(m, s, n, val)
        elif op == "low":
            if val < s["low"][n] or s["off"][n]:
                raise ValueError(n)
            s["low"][n] = val
            say(s, ["lo", s["t"], n, val])
        else:
            s["off"][n] = True
            say(s, ["sh", s["t"], n])


def serve(m, s):
    for n in sorted(s["box"]):
        if s["box"][n]:
            take(m, s, n, s["box"][n].pop(0))
            return


def close(m, s):
    land = reach(m, s)
    ripe = []
    for n in m["order"]:
        if m["kind"][n] != "gather":
            continue
        edge = land.get(n)
        for b in sorted(s["buk"][n]):
            hi = top(m, n, b)
            if any(x <= hi for x in s["box"][n]):
                continue
            if edge is not None and edge <= hi:
                continue
            ripe.append((n, b))
    for n, b in sorted(ripe):
        mem = list(s["buk"][n].pop(b))
        s["cut"][n].add(b)
        say(s, ["sl", s["t"], n, b, mem])
        push(m, s, n, top(m, n, b))


def spent(m, s):
    if s["i"] < len(m["sched"]):
        return False
    for n in m["order"]:
        if s["box"][n] or s["buk"][n]:
            return False
    return True


def play(text):
    m = rd(text)
    s = fresh(m)
    while True:
        s["t"] += 1
        if s["t"] > CAP:
            raise RuntimeError("cap")
        clock(m, s)
        serve(m, s)
        close(m, s)
        if spent(m, s):
            say(s, ["en", s["t"]])
            break
    got = {}
    for r in s["row"]:
        if r[0] == "sk":
            got.setdefault(r[2], []).append(r[3])
    return {"tr": s["row"], "sk": got}
