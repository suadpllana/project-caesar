"""Check an editable-file set against the sealed model on hand cases and generated programs.

Usage: python3 authoring/blank-fill-sure/variant_check.py <parts dir> [seed] [per]
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.join(os.path.dirname(os.path.dirname(HERE)), "tasks", "blank-fill-sure")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))
sys.path.insert(0, os.path.join(TASK, "tests", "seal"))

import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402
import tree  # noqa: E402


def main():
    parts = os.path.abspath(sys.argv[1])
    seed = sys.argv[2] if len(sys.argv) > 2 else "variant"
    per = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    run = tree.runner(parts)
    progs = [("hand", n, cases.prog(n)) for n in cases.ORDER] + gen.programs(seed, per)
    bad, took, slowest = [], 0.0, (0.0, "")
    for fam, name, lines in progs:
        t0 = time.time()
        try:
            got = run("\n".join(lines) + "\n")
        except Exception as exc:
            got = "raised %r" % exc
        dt = time.time() - t0
        took += dt
        slowest = max(slowest, (dt, name))
        if got != model.expect(lines):
            bad.append(name)
    print("%s: %d of %d programs wrong%s; %.2fs in total, slowest %s %.2fs"
          % (os.path.basename(parts.rstrip("/")), len(bad), len(progs),
             (" (%s)" % ", ".join(bad[:6])) if bad else "", took, slowest[1], slowest[0]))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
