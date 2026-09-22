"""Search for the smallest session that separates each wrong reading, and pick fences.

Programs are generated small on purpose (short bodies, few helpers) so the enumerated case
for each reading is as close to hand-sized as the generator allows. A case is truncated
right after the first line on which the reading differs from the model. Writes cases.json.
"""
import copy
import json
import os
import random
import sys

from lab import forge, model, HERE
import bench
import fastbench
import readings as make_readings

PER = int(sys.argv[1]) if len(sys.argv) > 1 else 500
rng = random.Random(8080)


def small(knobs):
    k = copy.deepcopy(knobs)
    k["min_len"] = 2
    k["max_len"] = min(k.get("max_len", 6), 4)
    k["max_help"] = min(k.get("max_help", 4), 3)
    return k


pop = []
for fam, knobs in forge.FAMILIES.items():
    sk = small(knobs)
    for _ in range(PER):
        text, tape, _ = forge.build(rng, sk)
        cmds, out = forge.script(text, tape, rng, n_cmds=(6, 16), weights=forge.WEIGHTS.get(fam))
        pop.append({"family": fam, "image": text, "tape": tape, "cmds": cmds, "want": out})
print("population", len(pop), flush=True)


def truncate(s, k):
    t = dict(s)
    t["cmds"] = s["cmds"][:k + 1]
    t["want"] = model.play(s["image"], s["tape"], t["cmds"])
    return t


def weight(s, k):
    return len(s["image"].splitlines()) * 4 + k


cases = {}
for name, (what, _) in make_readings.READINGS.items():
    res = fastbench.run(os.path.join(HERE, "readings", name), pop)
    best = None
    for i in bench.compare(pop, res):
        k = next((j for j, (a, b) in enumerate(zip(pop[i]["want"], res[i]["got"])) if a != b),
                 min(len(pop[i]["want"]), len(res[i]["got"])))
        w = weight(pop[i], k)
        if best is None or w < best[0]:
            best = (w, i, k)
    if best is None:
        print("%-26s NO CASE" % name, flush=True)
        continue
    w, i, k = best
    case = truncate(pop[i], k)
    case["reading"] = name
    case["believes"] = what
    cases[name] = case
    print("%-26s %4d image lines, %2d commands (%s)" % (name, len(case["image"].splitlines()),
                                                        len(case["cmds"]), case["family"]), flush=True)

# Re-check every case separates its own reading after truncation.
for name, case in cases.items():
    res = fastbench.run(os.path.join(HERE, "readings", name), [case])
    assert res[0]["got"] != case["want"] or res[0]["err"], name
    ref = fastbench.run("reference", [case])
    assert ref[0]["got"] == case["want"], name

fences = [s for s in pop if s["family"] == "plain" and len(s["want"]) >= 8]
fences.sort(key=lambda s: len(s["image"].splitlines()))
json.dump({"cases": cases, "fences": fences[:6]}, open(os.path.join(HERE, "cases.json"), "w"))
print("wrote %d cases and %d fences" % (len(cases), len(fences[:6])))
