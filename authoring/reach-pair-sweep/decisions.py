"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are
deliberately the raw ones - what is in a frame slot or the global table, how many fields an
object has, which space it is in, whether it carries a finalizer, what the queue and the ran-set
already hold, whether a remembered-set entry names it and whether that entry is still accurate.
Nothing derived is offered, because the derivation is the task: a feature called "is reached"
would answer the question it is supposed to pose.

The verdict to want is that at least one graded quantity has no short rule. Release cannot have
one, because whether an object survives depends on a fixed point over the whole heap rather than
on any property of the object itself.

    python authoring/reach-pair-sweep/decisions.py
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "reach-pair-sweep"
sys.path.insert(0, str(TASK / "tests"))

import gen  # noqa: E402
import model  # noqa: E402


def _facts(st):
    objs = st["objs"]
    slotted = {v for fr in st["frames"] for v in fr.values() if v is not None}
    globbed = {v for v in st["globs"].values() if v is not None}
    handled = set(st["handles"])
    pointed = {}
    for o in objs.values():
        for v in o["flds"].values():
            if v is not None:
                pointed[v] = pointed.get(v, 0) + 1
    keys = {k for k, _ in st["pairs"]}
    values = {v for _, v in st["pairs"]}
    named_by_rset, accurate_rset = set(), set()
    for src, fld, was in st["rset"]:
        named_by_rset.add(was)
        if src in objs and objs[src]["flds"].get(fld) == was:
            accurate_rset.add(was)
    weak_on = {}
    for w in st["weak"].values():
        weak_on[w[0]] = weak_on.get(w[0], 0) + 1
    return (objs, slotted, globbed, handled, pointed, keys, values,
            named_by_rset, accurate_rset, weak_on)


def samples():
    released, queued, promoted, cleared = [], [], [], []
    for _, _, lines in gen.programs("decisions", 12):
        ops = gen.ops(lines)
        if len(ops) > 200:
            continue
        for idx, op in enumerate(ops):
            if op[0] not in ("collect", "collectfull"):
                continue
            full = op[0] == "collectfull"
            st = model._run(ops[:idx])[1]
            (objs, slotted, globbed, handled, pointed, keys, values,
             named_by_rset, accurate_rset, weak_on) = _facts(st)
            before = set(objs)
            spaces = {i: objs[i]["space"] for i in objs}
            ages = {i: objs[i]["age"] for i in objs}

            after_out, after_st = model._run(ops[:idx + 1])[0:2]
            gone = before - set(after_st["objs"])
            fin_now = {int(l.split()[1]) for l in after_out if l.startswith("fin ")}
            pro_now = {int(l.split()[1]) for l in after_out if l.startswith("pro ")}
            wiped = {l.split()[1] for l in after_out if l.startswith("clr ")}

            for i in sorted(before):
                row = {
                    "full_collection": int(full),
                    "in_slot": int(i in slotted),
                    "in_global": int(i in globbed),
                    "in_handle": int(i in handled),
                    "n_fields": len(objs[i]["flds"]),
                    "pointed_at": pointed.get(i, 0),
                    "is_pair_key": int(i in keys),
                    "is_pair_value": int(i in values),
                    "has_fin": int(objs[i]["fin"] is not None),
                    "already_ran": int(i in st["done"]),
                    "already_queued": int(i in st["queue"]),
                    "in_old_space": int(spaces[i] == model.OLD),
                    "age": ages[i],
                    "pinned": int(objs[i]["pins"] > 0),
                    "named_by_rset": int(i in named_by_rset),
                    "rset_still_accurate": int(i in accurate_rset),
                    "weak_on_it": weak_on.get(i, 0),
                }
                released.append((row, int(i in gone)))
                queued.append((dict(row), int(i in fin_now)))
                promoted.append((dict(row), int(i in pro_now)))

            for name in sorted(st["weak"]):
                tgt = st["weak"][name][0]
                cleared.append(({
                    "full_collection": int(full),
                    "target_in_slot": int(tgt in slotted),
                    "target_in_global": int(tgt in globbed),
                    "target_pointed_at": pointed.get(tgt, 0),
                    "target_has_fin": int(tgt in objs and objs[tgt]["fin"] is not None),
                    "target_is_pair_value": int(tgt in values),
                    "target_in_old_space": int(tgt in objs and spaces[tgt] == model.OLD),
                    "target_queued": int(tgt in st["queue"]),
                    "target_gone": int(tgt not in objs),
                    "already_cleared": int(st["weak"][name][1]),
                }, int(name in wiped)))

    return {"released": released, "queued": queued,
            "promoted": promoted, "cleared": cleared}


if __name__ == "__main__":
    got = samples()
    for k, v in sorted(got.items()):
        print("%-10s %5d rows, %d positive" % (k, len(v), sum(1 for _, y in v if y)))
