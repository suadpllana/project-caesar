#!/usr/bin/env python3
"""The reference against the sealed definition, on random operation streams.

The work budget in tests/gt.json is taken from the reference, which is a claim that no
correct merge needs to do more than the reference does. That claim is only worth anything
if the reference is correct everywhere rather than on the fourteen streams somebody chose,
so build_gt.py refuses to write a ground truth without a clean run of this.

A stream is a random walk over sets, deletes, adjusts, flushes, pins, unpins and merges.
The reference runs it through the real engine; oracle.Truth runs the same stream keeping
every record ever written and never merging anything. Every read the store can answer -
each key at each read point, after every job and at the end - has to agree.

Usage:
    python3 authoring/fuzz.py [streams] [seed]
"""

from __future__ import annotations

import random
import shutil
import subprocess
import sys
import json
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "tests"))

import oracle  # noqa: E402

CHILD = r'''
import json, os, sys
sys.path.insert(0, os.environ["APP"])
from merge import drv
data = json.load(open(os.environ["STREAMS"]))
out = []
for sc in data:
    for m in list(sys.modules):
        if m.split(".")[0] in ("merge", "seg"):
            sys.modules.pop(m, None)
    from merge import drv as d2
    try:
        rep = d2.Drv(sc["cfg"]).run(sc["ops"])
        out.append({"view": rep["view"], "snaps": rep["snaps"],
                    "reads": rep["reads"], "writes": rep["writes"],
                    "probes": rep["probes"]})
    except Exception as e:
        out.append({"err": repr(e)})
json.dump(out, open(os.environ["OUT"], "w"))
'''


def stream(rng: random.Random) -> dict:
    keys = list(range(1, rng.choice([3, 4, 6, 9]) + 1))
    ops = []
    pins = 0
    for _ in range(rng.randint(8, 44)):
        r = rng.random()
        if r < 0.44:
            k = rng.choice(keys)
            w = rng.random()
            if w < 0.45:
                ops.append({"op": "put", "k": k, "v": rng.randint(-30, 90)})
            elif w < 0.7:
                ops.append({"op": "add", "k": k, "d": rng.choice([-6, -3, -1, 0, 1, 2, 4, 7])})
            else:
                ops.append({"op": "del", "k": k})
        elif r < 0.68:
            ops.append({"op": "flush"})
        elif r < 0.78:
            ops.append({"op": "pin"})
            pins += 1
        elif r < 0.84 and pins:
            i = rng.randrange(pins)
            ops.append({"op": "unpin", "i": i})
            pins -= 1
        else:
            ops.append({"op": "merge"})
    ops.append({"op": "merge"})
    return {"cfg": {"tier": rng.choice([2, 3, 4])}, "ops": ops}


def main(argv: list[str]) -> int:
    n = int(argv[1]) if len(argv) > 1 else 400
    seed = int(argv[2]) if len(argv) > 2 else 20260814
    rng = random.Random(seed)
    streams = [stream(rng) for _ in range(n)]

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        app = tmp / "app"
        shutil.copytree(TASK / "environment" / "app_src", app,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copyfile(TASK / "solution" / "ref" / "plan.py", app / "merge" / "plan.py")
        sp = tmp / "streams.json"
        sp.write_text(json.dumps(streams))
        out = tmp / "out.json"
        proc = subprocess.run(
            [sys.executable, "-c", CHILD], capture_output=True, text=True,
            env={"APP": str(app), "STREAMS": str(sp), "OUT": str(out),
                 "PYTHONDONTWRITEBYTECODE": "1", "SYSTEMROOT": "C:\\Windows",
                 "PATH": "/usr/bin:/bin"})
        if not out.is_file():
            print(proc.stdout[-3000:], proc.stderr[-3000:])
            return 1
        got = json.loads(out.read_text())

    bad = 0
    reads = 0
    for sc, g in zip(streams, got):
        t = oracle.Truth(sc["cfg"])
        t.run(sc["ops"])
        want = t.map()
        wsnaps = [[list(x) for x in m] for m in t.snaps]
        if "err" in g:
            bad += 1
            print("RAISED", g["err"])
            print(json.dumps(sc))
            continue
        reads += g["reads"]
        if g["view"] != want or g["snaps"] != wsnaps:
            bad += 1
            print("MISMATCH")
            print(json.dumps(sc))
            for a, b in zip(g["view"], want):
                if a != b:
                    print("  got %r want %r" % (a, b))
                    break
            for i, (a, b) in enumerate(zip(g["snaps"], wsnaps)):
                if a != b:
                    print("  snapshot %d differs" % i)
                    break
            if bad > 3:
                break

    print("%d streams, %d records pulled, %d mismatches" % (len(streams), reads, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
