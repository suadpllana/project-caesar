"""What a program should print, worked out a second time and on purpose differently.

The reference walks the tables in an order that puts every parent before its children, which
settles each row's group before the table is expanded. This one knows nothing about that
order: it relaxes a worklist until neither a group nor a new key moves again, keeps the links
that reached a row as a flat table and merges them at the end by taking the smallest index per
column, and runs every write through one setter that remembers what the slot held, so walking
a change back is a restore of remembered slots rather than a log played in reverse.

Where the two agree, it is the contract they agree on and not a shared structure.
"""

GOES = ("drop", "clear", "bar", "wait")
MOVES = ("follow", "clear", "bar", "wait")


class Bad(Exception):
    pass


def _val(text):
    if text == "-":
        return None
    return int(text)


def _parse(lines):
    tabs, links, ops = {}, [], []
    for raw in lines:
        part = raw.split()
        if not part:
            continue
        head = part[0]
        if head == "tab":
            name, cols = part[1], part[2:]
            tabs[name] = (len(tabs), cols, {c: i for i, c in enumerate(cols)})
        elif head == "link":
            name, kid, col, par, goes, moves = part[1:]
            links.append((name, kid, tabs[kid][2][col], col, par, goes, moves))
        elif head == "put":
            tab = part[1]
            ops.append(("put", tab, tuple(_val(v) for v in part[2:])))
        elif head == "out":
            ops.append(("out", part[1], int(part[2]), None))
        elif head == "mov":
            ops.append(("mov", part[1], int(part[2]), int(part[3])))
        else:
            raise Bad("unknown op %s" % head)
    return tabs, links, ops


class Run:
    """The store, the lookup that keeps it affordable, and the memory of one change."""

    def __init__(self, tabs, links):
        self.tabs = tabs
        self.links = links
        self.rows = {name: {} for name in tabs}
        self.watch = {}
        self.look = {}
        for ln in links:
            self.watch.setdefault(ln[1], set()).add(ln[2])
            self.look[(ln[1], ln[2])] = {}
        self.saved = None

    # -- one way in and out of the store ------------------------------------------------
    def put(self, tab, key, row):
        old = self.rows[tab].get(key)
        if self.saved is not None and (tab, key) not in self.saved:
            self.saved[(tab, key)] = old
        if old is not None:
            for ci in self.watch.get(tab, ()):
                if old[ci] is not None:
                    self.look[(tab, ci)][old[ci]].discard(key)
        if row is None:
            self.rows[tab].pop(key, None)
            return
        self.rows[tab][key] = row
        for ci in self.watch.get(tab, ()):
            if row[ci] is not None:
                self.look[(tab, ci)].setdefault(row[ci], set()).add(key)

    def kids(self, kid, ci, vals):
        by = self.look[(kid, ci)]
        got = set()
        for val in vals:
            got |= by.get(val, set())
        return sorted(got)

    def undo(self):
        for (tab, key), row in self.saved.items():
            here = self.rows[tab].get(key)
            if here is not None:
                for ci in self.watch.get(tab, ()):
                    if here[ci] is not None:
                        self.look[(tab, ci)][here[ci]].discard(key)
                self.rows[tab].pop(key)
            if row is not None:
                self.rows[tab][key] = row
                for ci in self.watch.get(tab, ()):
                    if row[ci] is not None:
                        self.look[(tab, ci)].setdefault(row[ci], set()).add(key)


def _reach(run, kind, tab, key, new):
    """Relax until no group and no new key moves. Edges are kept, not merged, until after."""
    edge = {}
    grp = {(tab, key): 0}
    carry = {(tab, key): new}
    stamp = {}
    bars = {}
    fan = {}
    for li, ln in enumerate(run.links):
        fan.setdefault(ln[4], []).append((li, ln))
    todo = [(tab, key)]
    while todo:
        seat = todo.pop()
        mark = (grp[seat], carry.get(seat))
        if stamp.get(seat) == mark:
            continue
        stamp[seat] = mark
        ptab, pkey = seat
        for li, ln in fan.get(ptab, ()):
            act = ln[5] if kind == "out" else ln[6]
            if act == "wait":
                continue
            for ck in run.kids(ln[1], ln[2], (pkey,)):
                if act == "bar":
                    bars[(li, ck)] = ln[1]
                    continue
                under = (ln[1], ck)
                edge[(ln[1], ck, li)] = (ln[2], act, mark[1])
                if grp.get(under, -1) < mark[0] + 1:
                    grp[under] = mark[0] + 1
                if act == "drop":
                    carry.setdefault(under, None)
                    todo.append(under)
                elif act == "follow" and ln[2] == 0:
                    now = sorted((i, v) for (t, k, i), (c, a, v) in edge.items()
                                 if (t, k) == under and c == 0 and a == "follow")
                    carry[under] = now[0][1]
                    todo.append(under)
                elif under in carry:
                    todo.append(under)
    return edge, grp, carry, bars


def _melt(run, edge, kind, tab, key, new):
    """One effect per row, or one per column, taking the link declared first."""
    got = {}
    for (ktab, ck, li), (ci, act, val) in sorted(edge.items(), key=lambda e: e[0][2]):
        here = got.setdefault((ktab, ck), {"gone": None, "cols": {}})
        if act == "drop":
            if here["gone"] is None:
                here["gone"] = li
        elif ci not in here["cols"]:
            here["cols"][ci] = (act, val, li)
    here = got.setdefault((tab, key), {"gone": None, "cols": {}})
    if kind == "out":
        here["gone"] = -1
    else:
        here["cols"][0] = ("follow", new, -1)
    return got


def expect(lines):
    tabs, links, ops = _parse(lines)
    run = Run(tabs, links)
    out = []
    for op in ops:
        if op[0] == "put":
            run.saved = None
            run.put(op[1], op[2][0], op[2])
            continue
        kind, tab, key, new = op
        if key not in run.rows[tab]:
            out.append("none %s %d" % (tab, key))
            continue
        edge, grp, _carry, bars = _reach(run, kind, tab, key, new)
        if bars:
            li, ck = sorted(bars)[0]
            out.append("bar %s %s %d" % (links[li][0], bars[(li, ck)], ck))
            continue
        got = _melt(run, edge, kind, tab, key, new)
        clash = []
        for (ktab, ck), here in got.items():
            if here["gone"] is not None or 0 not in here["cols"]:
                continue
            want = here["cols"][0][1]
            if want != ck and want in run.rows[ktab]:
                clash.append((tabs[ktab][0], want, ktab))
        if clash:
            clash.sort()
            out.append("clash %s %d" % (clash[0][2], clash[0][1]))
            continue
        plan = []
        for (ktab, ck), here in got.items():
            deep = grp[(ktab, ck)]
            if here["gone"] is not None:
                plan.append((deep, tabs[ktab][0], ck, 0, ktab, 0, "drop", None, here["gone"]))
            else:
                for ci, (act, val, li) in here["cols"].items():
                    plan.append((deep, tabs[ktab][0], ck, ci, ktab, ci, act, val, li))
        plan.sort(key=lambda p: ((-p[0] if kind == "out" else p[0]), p[1], p[2], p[3]))
        run.saved = {}
        where = {}
        for _g, _at, was, _c, ktab, ci, act, val, li in plan:
            name = links[li][0] if li >= 0 else "-"
            seat = where.get((ktab, was), was)
            row = run.rows[ktab][seat]
            if act == "drop":
                run.put(ktab, seat, None)
                out.append("drop %s %d %s" % (ktab, was, name))
                continue
            col = tabs[ktab][1][ci]
            fresh = list(row)
            fresh[ci] = None if act == "clear" else val
            if act == "clear":
                run.put(ktab, seat, tuple(fresh))
                out.append("clear %s %d %s %s" % (ktab, was, col, name))
                continue
            if ci == 0:
                run.put(ktab, seat, None)
                run.put(ktab, val, tuple(fresh))
                where[(ktab, was)] = val
            else:
                run.put(ktab, seat, tuple(fresh))
            out.append("move %s %d %s %d %s" % (ktab, was, col, val, name))
        lost = {}
        for (ktab, ck), row in run.saved.items():
            if row is not None and ck not in run.rows[ktab]:
                lost.setdefault(ktab, set()).add(ck)
        stop = None
        for li, ln in enumerate(links):
            act = ln[5] if kind == "out" else ln[6]
            if act != "wait" or not lost.get(ln[4]):
                continue
            hits = run.kids(ln[1], ln[2], lost[ln[4]])
            if hits:
                stop = (li, ln[1], hits[0])
                break
        if stop is not None:
            out.append("wait %s %s %d" % (links[stop[0]][0], stop[1], stop[2]))
            run.undo()
    return out
