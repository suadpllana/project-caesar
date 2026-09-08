"""Independent model of the whole store, written from the frozen contract.

It shares no code with `environment/app_src`: its own dictionaries, its own path walk, its own
op loop, its own accounting. Agreement with the reference is therefore agreement between two
readings of the contract rather than between two callers of one function.

Where the independence sits, stated precisely. Both sides keep a per-folder aggregate of the
bytes owned beneath a folder, because the execution limit forbids recomputing a space's total
from the tree, so that axis is closed to both and is evidence of nothing. What differs is
everything else. This decides an operation by applying it to its own store, reading every
space's total afterwards and rolling the mutations back one by one when the limit refuses,
where the reference computes per-space deltas from the effect list and never touches the store
until it has decided. This holds the links of an asset in one list sorted by age and reads the
head, where the reference keeps a map from age to folder and minimises. This rolls a checkpoint
back by restoring a whole-store snapshot, where the reference follows the runtime's journal of
inverse effects. The claim rule is applied here as a difference between two stores and there as
a filter over records the journal replays.
"""
import bisect


def blank():
    return {"dirs": {}, "itm": {}, "blob": {}, "roots": {}, "spn": {}, "lim": {}, "lnk": {},
            "bl": {}, "ag": {}, "marks": [], "age": 0, "nd": 0, "used": set()}


# --- primitive mutation, every change reversible ------------------------------------
#
# Each mutator takes (store, key, value) so one rollback list can hold them all: an entry is
# the mutator, the store, the key and the value that was there before. An operation that the
# limit refuses is undone by replaying that list backwards.

def _ent(m, key, val):
    d, nm = key
    if val is None:
        m["dirs"][d]["ent"].pop(nm, None)
    else:
        m["dirs"][d]["ent"][nm] = val


def _dir(m, d, val):
    if val is None:
        m["dirs"].pop(d, None)
    else:
        m["dirs"][d] = val


def _up(m, d, val):
    m["dirs"][d]["up"] = val


def _itm(m, a, val):
    if val is None:
        m["itm"].pop(a, None)
    else:
        m["itm"][a] = val


def _lnk(m, a, val):
    if val is None:
        m["lnk"].pop(a, None)
    else:
        m["lnk"][a] = val


def _bl(m, t, val):
    if val is None:
        m["bl"].pop(t, None)
    else:
        m["bl"][t] = val


def _ag(m, d, val):
    m["ag"][d] = val


def _lim(m, nm, val):
    m["lim"][nm] = val


def _age(m, key, val):
    m["age"] = val


def _seen(m, a, val):
    if val:
        m["used"].add(a)
    else:
        m["used"].discard(a)


def _read(fn, m, key):
    if fn is _ent:
        return m["dirs"][key[0]]["ent"].get(key[1])
    if fn is _dir:
        return m["dirs"].get(key)
    if fn is _up:
        return m["dirs"][key]["up"]
    if fn is _itm:
        return m["itm"].get(key)
    if fn is _lnk:
        return m["lnk"].get(key)
    if fn is _bl:
        return m["bl"].get(key)
    if fn is _ag:
        return m["ag"].get(key, 0)
    if fn is _lim:
        return m["lim"].get(key)
    if fn is _age:
        return m["age"]
    if fn is _seen:
        return key in m["used"]
    raise ValueError(fn)


def set_(tx, fn, m, key, new):
    tx.append((fn, m, key, _read(fn, m, key)))
    fn(m, key, new)


def undo(tx):
    while tx:
        fn, m, key, old = tx.pop()
        fn(m, key, old)


# --- reading the store --------------------------------------------------------------

def cut(p):
    return [x for x in p.split("/") if x]


def dirof(m, ps):
    if not ps:
        return None
    d = m["roots"].get(ps[0])
    if d is None:
        return None
    for nm in ps[1:]:
        e = m["dirs"][d]["ent"].get(nm)
        if e is None or e[0] != "d":
            return None
        d = e[1]
    return d


def par(m, ps):
    if len(ps) < 2:
        return None
    d = dirof(m, ps[:-1])
    if d is None:
        return None
    return d, ps[-1]


def spot(m, d):
    while d is not None:
        up = m["dirs"][d]["up"]
        if up is None:
            return m["spn"].get(d)
        d = up
    return None


def owner(m, t):
    ls = m["bl"].get(t)
    if not ls:
        return None
    return ls[0][1]


def links(m, a):
    return list(m["lnk"].get(a) or ())


def carried(m, t):
    return list(m["bl"].get(t) or ())


def total(m, nm):
    return m["ag"].get(m["roots"].get(nm), 0)


def standing(m):
    return dict((nm, total(m, nm)) for nm in m["roots"])


# --- accounting ---------------------------------------------------------------------
#
# The charge of an asset sits on the folder of its oldest link and on every folder above it,
# so a space's usage is the aggregate held at its root.

def charge(m, tx, d, n):
    if not n:
        return
    while d is not None:
        set_(tx, _ag, m, d, m["ag"].get(d, 0) + n)
        d = m["dirs"][d]["up"]


def rebuild(m, tx, t, rows):
    """Give a blob a new set of links and move its charge to wherever the oldest now sits."""
    was = owner(m, t)
    set_(tx, _bl, m, t, sorted(rows) if rows else None)
    now = owner(m, t)
    if now != was:
        sz = m["blob"].get(t, 0)
        if was is not None:
            charge(m, tx, was, -sz)
        if now is not None:
            charge(m, tx, now, sz)


def relink(m, tx, a, ls):
    rec = m["itm"].get(a)
    set_(tx, _lnk, m, a, list(ls) if ls else None)
    if rec is None:
        return
    t = rec["tag"]
    rows = [e for e in carried(m, t) if e[2] != a]
    rows.extend((g, d, a) for g, d in ls)
    rebuild(m, tx, t, rows)


def retag(m, tx, a, new):
    rec = dict(m["itm"][a])
    old = rec["tag"]
    ls = links(m, a)
    rebuild(m, tx, old, [e for e in carried(m, old) if e[2] != a])
    rec["tag"] = new
    set_(tx, _itm, m, a, rec)
    rebuild(m, tx, new, carried(m, new) + [(g, d, a) for g, d in ls])


# --- operations ---------------------------------------------------------------------

def op_mkdir(m, tx, op):
    pr = par(m, cut(op[1]))
    if pr is None:
        return "path"
    d, nm = pr
    if nm in m["dirs"][d]["ent"]:
        return "name"
    m["nd"] += 1
    new = m["nd"]
    set_(tx, _dir, m, new, {"up": d, "ent": {}})
    set_(tx, _ent, m, (d, nm), ("d", new))
    return None


def op_add(m, tx, op):
    pr = par(m, cut(op[1]))
    if pr is None:
        return "path"
    d, nm = pr
    if nm in m["dirs"][d]["ent"]:
        return "name"
    a = int(op[2])
    if a in m["used"]:
        return "id"
    if op[3] not in m["blob"]:
        return "tag"
    age = m["age"] + 1
    set_(tx, _age, m, None, age)
    set_(tx, _seen, m, a, True)
    set_(tx, _itm, m, a, {"tag": op[3], "hld": False})
    set_(tx, _ent, m, (d, nm), ("l", a, age))
    relink(m, tx, a, [(age, d)])
    return None


def op_link(m, tx, op):
    pr = par(m, cut(op[1]))
    if pr is None:
        return "path"
    d, nm = pr
    if nm in m["dirs"][d]["ent"]:
        return "name"
    a = int(op[2])
    if a not in m["itm"]:
        return "id"
    age = m["age"] + 1
    set_(tx, _age, m, None, age)
    set_(tx, _ent, m, (d, nm), ("l", a, age))
    ls = links(m, a)
    bisect.insort(ls, (age, d))
    relink(m, tx, a, ls)
    return None


def op_unlink(m, tx, op):
    pr = par(m, cut(op[1]))
    if pr is None:
        return "path"
    d, nm = pr
    e = m["dirs"][d]["ent"].get(nm)
    if e is None or e[0] != "l":
        return "path"
    a, age = e[1], e[2]
    set_(tx, _ent, m, (d, nm), None)
    left = [x for x in links(m, a) if x[0] != age]
    relink(m, tx, a, left)
    if not left and not m["itm"][a]["hld"]:
        set_(tx, _itm, m, a, None)
    return None


def op_rmdir(m, tx, op):
    ps = cut(op[1])
    d = dirof(m, ps)
    if d is None or m["dirs"][d]["up"] is None:
        return "path"
    pr = par(m, ps)
    doomed = []
    taken = {}
    stk = [d]
    while stk:
        x = stk.pop()
        doomed.append(x)
        for nm in sorted(m["dirs"][x]["ent"]):
            e = m["dirs"][x]["ent"][nm]
            if e[0] == "d":
                stk.append(e[1])
            else:
                taken.setdefault(e[1], set()).add(e[2])
                set_(tx, _ent, m, (x, nm), None)
    for a in sorted(taken):
        left = [x for x in links(m, a) if x[0] not in taken[a]]
        relink(m, tx, a, left)
        if not left and not m["itm"][a]["hld"]:
            set_(tx, _itm, m, a, None)
    set_(tx, _ent, m, (pr[0], pr[1]), None)
    for x in doomed:
        set_(tx, _dir, m, x, None)
    return None


def op_move(m, tx, op):
    sp = par(m, cut(op[1]))
    if sp is None:
        return "path"
    d0, nm0 = sp
    e = m["dirs"][d0]["ent"].get(nm0)
    if e is None:
        return "path"
    tp = par(m, cut(op[2]))
    if tp is None:
        return "path"
    d1, nm1 = tp
    if nm1 in m["dirs"][d1]["ent"]:
        return "name"
    if e[0] == "d":
        x = d1
        while x is not None:
            if x == e[1]:
                return "loop"
            x = m["dirs"][x]["up"]
        held = m["ag"].get(e[1], 0)
        set_(tx, _ent, m, (d0, nm0), None)
        set_(tx, _ent, m, (d1, nm1), e)
        charge(m, tx, d0, -held)
        set_(tx, _up, m, e[1], d1)
        charge(m, tx, d1, held)
        return None
    a, age = e[1], e[2]
    set_(tx, _ent, m, (d0, nm0), None)
    set_(tx, _ent, m, (d1, nm1), e)
    relink(m, tx, a, [(g, d1 if g == age else h) for g, h in links(m, a)])
    return None


def op_write(m, tx, op):
    a = int(op[1])
    if a not in m["itm"]:
        return "id"
    if op[2] not in m["blob"]:
        return "tag"
    retag(m, tx, a, op[2])
    return None


def op_limit(m, tx, op):
    if op[1] not in m["lim"]:
        return "path"
    set_(tx, _lim, m, op[1], int(op[2]))
    return None


def op_claim(m, tx, op):
    a = int(op[1])
    if a not in m["itm"]:
        return "id"
    if m["itm"][a]["hld"]:
        return "held"
    rec = dict(m["itm"][a])
    rec["hld"] = True
    set_(tx, _itm, m, a, rec)
    return None


def op_free(m, tx, op):
    a = int(op[1])
    if a not in m["itm"]:
        return "id"
    if not m["itm"][a]["hld"]:
        return "held"
    if links(m, a):
        rec = dict(m["itm"][a])
        rec["hld"] = False
        set_(tx, _itm, m, a, rec)
    else:
        set_(tx, _itm, m, a, None)
    return None


OPS = {"mkdir": op_mkdir, "add": op_add, "link": op_link, "unlink": op_unlink,
       "rmdir": op_rmdir, "move": op_move, "write": op_write, "limit": op_limit,
       "claim": op_claim, "free": op_free}


# --- checkpoints ---------------------------------------------------------------------
#
# A whole-store copy, restored as a whole. Claims are not part of it: an asset the rollback
# does not know about survives when a claim is open on it, and the asset records the snapshot
# does carry take back their sizes and links while keeping whatever claim stands now.

def save(m):
    return {"dirs": dict((d, {"up": v["up"], "ent": dict(v["ent"])}) for d, v in m["dirs"].items()),
            "itm": dict((a, dict(v)) for a, v in m["itm"].items()),
            "lnk": dict((a, list(v)) for a, v in m["lnk"].items()),
            "bl": dict((t, list(v)) for t, v in m["bl"].items()),
            "ag": dict(m["ag"]),
            "lim": dict(m["lim"])}


def load(m, s):
    live = m["itm"]
    m["dirs"] = dict((d, {"up": v["up"], "ent": dict(v["ent"])}) for d, v in s["dirs"].items())
    back = {}
    for a, v in s["itm"].items():
        rec = dict(v)
        rec["hld"] = live[a]["hld"] if a in live else False
        back[a] = rec
    for a, v in live.items():
        if a not in s["itm"] and v["hld"]:
            back[a] = dict(v)
    m["itm"] = back
    m["lnk"] = dict((a, list(v)) for a, v in s["lnk"].items())
    m["bl"] = dict((t, list(v)) for t, v in s["bl"].items())
    m["ag"] = dict(s["ag"])
    m["lim"] = dict(s["lim"])


# --- the op loop ---------------------------------------------------------------------

def fits(m, before):
    for nm, cap in m["lim"].items():
        now = total(m, nm)
        if now > cap and now > before.get(nm, 0):
            return False
    return True


def step(m, op, i):
    k = op[0]
    if k == "use":
        return "%d use %s" % (i, " ".join(
            "%s=%d" % (nm, total(m, nm)) for nm in sorted(m["roots"])))
    if k == "snap":
        for nm, _ in m["marks"]:
            if nm == op[1]:
                return "%d snap no name" % i
        m["marks"].append((op[1], save(m)))
        return "%d snap ok" % i
    if k == "undo":
        for j in range(len(m["marks"])):
            if m["marks"][j][0] == op[1]:
                load(m, m["marks"][j][1])
                del m["marks"][j:]
                return "%d undo ok" % i
        return "%d undo no snap" % i
    before = standing(m)
    tx = []
    why = OPS[k](m, tx, op)
    if why is None and not fits(m, before):
        why = "over"
    if why is not None:
        undo(tx)
        return "%d %s no %s" % (i, k, why)
    return "%d %s ok" % (i, k)


def run(script):
    m = blank()
    out = []
    i = 0
    for op in script:
        if op[0] == "space":
            m["nd"] += 1
            d = m["nd"]
            m["dirs"][d] = {"up": None, "ent": {}}
            m["roots"][op[1]] = d
            m["spn"][d] = op[1]
            m["lim"][op[1]] = int(op[2])
            continue
        if op[0] == "blob":
            m["blob"][op[1]] = int(op[2])
            continue
        i += 1
        out.append(step(m, op, i))
    return out


def expect(script):
    return run(script)
