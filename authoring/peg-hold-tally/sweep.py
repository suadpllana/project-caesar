"""Three-way sweep: definitional oracle, sealed model, staged reference."""
import json
import subprocess
import sys

from stage import TESTS, stage

sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS / "seal"))

import gen  # noqa: E402
import model  # noqa: E402
import slow  # noqa: E402

fams = list(gen.SMALL)
shapes = [(40, 4, 1), (60, 6, 2), (90, 8, 2), (120, 5, 3), (200, 10, 3), (60, 3, 1)]

def build(count):
    out = []
    for i in range(count):
        fam = fams[i % len(fams)]
        n, slots, vols = shapes[(i // len(fams)) % len(shapes)]
        if fam in ("plain", "weave", "hop"):
            vols = min(vols, 2)
        out.append([fam, 90000 + i, n, slots, vols])
    return out

count = int(sys.argv[1]) if len(sys.argv) > 1 else 600
sp = build(count)
tree = stage("../../tasks/peg-hold-tally/solution")
ref = json.loads(subprocess.run([sys.executable, "runner.py", str(tree)],
                                input=json.dumps(sp), capture_output=True, text=True,
                                check=True).stdout)
bad_m = bad_r = 0
for (fam, seed, n, slots, vols), got in zip(sp, ref):
    lines = gen.small(fam, seed, n, slots, vols)
    want = slow.expect(lines)
    if model.expect(lines) != want:
        bad_m += 1
        if bad_m == 1:
            print("model differs first at", fam, seed)
    if got != want:
        bad_r += 1
        if bad_r == 1:
            print("reference differs first at", fam, seed)
print("%d programs: model %d differ, reference %d differ" % (count, bad_m, bad_r))
