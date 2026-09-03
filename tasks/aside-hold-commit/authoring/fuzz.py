"""The reference against the sealed model on random jobs, before any answer is believed.

build_gt.py refuses to write a ground truth without a clean run of this. It is kept separate so a
longer run can be asked for without rewriting anything.
"""
import json
import sys

import stage

SNIP = """
import json, sys
sys.path.insert(0, %r)
import gen
from srv import wire
print(json.dumps({n: wire.drive(j) for n, j in gen.jobs(%r, %d)}))
"""


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 800
    nonce = sys.argv[2] if len(sys.argv) > 2 else "fuzz"
    app = stage.reference()
    mine = json.loads(stage.drive_in(app, SNIP % (stage.TESTS, nonce, count)))
    sys.path.insert(0, stage.TESTS)
    import gen
    import oracle
    off = []
    for name, job in gen.jobs(nonce, count):
        if oracle.drive(job) != mine[name]:
            off.append(name)
    print("%d jobs, %d disagreements %s" % (count, len(off), off[:6]))
    return 1 if off else 0


if __name__ == "__main__":
    raise SystemExit(main())
