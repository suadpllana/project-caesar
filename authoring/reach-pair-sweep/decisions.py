"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are
deliberately the raw ones - what is in a frame slot, how many fields an object has, whether it
is named as a pair key, whether it carries a finalizer, what the queue and the ran-set already
hold. Nothing derived is offered, because the derivation is the task: a feature called
"is reached" would answer the question it is supposed to pose.

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


def _features(ops, upto):
    """Heap state after ops[:upto], as plain readable facts."""
    _, st = model._run(ops[:upto])
    obj, frames, pairs = st["obj"], st["frames"], st["pairs"]
    slotted = {v for fr in frames for v in fr.values() if v is not None}
    pointed = {}
    for i, o in obj.items():
        for v in o["fl"].values():
            if v is not None:
                pointed[v] = pointed.get(v, 0) + 1
    keys = {k for k, _ in pairs}
    values = {v for _, v in pairs}
    weak_on = {}
    for name, w in st["weak"].items():
        weak_on[w[0]] = weak_on.get(w[0], 0) + 1
    return st, obj, slotted, pointed, keys, values, weak_on


def samples():
    released, queued, cleared = [], [], []
    for _, _, lines in gen.programs("decisions", 25):
        ops = gen.ops(lines)
        for idx, op in enumerate(ops):
            if op[0] != "collect":
                continue
            st, obj, slotted, pointed, keys, values, weak_on = _features(ops, idx)
            before = set(obj)
            after_out, after_st = model._run(ops[:idx + 1])
            gone = before - set(after_st["obj"])
            fresh = {int(ln.split()[1]) for ln in after_out if ln.startswith("fin ")}
            wiped = {ln.split()[1] for ln in after_out if ln.startswith("clr ")}

            for i in sorted(before):
                row = {
                    "in_slot": int(i in slotted),
                    "n_fields": len(obj[i]["fl"]),
                    "pointed_at": pointed.get(i, 0),
                    "is_pair_key": int(i in keys),
                    "is_pair_value": int(i in values),
                    "has_fin": int(obj[i]["fz"] is not None),
                    "already_ran": int(i in st["ran"]),
                    "already_queued": int(i in st["queue"]),
                    "weak_on_it": weak_on.get(i, 0),
                }
                released.append((row, int(i in gone)))
                queued.append((dict(row), int(i in fresh)))

            for name in sorted(st["weak"]):
                tgt, done = st["weak"][name]
                cleared.append(({
                    "target_in_slot": int(tgt in slotted),
                    "target_pointed_at": pointed.get(tgt, 0),
                    "target_has_fin": int(tgt in obj and obj[tgt]["fz"] is not None),
                    "target_is_pair_value": int(tgt in values),
                    "target_queued": int(tgt in st["queue"]),
                    "target_gone": int(tgt not in obj),
                    "already_cleared": int(done),
                }, int(name in wiped)))

    return {"released": released, "queued": queued, "cleared": cleared}


if __name__ == "__main__":
    got = samples()
    for k, v in sorted(got.items()):
        ones = sum(1 for _, y in v if y)
        print("%-10s %5d rows, %d positive" % (k, len(v), ones))
