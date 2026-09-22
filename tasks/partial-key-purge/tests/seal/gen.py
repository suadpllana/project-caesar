"""Nonce population. Sealed: it runs as root before the worker starts and the worker never
imports it, because it tracks store state with the model while it writes statements.

Every family is shaped around one mechanism, at far above its natural rate, over a document
store: documents, revisions based on other revisions (a null revision number means "whichever
revision of that document"), and rows attached to revisions - notes, links between two
revisions, holds, watches, pins, citations, tags and annotations. Per script the declaration
order, the subset of attached tables and some modes and actions vary, so no single schema is
graded. `mixed` draws abstract random schemas for breadth. `deep` is the scale family.
"""
import random

import model

SMALL = ("plain", "half", "loop", "hold", "clear", "multi", "fork", "order", "mixed", "chain")
FAMILIES = [(f, True) for f in SMALL] + [("deep", False)]
DEEP = 3

COLS = {
    "doc": ["d"],
    "rev": ["d", "n", "bd", "bn"],
    "note": ["k", "d", "n"],
    "link": ["k", "fd", "fn", "td", "tn"],
    "hold": ["k", "d", "n"],
    "watch": ["k", "d", "n"],
    "pin": ["k", "d", "n"],
    "cite": ["k", "d", "n"],
    "tag": ["d", "n", "t"],
    "ann": ["k", "d", "n", "e", "m"],
}
KEYS = {
    "doc": ("doc_k", ["d"]),
    "rev": ("rev_k", ["d", "n"]),
    "note": ("note_k", ["k"]),
    "link": ("link_k", ["k"]),
    "hold": ("hold_k", ["k"]),
    "watch": ("watch_k", ["k"]),
    "pin": ("pin_k", ["k"]),
    "cite": ("cite_k", ["k"]),
    "tag": ("tag_k", ["d", "n", "t"]),
    "ann": ("ann_k", ["k"]),
}
# name, table, columns, key, mode, action, cleared columns
REFS = [
    ("rev_doc", "rev", ["d"], "doc_k", "simple", "noaction", []),
    ("rev_base", "rev", ["bd", "bn"], "rev_k", "partial", "cascade", []),
    ("note_on", "note", ["d", "n"], "rev_k", "partial", "cascade", []),
    ("link_from", "link", ["fd", "fn"], "rev_k", "simple", "cascade", []),
    ("link_to", "link", ["td", "tn"], "rev_k", "partial", "cascade", []),
    ("hold_on", "hold", ["d", "n"], "rev_k", "partial", "restrict", []),
    ("watch_on", "watch", ["d", "n"], "rev_k", "simple", "noaction", []),
    ("pin_on", "pin", ["d", "n"], "rev_k", "partial", "setnull", ["n"]),
    ("cite_on", "cite", ["d", "n"], "rev_k", "full", "setnull", ["n"]),
    ("tag_on", "tag", ["d", "n"], "rev_k", "simple", "setnull", []),
    ("ann_on", "ann", ["d", "n"], "rev_k", "partial", "cascade", []),
    ("ann_see", "ann", ["e", "m"], "rev_k", "partial", "noaction", []),
]
EXTRA = [
    ("pin_doc", "pin", ["d"], "doc_k", "simple", "setnull", []),
    ("cite_by", "cite", ["d", "n"], "rev_k", "partial", "noaction", []),
    ("note_see", "note", ["d", "n"], "rev_k", "full", "restrict", []),
]


class Story:
    """Rows of the document store, built so that every key and reference holds."""

    def __init__(self, rng, tabs):
        self.rng = rng
        self.tabs = tabs
        self.rows = {t: [] for t in COLS}
        self.revs = {}

    def doc(self, d):
        self.rows["doc"].append([d])
        self.revs[d] = []

    def rev(self, d, n, bd, bn):
        self.rows["rev"].append([d, n, bd, bn])
        self.revs[d].append(n)

    def pick(self, doclevel=0.0, docs=None):
        rng = self.rng
        pool = [d for d in (docs or list(self.revs)) if self.revs[d]]
        d = rng.choice(pool)
        if rng.random() < doclevel:
            return d, None
        return d, rng.choice(self.revs[d])

    def attach(self, tab, d, n, **kw):
        k = str(len(self.rows[tab]) + 1)
        if tab == "link":
            fd, fn = kw["src"]
            self.rows[tab].append([k, fd, fn, d, n])
        elif tab == "tag":
            self.rows[tab].append([d, n, kw.get("t", "x")])
        elif tab == "ann":
            e, m = kw["see"]
            self.rows[tab].append([k, d, n, e, m])
        else:
            self.rows[tab].append([k, d, n])


def rev_chain(st, rng, d, length, shape):
    """Revisions 1..length of document d; shape weights the base of each revision."""
    st.doc(d)
    kinds, weights = zip(*shape.items())
    for n in range(1, length + 1):
        kind = rng.choices(kinds, weights)[0] if n > 1 else "root"
        others = [e for e in st.revs if e != d and st.revs[e]]
        if kind == "root":
            st.rev(d, str(n), None, None)
        elif kind == "prev":
            st.rev(d, str(n), d, str(n - 1))
        elif kind == "tree":
            st.rev(d, str(n), d, str(rng.randint(1, n - 1)))
        elif kind == "self":
            st.rev(d, str(n), d, None)
        elif kind == "cross" and others:
            e = rng.choice(others)
            st.rev(d, str(n), e, rng.choice(st.revs[e]))
        elif kind == "crossdoc" and others:
            st.rev(d, str(n), rng.choice(others), None)
        elif kind == "ahead":
            st.rev(d, str(n), d, str(n + rng.randint(1, 2)))
        else:
            st.rev(d, str(n), d, str(n - 1))


def fix_ahead(st):
    """Bases that point forward at revisions that were never made fall back to the previous one."""
    have = {(r[0], r[1]) for r in st.rows["rev"]}
    for r in st.rows["rev"]:
        if r[2] is not None and r[3] is not None and (r[2], r[3]) not in have:
            r[3] = str(int(r[1]) - 1) if r[1] != "1" else None
            if r[3] is None:
                r[2] = None


def text_of(tabs, refs, rows, rng, stmts, keys=None):
    keys = keys or KEYS
    lines = ["table %s %s" % (t, " ".join(COLS[t])) for t in tabs]
    decls = []
    for t in tabs:
        kname, kcols = keys[t]
        decls.append(("key", "key %s %s %s" % (kname, t, " ".join(kcols)), t))
    for name, t, cols, key, mode, act, wipe in refs:
        line = "ref %s %s %s -> %s %s %s" % (name, t, " ".join(cols), key, mode, act)
        if wipe:
            line += " " + " ".join(wipe)
        decls.append(("ref", line, key))
    rng.shuffle(decls)
    keyline = {}
    for kind, line, _ in decls:
        if kind == "key":
            keyline[line.split()[1]] = line
    placed = set()
    for kind, line, dep in decls:
        if kind == "key":
            if line.split()[1] in placed:
                continue
            lines.append(line)
            placed.add(line.split()[1])
        else:
            if dep not in placed:
                lines.append(keyline[dep])
                placed.add(dep)
            lines.append(line)
    for t in tabs:
        for i, vals in enumerate(rows[t], 1):
            lines.append("row %s %d %s" % (t, i, " ".join("-" if v is None else v for v in vals)))
    return "\n".join(lines + stmts) + "\n"


def statements(rng, text, count, weights, focus=None):
    """Audits, dumps and deletes of present rows, tracked through the model."""
    db = model.DB(text)
    data = {t: dict(r) for t, r in db.data.items()}
    ix = model.Index(db, data)
    out = []
    kinds = ("audit", "dump", "delete")
    for _ in range(count):
        kind = rng.choices(kinds, weights)[0]
        tabs = [t for t in db.order if data[t]]
        if kind == "audit" or not tabs:
            out.append("audit")
            continue
        if kind == "dump":
            out.append("dump %s" % rng.choice(db.order))
            continue
        pool = [t for t in tabs if focus is None or t in focus] or tabs
        t = rng.choice(pool)
        ids = sorted(data[t])
        pick = [rng.choice(ids)]
        more = rng.choice((0, 0, 0, 1, 2, 3))
        if t == "rev" and more:
            d = data[t][pick[0]][0]
            same = [i for i in ids if data[t][i][0] == d and i != pick[0]]
            pick += rng.sample(same, min(len(same), more))
        elif more:
            rest = [i for i in ids if i != pick[0]]
            pick += rng.sample(rest, min(len(rest), more))
        out.append("delete %s %s" % (t, " ".join(map(str, pick))))
        gone, wiped, new, fail = model.attempt(db, ix, t, pick)
        if fail is None:
            data = {tt: dict(r) for tt, r in data.items()}
            for tt, rid in gone:
                del data[tt][rid]
            for (tt, rid), vals in new.items():
                data[tt][rid] = vals
            ix = model.Index(db, data)
    return out


def story(rng, fam):
    """One small or medium document-store script of family fam."""
    tabs = ["doc", "rev"]
    extra = []
    shape = {"root": 1, "prev": 6, "tree": 2, "self": 0, "cross": 1, "crossdoc": 0, "ahead": 0}
    ndocs, length = rng.randint(2, 4), rng.randint(2, 6)
    attach = {"note": 3, "link": 0, "hold": 0, "watch": 0, "pin": 0, "cite": 0, "tag": 0,
              "ann": 0}
    doclevel = 0.3
    nstmt, weights, focus = rng.randint(4, 8), (3, 1, 5), None
    keys = dict(KEYS)
    if fam == "plain":
        shape.update(prev=8, tree=3, cross=0)
        doclevel = 0.0
    elif fam == "half":
        shape.update(crossdoc=3, cross=2)
        attach.update(note=6, pin=1)
        doclevel = 0.6
    elif fam == "loop":
        shape.update(self=3, ahead=3, crossdoc=2, cross=2)
        attach.update(note=3, hold=1)
    elif fam == "hold":
        attach.update(hold=3, watch=3, ann=3)
        shape.update(crossdoc=1)
    elif fam == "clear":
        attach.update(pin=5, cite=2, tag=1, note=2)
        doclevel = 0.4
        if rng.random() < 0.5:
            extra.append(EXTRA[0])
        if rng.random() < 0.5:
            extra.append(EXTRA[1])
    elif fam == "multi":
        shape.update(crossdoc=2)
        attach.update(note=5, pin=2, ann=2)
        doclevel = 0.6
        focus = {"rev"}
        weights = (2, 1, 7)
    elif fam == "fork":
        attach.update(link=6, note=2, pin=1)
        shape.update(self=1, cross=2)
    elif fam == "order":
        attach.update(hold=2, watch=2, pin=2, cite=2, tag=2, ann=2)
        if rng.random() < 0.5:
            extra.append(EXTRA[2])
        weights = (1, 1, 8)
    elif fam == "chain":
        ndocs, length = rng.randint(4, 8), rng.randint(20, 60)
        shape.update(prev=12, tree=3, self=1, ahead=1, crossdoc=1, cross=1)
        attach.update(note=4, link=2, hold=1, watch=1, pin=2, cite=1, tag=1, ann=1)
        nstmt = rng.randint(3, 6)
    if fam in ("clear", "order", "chain") and rng.random() < 0.5:
        keys["tag"] = ("tag_k", ["t"])
    used = [t for t, w in attach.items() if w]
    tabs += [t for t in COLS if t in used]
    refs = [r for r in REFS if r[1] in tabs] + [r for r in extra if r[1] in tabs]
    refs = vary(rng, refs, fam)
    full = {(r[1], tuple(r[2])) for r in refs if r[4] == "full"}
    st = Story(rng, tabs)
    for i in range(ndocs):
        rev_chain(st, rng, "d%d" % (i + 1), rng.randint(1, length), shape)
    fix_ahead(st)
    total = ndocs * length
    names, weights_a = zip(*[(t, w) for t, w in attach.items() if w])
    for _ in range(rng.randint(total // 2 + 1, total + 2)):
        t = rng.choices(names, weights_a)[0]
        near = 0.0 if (t, ("d", "n")) in full else doclevel
        if t in ("watch", "tag"):
            d, n = st.pick()
        elif t == "cite":
            d, n = st.pick()
            if rng.random() < 0.15:
                d, n = None, None
        else:
            d, n = st.pick(near)
        if t == "link":
            st.attach(t, d, n, src=st.pick())
        elif t == "ann":
            st.attach(t, d, n, see=st.pick(0.0 if (t, ("e", "m")) in full else doclevel))
        elif t == "tag":
            st.attach(t, d, n, t=str(len(st.rows["tag"]) + 1))
        else:
            st.attach(t, d, n)
    base = text_of(tabs, refs, st.rows, rng, [], keys)
    return base + "\n".join(statements(rng, base, nstmt, weights, focus)) + "\n"


def vary(rng, refs, fam):
    """Swap a mode, an action or a clear list now and then; two-cascade tables stay unreferenced."""
    out = []
    for r in refs:
        name, t, cols, key, mode, act, wipe = r
        if fam in ("order", "hold", "chain") and rng.random() < 0.25:
            if name in ("note_on", "hold_on", "watch_on", "ann_see"):
                mode = rng.choice(("simple", "full", "partial"))
            if name in ("hold_on", "watch_on", "ann_see"):
                act = rng.choice(("restrict", "noaction"))
        if fam in ("clear", "order", "chain") and name == "cite_on" and rng.random() < 0.4:
            wipe = []
        out.append((name, t, cols, key, mode, act, wipe))
    return out


def abstract(rng):
    """A random schema over tables t0.. with dense values, for breadth."""
    while True:
        nt = rng.randint(1, 4)
        tabs = [("t%d" % i, ["c%d" % j for j in range(rng.randint(1, 4))]) for i in range(nt)]
        keys = []
        for name, cols in tabs:
            if rng.random() < 0.85:
                keys.append(("k" + name[1:], name, rng.sample(cols, rng.randint(1, min(2, len(cols))))))
        refs = []
        for i in range(rng.randint(1, 6) if keys else 0):
            kname, ktab, kcols = rng.choice(keys)
            ctab, ccols = rng.choice(tabs)
            if len(ccols) < len(kcols):
                continue
            cols = rng.sample(ccols, len(kcols))
            act = rng.choices(("cascade", "restrict", "noaction", "setnull"), (5, 2, 2, 3))[0]
            wipe = rng.sample(cols, rng.randint(1, len(cols))) if act == "setnull" and rng.random() < 0.6 else []
            refs.append(["r%d" % i, ctab, cols, kname, rng.choice(("simple", "full", "partial")), act, wipe])
        hit = {k[1] for k in keys if any(r[3] == k[0] for r in refs)}
        for name, _ in tabs:
            cas = [r for r in refs if r[1] == name and r[5] == "cascade"]
            if len(cas) >= 2 and name in hit:
                for r in cas[1:]:
                    r[5] = rng.choice(("restrict", "noaction", "setnull"))
        rows = dense_rows(rng, tabs, keys, refs)
        if rows:
            break
    lines = ["table %s %s" % (n, " ".join(c)) for n, c in tabs]
    decls = ["key %s %s %s" % (k[0], k[1], " ".join(k[2])) for k in keys]
    for r in refs:
        line = "ref %s %s %s -> %s %s %s" % (r[0], r[1], " ".join(r[2]), r[3], r[4], r[5])
        decls.append(line + (" " + " ".join(r[6]) if r[6] else ""))
    lines += decls
    for t, rid, vals in rows:
        lines.append("row %s %d %s" % (t, rid, " ".join("-" if v is None else v for v in vals)))
    base = "\n".join(lines) + "\n"
    return base + "\n".join(statements(rng, base, rng.randint(4, 8), (3, 1, 5))) + "\n"


def dense_rows(rng, tabs, keys, refs):
    dom = ["a", "b", "c", "d"][: rng.randint(2, 4)]
    colsof = dict(tabs)
    rows = {}
    for name, cols in tabs:
        rows[name] = {rid: [rng.choice(dom) if rng.random() < 0.8 else None for _ in cols]
                      for rid in range(1, rng.randint(1, 8) + 1)}
    for _ in range(2):
        for r in refs:
            k = next(k for k in keys if k[0] == r[3])
            if not rows[k[1]]:
                continue
            for vals in rows[r[1]].values():
                if rng.random() < 0.7:
                    pv = rows[k[1]][rng.choice(sorted(rows[k[1]]))]
                    for cc, kc in zip(r[2], k[2]):
                        v = pv[colsof[k[1]].index(kc)]
                        vals[colsof[r[1]].index(cc)] = None if rng.random() < 0.25 else v
    for _ in range(50):
        changed = False
        for kname, ktab, kcols in keys:
            idx = [colsof[ktab].index(c) for c in kcols]
            seen = set()
            for rid in sorted(rows[ktab]):
                kv = tuple(rows[ktab][rid][i] for i in idx)
                if None in kv or kv in seen:
                    del rows[ktab][rid]
                    changed = True
                else:
                    seen.add(kv)
        for r in refs:
            k = next(k for k in keys if k[0] == r[3])
            ci = [colsof[r[1]].index(c) for c in r[2]]
            ki = [colsof[k[1]].index(c) for c in k[2]]
            for rid in sorted(rows[r[1]]):
                if rid not in rows[r[1]]:
                    continue
                vals = rows[r[1]][rid]
                v = [vals[i] for i in ci]
                some = [x is not None for x in v]
                if not any(some) or (r[4] == "simple" and not all(some)):
                    continue
                if (r[4] == "full" and not all(some)) or not any(
                        all(x is None or pv[j] == x for x, j in zip(v, ki))
                        for pv in rows[k[1]].values()):
                    if rng.random() < 0.5:
                        for i in ci:
                            vals[i] = None
                    else:
                        del rows[r[1]][rid]
                    changed = True
        if not changed:
            return [(n, rid, rows[n][rid]) for n, _ in tabs for rid in sorted(rows[n])]
    return None


def deep(rng):
    """About forty thousand rows: four revision chains six to seven thousand deep, thirty short
    documents carrying most loops, pairs and cross-document bases, and rows attached throughout."""
    tabs = ["doc", "rev", "note", "link", "hold", "watch", "pin", "cite", "tag"]
    st = Story(rng, tabs)
    longs = ["d%d" % (i + 1) for i in range(4)]
    for d in longs:
        rev_chain(st, rng, d, rng.randint(6000, 7000), {"prev": 90, "tree": 10})
        for r in st.rows["rev"]:
            if r[0] == d and r[2] == d and r[3] is not None and int(r[1]) - int(r[3]) > 1:
                r[3] = str(max(int(r[1]) - rng.randint(2, 12), 1))
    shorts = ["d%d" % (i + 5) for i in range(30)]
    shape = {"root": 1, "prev": 30, "tree": 6, "self": 1, "cross": 2, "crossdoc": 2, "ahead": 1}
    for d in shorts:
        rev_chain(st, rng, d, rng.randint(50, 200), shape)
    bydoc = {}
    for r in st.rows["rev"]:
        bydoc.setdefault(r[0], []).append(r)
    for d in shorts + rng.sample(longs, 2):
        rs = bydoc[d]
        if len(rs) < 6:
            continue
        lo = len(rs) * 9 // 10 if d in longs else 1
        a = rng.randint(lo, len(rs) - 3)
        rs[a][2], rs[a][3] = d, rs[a + 1][1]
        rs[a + 1][2], rs[a + 1][3] = d, rs[a][1]
        b = rng.randint(lo, len(rs) - 1)
        if b not in (a, a + 1):
            rs[b][2], rs[b][3] = d, None
    fix_ahead(st)
    for t, count, doclevel in (("note", 4000, 0.2), ("link", 1000, 0.1), ("pin", 1000, 0.2)):
        for _ in range(count):
            d, n = st.pick(doclevel)
            if t == "link":
                st.attach(t, d, n, src=st.pick())
            else:
                st.attach(t, d, n)
    guarded = rng.sample(shorts, 6) + [rng.choice(longs)]
    for t in ("hold", "watch", "cite", "tag"):
        for _ in range(100):
            d = rng.choice(guarded)
            ns = st.revs[d]
            n = ns[rng.randint(len(ns) * 3 // 4, len(ns) - 1)]
            if t == "tag":
                st.attach(t, d, n, t=str(len(st.rows["tag"]) + 1))
            else:
                st.attach(t, d, n)
    refs = [r for r in REFS if r[1] in tabs]
    base = text_of(tabs, refs, st.rows, rng, [])
    db = model.DB(base)
    early = [i for i, r in sorted(db.data["rev"].items())
             if r[0] in longs and r[0] not in guarded and 50 < int(r[1]) < 600]
    free = [i for i, r in sorted(db.data["rev"].items())
            if r[2] is not None and r[0] not in guarded]
    heads = [i for i, r in sorted(db.data["rev"].items()) if r[2] is not None]
    stmts = ["audit", "delete rev %d" % rng.choice(early), "delete rev %d" % rng.choice(free),
             "delete rev %d" % rng.choice(heads), "dump doc", "audit"]
    return base + "\n".join(fixup(rng, base, stmts)) + "\n"


def fixup(rng, base, stmts):
    """Deletes in the deep family name rows still present when they run."""
    db = model.DB(base)
    data = {t: dict(r) for t, r in db.data.items()}
    ix = model.Index(db, data)
    out = []
    for s in stmts:
        w = s.split()
        if w[0] == "delete":
            t = w[1]
            rid = int(w[2])
            if rid not in data[t]:
                rid = rng.choice(sorted(data[t]))
            out.append("delete %s %d" % (t, rid))
            gone, wiped, new, fail = model.attempt(db, ix, t, [rid])
            if fail is None:
                data = {tt: dict(r) for tt, r in data.items()}
                for tt, x in gone:
                    del data[tt][x]
                for (tt, x), vals in new.items():
                    data[tt][x] = vals
                ix = model.Index(db, data)
        else:
            out.append(s)
    return out


def programs(seed, per):
    """(family, name, script text) for every nonce script."""
    out = []
    for fam, small in FAMILIES:
        count = per if small else DEEP
        for i in range(count):
            rng = random.Random("%s:%s:%d" % (seed, fam, i))
            if fam == "deep":
                text = deep(rng)
            elif fam == "mixed":
                text = abstract(rng)
            else:
                text = story(rng, fam)
            out.append((fam, "%s-%d" % (fam, i), text))
    return out
