"""Broad random scripts for cross-checking implementations. Authoring only.

Unlike tests/gen.py, which shapes its families around the graded mechanisms, this draws random
schemas with every structure the contract allows - several setnull references on one table,
clear lists overlapping other references, cleared key columns, self references, loops, rows with
two cascade references - and consistent random rows over a small value domain, so that matches
are dense. Statements are tracked against the brute force so every delete names present rows.
"""
import random
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import brute  # noqa: E402

MODES = ("simple", "full", "partial")
ACTS = ("cascade", "restrict", "noaction", "setnull")


def schema(rng):
    nt = rng.randint(1, 4)
    tabs = []
    for t in range(nt):
        ncol = rng.randint(1, 4)
        tabs.append(("t%d" % t, ["c%d" % i for i in range(ncol)]))
    keys = []
    for name, cols in tabs:
        if rng.random() < 0.85:
            k = rng.randint(1, min(2, len(cols)))
            keys.append(("k%s" % name[1:], name, rng.sample(cols, k)))
        if rng.random() < 0.2 and len(cols) >= 2:
            keys.append(("j%s" % name[1:], name, rng.sample(cols, rng.randint(1, len(cols)))))
    refs = []
    if keys:
        for i in range(rng.randint(1, 6)):
            kname, ktab, kcols = rng.choice(keys)
            ctab, ccols = rng.choice(tabs)
            if len(ccols) < len(kcols):
                continue
            cols = rng.sample(ccols, len(kcols))
            mode = rng.choice(MODES)
            act = rng.choices(ACTS, weights=(5, 2, 2, 3))[0]
            wipe = []
            if act == "setnull" and rng.random() < 0.6:
                wipe = rng.sample(cols, rng.randint(1, len(cols)))
            refs.append(["r%d" % i, ctab, cols, kname, mode, act, wipe])
    referenced = {ktab for kname, ktab, kcols in keys if any(r[3] == kname for r in refs)}
    for name, _ in tabs:
        cas = [r for r in refs if r[1] == name and r[5] == "cascade"]
        if len(cas) >= 2 and name in referenced:
            for r in cas[1:]:
                r[5] = rng.choice(("restrict", "noaction", "setnull"))
    return tabs, keys, refs


def text_of(tabs, keys, refs, rows, stmts):
    out = []
    for name, cols in tabs:
        out.append("table %s %s" % (name, " ".join(cols)))
    decls = [("key", k) for k in keys] + [("ref", r) for r in refs]
    for kind, d in decls:
        if kind == "key":
            out.append("key %s %s %s" % (d[0], d[1], " ".join(d[2])))
        else:
            line = "ref %s %s %s -> %s %s %s" % (d[0], d[1], " ".join(d[2]), d[3], d[4], d[5])
            if d[6]:
                line += " " + " ".join(d[6])
            out.append(line)
    for t, rid, vals in rows:
        out.append("row %s %d %s" % (t, rid, " ".join("-" if v is None else v for v in vals)))
    out.extend(stmts)
    return "\n".join(out) + "\n"


def consistent_rows(rng, tabs, keys, refs, per):
    """Random rows over a small domain, then repaired until every key and reference holds."""
    dom = ["a", "b", "c", "d"][: rng.randint(2, 4)]
    colsof = dict(tabs)
    rows = {}
    for name, cols in tabs:
        rows[name] = {}
        for rid in range(1, rng.randint(1, per) + 1):
            rows[name][rid] = [rng.choice(dom) if rng.random() < 0.8 else None for _ in cols]
    # copy key values into reference columns so matches are common
    for _ in range(2):
        for r in refs:
            name, ccols, kname = r[1], r[2], r[3]
            k = next(k for k in keys if k[0] == kname)
            ktab, kcols = k[1], k[2]
            if not rows[ktab]:
                continue
            for rid, vals in rows[name].items():
                if rng.random() < 0.7:
                    pv = rows[ktab][rng.choice(list(rows[ktab]))]
                    for cc, kc in zip(ccols, kcols):
                        v = pv[colsof[ktab].index(kc)]
                        if rng.random() < 0.25:
                            v = None
                        vals[colsof[name].index(cc)] = v
    changed = True
    guard = 0
    while changed and guard < 50:
        guard += 1
        changed = False
        for kname, ktab, kcols in keys:
            idx = [colsof[ktab].index(c) for c in kcols]
            seen = set()
            for rid in sorted(rows[ktab]):
                vals = rows[ktab][rid]
                kv = tuple(vals[i] for i in idx)
                if None in kv or kv in seen:
                    del rows[ktab][rid]
                    changed = True
                else:
                    seen.add(kv)
        for r in refs:
            name, ccols, kname, mode = r[1], r[2], r[3], r[4]
            k = next(k for k in keys if k[0] == kname)
            ktab, kcols = k[1], k[2]
            ci = [colsof[name].index(c) for c in ccols]
            ki = [colsof[ktab].index(c) for c in kcols]
            for rid in sorted(rows[name]):
                if rid not in rows[name]:
                    continue
                vals = rows[name][rid]
                v = [vals[i] for i in ci]
                some = [x is not None for x in v]
                if not any(some) or (mode == "simple" and not all(some)):
                    continue
                if mode == "full" and not all(some):
                    if rng.random() < 0.5:
                        for i in ci:
                            vals[i] = None
                    else:
                        del rows[name][rid]
                    changed = True
                    continue
                hit = any(all(x is None or pv[j] == x for x, j in zip(v, ki))
                          for pv in rows[ktab].values())
                if not hit:
                    if rng.random() < 0.5:
                        for i in ci:
                            vals[i] = None
                    else:
                        del rows[name][rid]
                    changed = True
    out = []
    for name, _ in tabs:
        for rid in sorted(rows[name]):
            out.append((name, rid, rows[name][rid]))
    return out, guard < 50


def script(seed, per=8, nstmt=6):
    rng = random.Random(seed)
    while True:
        tabs, keys, refs = schema(rng)
        rows, ok = consistent_rows(rng, tabs, keys, refs, per)
        if ok and rows:
            break
    base = text_of(tabs, keys, refs, rows, [])
    db = brute.read(base)
    data = db["data"]
    stmts = []
    for _ in range(nstmt):
        roll = rng.random()
        present = [(t, rid) for t in db["order"] for rid in sorted(data[t])]
        if roll < 0.3 or not present:
            stmts.append("audit")
        elif roll < 0.45:
            stmts.append("dump %s" % rng.choice(db["order"]))
        else:
            t, rid = rng.choice(present)
            same = [r for tt, r in present if tt == t and r != rid]
            ids = [rid] + rng.sample(same, min(len(same), rng.choice((0, 0, 1, 2))))
            stmts.append("delete %s %s" % (t, " ".join(map(str, ids))))
            gone, wiped, fail, end = brute.attempt(db, data, t, ids)
            if not fail:
                data = end
    return base + "\n".join(stmts) + "\n"


if __name__ == "__main__":
    sys.stdout.write(script(int(sys.argv[1])))
