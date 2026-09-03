"""Write tests/gt.json, and refuse to write one that has not been proved.

Two proofs are required before a byte is written. The reference and the sealed model have to
produce the same trace for every enumerated job, and they have to agree on a run of random
jobs as well - the enumerated set was written by the same person as the reference, so it is
the random run that says the specification and not one author's habit is what was captured.
"""
import json
import os
import sys

import stage

OUT = os.path.join(stage.TESTS, "gt.json")

SNIP = """
import json, sys
sys.path.insert(0, %r)
import cases, gen
from srv import wire
rows = {}
for name, job in cases.jobs():
    rows[name] = wire.drive(job)
for name, job in gen.jobs(%r, %d):
    rows[name] = wire.drive(job)
print(json.dumps(rows))
"""


def reference_runs(nonce, count):
    app = stage.reference()
    return json.loads(stage.drive_in(app, SNIP % (stage.TESTS, nonce, count)))


def model_runs(nonce, count):
    sys.path.insert(0, stage.TESTS)
    import cases
    import gen
    import oracle
    rows = {}
    for name, job in cases.jobs():
        rows[name] = oracle.drive(job)
    for name, job in gen.jobs(nonce, count):
        rows[name] = oracle.drive(job)
    return rows


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    nonce = "buildgt"
    mine = reference_runs(nonce, count)
    theirs = model_runs(nonce, count)
    off = sorted(k for k in mine if mine[k] != theirs[k])
    if off:
        print("the reference and the sealed model disagree on %d jobs: %s"
              % (len(off), off[:6]))
        for k in off[:2]:
            for i, (a, b) in enumerate(zip(theirs[k], mine[k])):
                if a != b:
                    print("  %s row %d model=%r reference=%r" % (k, i, a, b))
                    break
        return 1
    pinned = {k: v for k, v in mine.items() if not k.startswith("g")}
    with open(OUT, "w", newline="\n") as fh:
        json.dump(pinned, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.chmod(OUT, 0o600)
    print("agreed on %d jobs (%d enumerated, %d generated); wrote %d to gt.json"
          % (len(mine), len(pinned), count, len(pinned)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
