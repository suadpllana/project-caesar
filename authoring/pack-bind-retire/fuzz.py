"""The reference against the sealed model on random scripts.

Nothing the reference produces is believed because the reference produced it. This runs both
implementations over freshly generated scripts and reports the first row they disagree on.

Usage:
    python3 authoring/pack-bind-retire/fuzz.py [count]
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.abspath(os.path.join(HERE, "..", "..", "tasks", "pack-bind-retire"))
sys.path.insert(0, os.path.join(TASK, "tests"))

import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402


def tree(work):
    dest = os.path.join(work, "tree")
    shutil.copytree(os.path.join(TASK, "environment", "app_src"), dest)
    for f in sorted(os.listdir(os.path.join(TASK, "solution"))):
        if f.endswith(".py"):
            shutil.copyfile(os.path.join(TASK, "solution", f), os.path.join(dest, "hst", f))
    return dest


def main(argv):
    count = int(argv[0]) if argv else 800
    work = tempfile.mkdtemp(prefix="fz-")
    t = tree(work)
    sys.path.insert(0, t)
    from hst import ev
    d = os.path.join(work, "case")
    os.makedirs(d)
    bad = 0
    seen = 0
    for nm in sorted(cases.FIXED):
        p = os.path.join(d, nm + ".txt")
        with open(p, "w", encoding="ascii") as fh:
            fh.write(cases.FIXED[nm])
    for i in range(count):
        nm = "f%05d" % i
        p = os.path.join(d, nm + ".txt")
        with open(p, "w", encoding="ascii") as fh:
            fh.write(gen.spec(0x2F1100 ^ (i * 0x9E3779B1)))
    for f in sorted(os.listdir(d)):
        nm = f[:-4]
        p = os.path.join(d, f)
        rows = []
        try:
            ev.go(nm, p, rows)
        except Exception as exc:
            bad += 1
            print("%s: the reference raised %s: %s" % (nm, type(exc).__name__, exc))
            continue
        want = model.ledger(nm, p)
        seen += 1
        if rows != want:
            bad += 1
            for a, b in zip(rows, want):
                if a != b:
                    print("%s: reference %r, model %r" % (nm, a, b))
                    break
            else:
                print("%s: lengths %d and %d" % (nm, len(rows), len(want)))
    shutil.rmtree(work, ignore_errors=True)
    print("%d scripts compared, %d disagreements" % (seen, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
