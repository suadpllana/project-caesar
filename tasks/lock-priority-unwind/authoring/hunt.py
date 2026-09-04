#!/usr/bin/env python3
"""Find a small task set that separates a given reading from the sealed model. Authoring only.

When a reading survives the whole written set, the fix is not to argue about it: draw task sets
of the shape it should die on, keep the ones where the reading disagrees and the reference
agrees, and take the smallest. That case becomes a written scenario, so the misreading is named
rather than surfacing as a handful of drawn sets.

Usage: python3 authoring/hunt.py <reading> [tries] [seed]
"""
from __future__ import annotations
import json, random, sys, tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "authoring"))
import oracle, separation  # noqa: E402

FIELDS = ("trace", "prio", "ev", "done", "ids", "ticks")


def draw(rng):
    nt = rng.randint(4, 6)
    nm = rng.randint(1, 2)
    bases = rng.sample(range(1, 12), nt)
    tasks = []
    for i in range(nt):
        prog = []
        held = []
        if rng.random() < 0.85:
            m0 = rng.randint(1, nm)
            prog.append(["lock", m0, -1 if rng.random() < 0.6 else rng.randint(2, 8)])
            held.append(m0)
            prog.append(["run", rng.randint(2, 7)])
        for _ in range(rng.randint(1, 3)):
            pick = rng.random()
            if pick < 0.5 and len(held) < 2:
                m = rng.randint(1, nm)
                if m not in held:
                    prog.append(["lock", m, -1 if rng.random() < 0.6 else rng.randint(2, 8)])
                    held.append(m)
                    prog.append(["run", rng.randint(2, 5)])
            elif pick < 0.8 and held:
                prog.append(["unlock", held.pop(0)])
                prog.append(["run", rng.randint(1, 4)])
            else:
                prog.append(["run", rng.randint(1, 5)])
        for m in held:
            prog.append(["unlock", m])
        prog.append(["run", rng.randint(1, 3)])
        tasks.append({"id": i + 1, "base": bases[i],
                      "start": rng.choice([0, 0, 1, 2, 3, 4, 5, 7]), "prog": prog})
    return {"name": "hunt", "tasks": tasks}


def size(sc):
    return sum(len(t["prog"]) for t in sc["tasks"]) + len(sc["tasks"])


def main(argv):
    name = argv[1]
    tries = int(argv[2]) if len(argv) > 2 else 600
    seed = int(argv[3]) if len(argv) > 3 else 11
    rng = random.Random(seed)
    cfg = json.loads((TASK / "tests" / "sched.json").read_text())
    sets = [draw(rng) for _ in range(tries)]
    want = [oracle.expect(dict(cfg), sc) for sc in sets]
    with tempfile.TemporaryDirectory() as tmp:
        bad = separation.drive(separation.resolve(name), sets, tmp)
    with tempfile.TemporaryDirectory() as tmp:
        good = separation.drive(separation.resolve("solution"), sets, tmp)
    hits = []
    for sc, w, b, g in zip(sets, want, bad, good):
        if "err" in b or "err" in g:
            continue
        if any(g[f] != w[f] for f in FIELDS):
            continue
        if any(b[f] != w[f] for f in FIELDS):
            hits.append(sc)
    hits.sort(key=size)
    print("%s: %d of %d drawn shapes separate it" % (name, len(hits), tries))
    for sc in hits[:2]:
        print(json.dumps(sc["tasks"], indent=1))
        print("---")
    return 0 if hits else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
