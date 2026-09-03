"""Which graded field separates each cheat, and on how many sets.

A field that separates nothing is pure liability: it cannot catch a wrong answer
and it can fail a right one. A field that separates only one cheat on one set in
four hundred is a lottery ticket rather than a test of expertise, and this prints
the count so that can be seen rather than assumed.
"""

import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))

import cases
import gen
import harness

REF = os.path.join(TASK, "solution")
NAMES = ("rch.py", "hold.py", "card.py", "seq.py")


def policy(paths):
    box = tempfile.mkdtemp(prefix="field-")
    for name in NAMES:
        shutil.copyfile(os.path.join(REF, name), os.path.join(box, name))
    for name, body in paths.items():
        with open(os.path.join(box, name), "w", newline="\n") as fh:
            fh.write(body)
    return box


def parts(rows):
    fl = [r for r in rows if r[0] == "fl"]
    return {
        "when a key is filed": [(r[2], r[1]) for r in fl],
        "the key it is filed under": [(r[2], r[3]) for r in fl],
        "the score that stands": [(r[2], r[4]) for r in fl],
        "the order rows land in": [r[2] for r in fl],
        "the set of keys filed": sorted(r[2] for r in fl),
    }


def main():
    sys.path.insert(0, HERE)
    import readings
    texts = [cases.SETS[n] for n in sorted(cases.SETS)]
    texts += [gen.one("field:%d" % i) for i in range(400)]
    base = harness.Rig(REF)
    want = [base.run(t) for t in texts]
    base.close()
    tally = {}
    for name, over in sorted(readings.READINGS.items()):
        box = policy(over)
        rig = harness.Rig(box)
        counts = {}
        for text, good in zip(texts, want):
            got = rig.run(text)
            a, b = parts(good), parts(got)
            for field in a:
                if a[field] != b[field]:
                    counts[field] = counts.get(field, 0) + 1
        rig.close()
        shutil.rmtree(box, ignore_errors=True)
        best = sorted(counts.items(), key=lambda kv: -kv[1])
        print("%-28s %s" % (name, "  ".join("%s:%d" % kv for kv in best) or "NOTHING"))
        for field, n in counts.items():
            tally[field] = max(tally.get(field, 0), n)
    print()
    dead = []
    for field in parts([]):
        n = tally.get(field, 0)
        print("%-28s separates at most %d of %d sets" % (field, n, len(texts)))
        if n == 0:
            dead.append(field)
    if dead:
        print("dead weight: %s" % dead)
        return 1
    print("no graded field is dead weight")
    return 0


if __name__ == "__main__":
    sys.exit(main())
