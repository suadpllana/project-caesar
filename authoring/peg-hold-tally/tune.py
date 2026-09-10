"""Time the core, the reference and the naive family on one shape config."""
import json
import subprocess
import sys
import time

from stage import stage, TESTS

sys.path.insert(0, str(TESTS))

import gen  # noqa: E402

CODE = """
import sys, time, json
sys.path.insert(0, %r)
from store import ops
from store.host import Host
lines = json.load(sys.stdin)
h = Host(); acc = []
t0 = time.time()
for line in lines:
    bits = line.split()
    if bits: ops.ex(h, tuple(bits), acc)
print(json.dumps([round(time.time() - t0, 2), len(acc)]))
"""

TREES = {
    "core": stage("nop"),
    "ref": stage("../../tasks/peg-hold-tally/solution"),
    "naive": stage("naive"),
    "shipped": stage(None),
    "rescan": stage("probe-shed"),
    "bucket": stage("variants/ok-bucket-scan"),
}


def go(shape, seed, kw, which=("core", "ref", "naive")):
    lines = gen.BIGMAKE[shape](seed, **kw)
    row = ["%s %s n=%d" % (shape, kw, len(lines))]
    for name in which:
        t0 = time.time()
        r = subprocess.run([sys.executable, "-c", CODE % str(TREES[name])],
                           input=json.dumps(lines), capture_output=True, text=True, timeout=1800)
        if r.returncode:
            row.append("%s=FAIL(%s)" % (name, r.stderr.strip()[-90:]))
        else:
            got = json.loads(r.stdout)
            row.append("%s=%.1fs/%d" % (name, got[0], got[1]))
    print(" | ".join(row), flush=True)


if __name__ == "__main__":
    shape = sys.argv[1]
    kw = json.loads(sys.argv[2])
    which = sys.argv[3].split(",") if len(sys.argv) > 3 else ("core", "ref", "naive")
    go(shape, 1, kw, which)
