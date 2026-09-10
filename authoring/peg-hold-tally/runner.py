"""Run generated programs through a staged tree and print the traces as JSON.

Usage: python runner.py <tree-dir> < spec.json
Spec: [[family, seed, n, slots, vols], ...]
"""
import json
import pathlib
import sys

tree = sys.argv[1]
sys.path.insert(0, tree)
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent
                       / "tasks" / "peg-hold-tally" / "tests"))

import gen  # noqa: E402
from store import ops  # noqa: E402
from store.host import Host  # noqa: E402

spec = json.load(sys.stdin)
out = []
for fam, seed, n, slots, vols in spec:
    lines = gen.small(fam, seed, n, slots, vols)
    h = Host()
    acc = []
    try:
        for line in lines:
            ops.ex(h, tuple(line.split()), acc)
        out.append(acc)
    except Exception as exc:  # noqa: BLE001
        out.append(["ERROR %s: %s" % (type(exc).__name__, exc)])
json.dump(out, sys.stdout)
