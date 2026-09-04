"""A second implementation of the same specification, written from the
specification and sharing no code with the tree.

Where the machine keeps a book object with a union-find inside it and asks a
policy about one cell at a time, this keeps one flat list of groups and answers
the whole question by enumerating the groups a legal future could actually
build - starting from the cell the key sits in, absorbing whole cells that a
still-open tag can reach over keys still on the desk, refusing any group that
would put two barred keys together - and asking of every one of them whether the
row would still read the same.

The tree's policy argues that it is enough to look at each cell that could still
be welded on one at a time, because welding several of them at once cannot
produce a smaller key or an earlier post than the smallest and earliest among
them. This makes no such argument, and that is the point of the file.

It settles a tick the same way for the same reason: the set of rows a tick owes
is the smallest set consistent with itself, grown one cell at a time from the
cells that had already gone, never the largest. A tag whose pool names a key
that has gone, or that would go were this set of rows written, is asked nothing:
its pool was handed to it whole and is stale the moment any of it is filed.

Nothing here is imported by the tree and nothing here is readable from the run.
"""


def read(text):
    st = {"watch": [], "runs": {}, "tags": {}, "script": []}
    body = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        w = line.split()
        if w[0] == "go":
            body = True
        elif not body:
            if w[0] == "watch":
                st["watch"] = [int(x) for x in w[1:]]
            elif w[0] == "run":
                st["runs"][w[1]] = sorted(int(x) for x in w[2:])
            elif w[0] == "tag":
                st["tags"][w[1]] = sorted(int(x) for x in w[2:])
        elif w[0] == "shut":
            st["script"].append((w[0], w[1], 0, 0))
        else:
            st["script"].append((w[0], w[1], int(w[2]), int(w[3])))
    return st


def start(st):
    keys = set(st["watch"])
    for pool in st["runs"].values():
        keys.update(pool)
    for pool in st["tags"].values():
        keys.update(pool)
    return {"keys": sorted(keys),
            "part": [frozenset([k]) for k in sorted(keys)],
            "bars": [], "post": {}, "runs": st["runs"], "tags": st["tags"],
            "live": sorted(set(st["runs"]) | set(st["tags"])),
            "watch": list(st["watch"]), "done": [], "gone": set()}


def home(w, key):
    for grp in w["part"]:
        if key in grp:
            return grp
    return frozenset([key])


def merge(w, a, b):
    ga, gb = home(w, a), home(w, b)
    if ga == gb:
        return
    rest = [g for g in w["part"] if g is not ga and g is not gb]
    rest.append(ga | gb)
    w["part"] = sorted(rest, key=lambda g: min(g))


def clean(w, grp):
    for a, b in w["bars"]:
        if a in grp and b in grp:
            return False
    return True


def reachable(w, seed, off):
    live_tags = [n for n in sorted(w["tags"])
                 if n in w["live"] and not (set(w["tags"][n]) & off)]
    if not w["bars"]:
        seen = set(seed)
        work = [seed]
        while work:
            grp = work.pop()
            for n in live_tags:
                pool = set(k for k in w["tags"][n] if k not in off)
                if not pool & set(grp):
                    continue
                for k in pool:
                    nxt = home(w, k)
                    if nxt & off:
                        continue
                    new = set(nxt) - seen
                    if new:
                        seen.update(new)
                        work.append(nxt)
        return [frozenset(seen)]
    seen = set()
    stack = [seed]
    groups = []
    while stack:
        grp = stack.pop()
        if grp in seen:
            continue
        seen.add(grp)
        groups.append(grp)
        for n in live_tags:
            pool = [k for k in w["tags"][n] if k not in off]
            if not (set(pool) & grp):
                continue
            for k in pool:
                if k in grp:
                    continue
                nxt = home(w, k)
                if nxt & off:
                    continue
                wider = grp | nxt
                if wider != grp and clean(w, wider):
                    stack.append(wider)
    return groups


def face(w, grp):
    top = None
    for (n, k) in sorted(w["post"]):
        if k in grp and (top is None or (n, k) < top):
            top = (n, k)
    return min(grp), top


def steady(w, key, off):
    here = home(w, key)
    rep, top = face(w, here)
    if top is None:
        return False
    wide = set()
    for grp in reachable(w, here, off):
        wide |= grp
        r2, t2 = face(w, grp)
        if r2 != rep or t2 != top:
            return False
    for n in sorted(w["runs"]):
        if n not in w["live"]:
            continue
        for k in w["runs"][n]:
            if (n, k) in w["post"]:
                continue
            if k in wide and (n, k) < top:
                return False
    return True


def ready(w):
    dead = set(w["gone"])
    off = set(dead)
    picked = []
    moved = True
    while moved:
        moved = False
        for k in w["watch"]:
            if k in w["done"] or k in picked:
                continue
            here = home(w, k)
            if here & dead:
                continue
            if here & off:
                picked.append(k)
                moved = True
                continue
            if steady(w, k, off):
                picked.append(k)
                off = off | here
                moved = True
    return sorted(picked)


def play(text):
    st = read(text)
    w = start(st)
    rows = []
    t = 0
    for kind, who, a, b in st["script"]:
        t += 1
        if kind == "post":
            w["post"][(who, a)] = b
            rows.append(["ps", t, who, a, b])
        elif kind == "tie":
            if who in w["live"] and a not in w["gone"] and b not in w["gone"]:
                merge(w, a, b)
                rows.append(["ty", t, who, a, b])
        elif kind == "bar":
            if who in w["live"] and a not in w["gone"] and b not in w["gone"]:
                w["bars"].append((min(a, b), max(a, b)))
                rows.append(["br", t, who, a, b])
        elif kind == "shut":
            w["live"] = [n for n in w["live"] if n != who]
            rows.append(["sd", t, who])
        lines = []
        for k in ready(w):
            rep, top = face(w, home(w, k))
            lines.append([k, rep, w["post"][top]])
        for k, rep, sc in lines:
            w["done"].append(k)
            went = home(w, k)
            w["gone"] |= went
            w["live"] = [n for n in w["live"]
                         if n not in w["tags"] or not (set(w["tags"][n]) & went)]
            rows.append(["fl", t, k, rep, sc])
    rows.append(["ed", t])
    return rows


def filings(rows):
    out = {}
    for row in rows:
        if row[0] == "fl":
            out[str(row[2])] = [row[1], row[3], row[4]]
    return out
