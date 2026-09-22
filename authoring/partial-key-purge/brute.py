"""Brute-force transcription of the frozen contract. Authoring only, never ships.

Every rule is written the way the contract states it, with no index and no cleverness:
match sets by scanning, the removed set by iterating the closure rule until nothing changes,
the end state checked row by row over a full copy of the store. It is slow on purpose and is the
semantic oracle that the sealed model, the reference and the correct variants are checked
against on small stores.
"""
import copy
import sys


def read(text):
    tabs, keys, refs, decls = {}, {}, {}, []
    order = []
    data = {}
    stmts = []
    for raw in text.split("\n"):
        w = raw.split()
        if not w or w[0].startswith("#"):
            continue
        op = w[0]
        if op == "table":
            tabs[w[1]] = w[2:]
            order.append(w[1])
            data[w[1]] = {}
        elif op == "key":
            cols = [tabs[w[2]].index(c) for c in w[3:]]
            keys[w[1]] = {"name": w[1], "tab": w[2], "cols": cols, "pos": len(decls)}
            decls.append(w[1])
        elif op == "ref":
            a = w.index("->")
            cols = [tabs[w[2]].index(c) for c in w[3:a]]
            key = w[a + 1]
            mode, act = w[a + 2], w[a + 3]
            wipe = [tabs[w[2]].index(c) for c in w[a + 4:]] or list(cols)
            refs[w[1]] = {"name": w[1], "tab": w[2], "cols": cols, "key": key, "mode": mode,
                          "act": act, "wipe": wipe if act == "setnull" else [],
                          "pos": len(decls)}
            decls.append(w[1])
        elif op == "row":
            data[w[1]][int(w[2])] = [None if v == "-" else v for v in w[3:]]
        elif op == "delete":
            stmts.append(("delete", w[1], [int(x) for x in w[2:]]))
        elif op == "dump":
            stmts.append(("dump", w[1], []))
        elif op == "audit":
            stmts.append(("audit", None, []))
        else:
            raise ValueError(raw)
    return {"tabs": tabs, "order": order, "keys": keys, "refs": refs, "decls": decls,
            "data": data, "stmts": stmts}


def status(ref, vals):
    v = [vals[i] for i in ref["cols"]]
    some = [x is not None for x in v]
    if not any(some):
        return "inert"
    if ref["mode"] == "simple" and not all(some):
        return "inert"
    if ref["mode"] == "full" and not all(some):
        return "broken"
    return "live"


def matches(db, ref, vals, data):
    key = db["keys"][ref["key"]]
    v = [vals[i] for i in ref["cols"]]
    out = set()
    for pid, pv in data[key["tab"]].items():
        if all(x is None or pv[k] == x for x, k in zip(v, key["cols"])):
            out.add(pid)
    return out


def attempt(db, data, tab, ids):
    """What `delete tab ids` does to `data`: (removed, cleared, failure, end data)."""
    refs_of = {t: [r for r in db["refs"].values() if r["tab"] == t] for t in db["order"]}
    keys_of = {t: [k for k in db["keys"].values() if k["tab"] == t] for t in db["order"]}
    before = {}
    for t in db["order"]:
        for c, vals in data[t].items():
            for r in refs_of[t]:
                if status(r, vals) == "live":
                    before[(t, c, r["name"])] = matches(db, r, vals, data)
    gone = {(tab, i) for i in ids}
    grew = True
    while grew:
        grew = False
        for (t, c, rn), ms in before.items():
            r = db["refs"][rn]
            ktab = db["keys"][r["key"]]["tab"]
            if (r["act"] == "cascade" and (t, c) not in gone and ms
                    and all((ktab, p) in gone for p in ms)):
                gone.add((t, c))
                grew = True
    lost = []
    for (t, c, rn), ms in before.items():
        r = db["refs"][rn]
        ktab = db["keys"][r["key"]]["tab"]
        if ms and all((ktab, p) in gone for p in ms):
            lost.append((t, c, rn))
    fails = []
    for t, c, rn in lost:
        if db["refs"][rn]["act"] == "restrict":
            fails.append((db["refs"][rn]["pos"], c))
    end = copy.deepcopy(data)
    for t, c in gone:
        del end[t][c]
    wiped = set()
    for t, c, rn in lost:
        r = db["refs"][rn]
        if r["act"] == "setnull" and (t, c) not in gone:
            for i in r["wipe"]:
                end[t][c][i] = None
            wiped.add((t, c))
    for t in db["order"]:
        for c, vals in end[t].items():
            for r in refs_of[t]:
                st = status(r, vals)
                if st == "broken" or (st == "live" and not matches(db, r, vals, end)):
                    fails.append((r["pos"], c))
            for k in keys_of[t]:
                if any(vals[i] is None for i in k["cols"]):
                    fails.append((k["pos"], c))
    fail = None
    if fails:
        pos = min(p for p, _ in fails)
        fail = (db["decls"][pos], min(c for p, c in fails if p == pos))
    return gone, wiped, fail, end


def run(text):
    db = read(text)
    data = db["data"]
    out = []
    for op, tab, ids in db["stmts"]:
        if op == "delete":
            gone, wiped, fail, end = attempt(db, data, tab, ids)
            if fail:
                out.append("refused %s %d" % fail)
            else:
                data = end
                out.append("ok %d %d" % (len(gone), len(wiped)))
        elif op == "dump":
            for rid in sorted(data[tab]):
                vals = ["-" if v is None else v for v in data[tab][rid]]
                out.append(" ".join([tab, str(rid)] + vals))
        else:
            for t in db["order"]:
                for rid in sorted(data[t]):
                    gone, wiped, fail, _ = attempt(db, data, t, [rid])
                    out.append("%s %d %d %d %s" % (t, rid, len(gone), len(wiped),
                                                   "held" if fail else "ok"))
    return out


if __name__ == "__main__":
    sys.stdout.write("".join(line + "\n" for line in run(open(sys.argv[1]).read())))
