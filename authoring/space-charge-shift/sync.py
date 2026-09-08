"""Keep tests/pristine identical to the shipped tree, and say so when it is not.

The verifier overlays the four submitted files onto its own copy of the store. If that copy
drifts from environment/app_src, the agent is graded against a runtime it never saw.

    python3 authoring/space-charge-shift/sync.py [--write]
"""
import filecmp
import os
import shutil
import sys

import harness

SRC = harness.SRC
DST = os.path.join(harness.TESTS, "pristine")
SKIP = ("__pycache__",)


def walk(root):
    out = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in files:
            if f.endswith(".pyc"):
                continue
            p = os.path.join(base, f)
            out[os.path.relpath(p, root)] = p
    return out


def main(argv):
    write = "--write" in argv
    a, b = walk(SRC), walk(DST)
    bad = []
    for rel in sorted(set(a) | set(b)):
        if rel not in a:
            bad.append("only in pristine: " + rel)
        elif rel not in b:
            bad.append("missing from pristine: " + rel)
        elif not filecmp.cmp(a[rel], b[rel], shallow=False):
            bad.append("differs: " + rel)
    if bad and write:
        shutil.rmtree(DST, ignore_errors=True)
        shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns(*SKIP))
        print("rewrote %s (%d differences)" % (DST, len(bad)))
        return 0
    for line in bad:
        print(line)
    print("pristine %s" % ("differs from the shipped tree" if bad else "matches the shipped tree"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
