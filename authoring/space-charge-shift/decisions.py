#!/usr/bin/env python3
"""The graded decisions this reference makes, as rows of features plus the choice.

Read by tools/onelinecheck.py, which searches for the shortest exact rule over these features.
The features are what the environment itself hands a submission at the moment it decides: the
shape of the path, the size of the content named, the limit of the space it lands in, how many
links the asset and the content carry, how deep the folder sits, what the store holds. The
accounting a submission builds for itself is deliberately not among them - a space's standing
usage is the thing being computed, and feeding it back in would only rediscover the stated rule.

Three questions are exported.

  allowed        Does this operation go through, or is it refused?
  charge-moves   Does it move bytes between spaces at all?
  owner-space    Which space ends up paying for the content it touches?

Run it directly to see the rows.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tasks", "space-charge-shift", "tests"))
import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

KINDS = ("mkdir", "add", "link", "unlink", "rmdir", "move", "write", "claim", "free",
         "limit", "snap", "undo", "use")


def _dir_of(m, ps):
    return model.dirof(m, ps)


def _under(m, d):
    n, stk = 0, [d]
    while stk:
        x = stk.pop()
        for e in m["dirs"][x]["ent"].values():
            if e[0] == "d":
                stk.append(e[1])
            else:
                n += 1
    return n


def _space_index(m, d):
    if d is None:
        return -1
    nm = model.spot(m, d)
    return sorted(m["roots"]).index(nm) if nm in m["roots"] else -1


def features(m, op):
    kind = op[0]
    row = {"kind": KINDS.index(kind), "links": -1, "sharers": -1, "size": -1, "cap": -1,
           "sub": -1, "depth": -1, "space": -1, "claimed": -1,
           "spaces": len(m["roots"]), "marks": len(m["marks"]), "assets": len(m["itm"])}
    a = None
    if kind in ("write", "claim", "free"):
        a = int(op[1])
    elif kind in ("add", "link"):
        a = int(op[2])
    if a is not None and a in m["itm"]:
        tag = m["itm"][a]["tag"]
        row["links"] = len(m["lnk"].get(a) or ())
        row["size"] = m["blob"].get(tag, 0)
        row["sharers"] = sum(1 for v in m["itm"].values() if v["tag"] == tag)
        row["claimed"] = 1 if m["itm"][a]["hld"] else 0
    if kind in ("mkdir", "add", "link", "unlink", "rmdir", "move"):
        ps = model.cut(op[1])
        row["depth"] = len(ps)
        d = _dir_of(m, ps)
        if d is None:
            pr = model.par(m, ps)
            d = pr[0] if pr else None
        else:
            row["sub"] = _under(m, d)
        row["space"] = _space_index(m, d)
        if row["space"] >= 0:
            row["cap"] = m["lim"][sorted(m["roots"])[row["space"]]]
    if kind == "add" and len(op) > 3:
        row["size"] = m["blob"].get(op[3], -1)
    if kind == "write" and len(op) > 2:
        row["size"] = m["blob"].get(op[2], -1)
    if kind == "limit":
        row["space"] = sorted(m["roots"]).index(op[1]) if op[1] in m["roots"] else -1
        row["cap"] = int(op[2])
    return row


def _owner_space(m, op):
    kind = op[0]
    a = None
    if kind in ("write", "claim", "free"):
        a = int(op[1])
    elif kind in ("add", "link"):
        a = int(op[2])
    elif kind in ("unlink", "move"):
        pr = model.par(m, model.cut(op[1]))
        if pr is not None:
            e = m["dirs"][pr[0]]["ent"].get(pr[1]) if pr[0] in m["dirs"] else None
            if e is not None and e[0] == "l":
                a = e[1]
    if a is None or a not in m["itm"]:
        return -1
    return _space_index(m, model.owner(m, m["itm"][a]["tag"]))


def _walk(script, allowed, moves, owner):
    m = model.blank()
    i = 0
    for op in script:
        if op[0] == "space":
            m["nd"] += 1
            m["dirs"][m["nd"]] = {"up": None, "ent": {}}
            m["roots"][op[1]] = m["nd"]
            m["spn"][m["nd"]] = op[1]
            m["lim"][op[1]] = int(op[2])
            continue
        if op[0] == "blob":
            m["blob"][op[1]] = int(op[2])
            continue
        i += 1
        row = features(m, op)
        before = model.standing(m)
        line = model.step(m, op, i)
        after = model.standing(m)
        if op[0] != "use":
            allowed.append((row, line.endswith(" ok")))
            moves.append((row, before != after))
            owner.append((row, _owner_space(m, op)))


def samples():
    allowed, moves, owner = [], [], []
    for name in cases.ORDER:
        _walk(cases.ops(name), allowed, moves, owner)
    for fam, name, lines in gen.programs("onelineprobe", 3):
        if fam == "wide":
            continue
        _walk(gen.ops(lines), allowed, moves, owner)
    return {"allowed": allowed, "charge-moves": moves, "owner-space": owner}


if __name__ == "__main__":
    for name, rows in sorted(samples().items()):
        print("%s: %d rows" % (name, len(rows)))
        for feat, label in rows[:3]:
            print("   ", feat, "->", label)
