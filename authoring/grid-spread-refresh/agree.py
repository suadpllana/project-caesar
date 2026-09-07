"""Differential test: the reference policy against the sealed model.

Both are driven over the generated families and every report line is compared. A
disagreement is printed with the first differing line and the script that produced it.

    python3 authoring/grid-spread-refresh/agree.py [count]
"""

import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tasks", "grid-spread-refresh", "tests"))

import gen  # noqa: E402
import oracle  # noqa: E402
import tree  # noqa: E402


def main(argv):
    n = int(argv[1]) if len(argv) > 1 else 40
    app = tree.ref()
    sys.path.insert(0, app)
    from sheet import core
    scripts = gen.batch("agree-v1", n)
    bad = 0
    t0 = time.time()
    for name, text in scripts:
        rows = []
        try:
            core.drive(text.split("\n"), rows.append)
        except Exception as exc:
            print("%s: reference raised %r" % (name, exc))
            bad += 1
            continue
        want = oracle.solve(text)
        if rows == want:
            continue
        bad += 1
        for i in range(max(len(rows), len(want))):
            a = rows[i] if i < len(rows) else "<missing>"
            b = want[i] if i < len(want) else "<missing>"
            if a != b:
                print("%s line %d\n   ref %s\n   mod %s" % (name, i, a, b))
                break
        if bad > 6:
            break
    print("%d scripts, %d disagreements, %.1fs" % (len(scripts), bad, time.time() - t0))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
