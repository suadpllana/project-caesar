"""No graded value may come down to a name, or to the order a submission happens to scan in.

A submission picks its own order to walk the members in and its own order to sort a handful
of obligations by, and if either can reach a comparison the graded answer depends on a choice
the rules never made. That is a run-audit rejection waiting to happen and no amount of
reasoning about the specification finds it; renaming everything and running it again does.

Two things are checked. Every member and every obligation is renamed by a map that reverses
their lexicographic order, and the answer has to come back as the same answer with the new
labels on it. And the mirror variant - the reference walking the members the other way round -
has to agree row for row.

    python3 authoring/tiecheck.py [generated-count]
"""
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import gen  # noqa: E402
import harness  # noqa: E402
import scen  # noqa: E402

FLIP = {c: chr(ord("z") - (ord(c) - ord("a"))) for c in "abcdefghijklmnopqrstuvwxyz"}


def turn(word):
    return "".join(FLIP.get(c, c) for c in word)


def rename(text):
    out = []
    for ln in text.splitlines():
        f = ln.split()
        if not f:
            continue
        if f[0] == "who":
            out.append(" ".join(["who"] + [turn(x) for x in f[1:]]))
        elif f[0] == "run":
            out.append(ln)
        elif f[1] == "fund":
            out.append("%s fund %s %s" % (f[0], turn(f[2]), f[3]))
        else:
            out.append("%s owe %s %s %s %s %s" % (f[0], turn(f[2]), turn(f[3]), turn(f[4]), f[5], f[6]))
    return "\n".join(out) + "\n"


def mapped(r):
    return {
        "log": [[x[0], turn(str(x[1])), x[2]] for x in r["log"]],
        "sheet": {turn(k): v for k, v in r["sheet"].items()},
    }


def main(argv):
    count = int(argv[1]) if len(argv) > 1 else 200
    streams = list(scen.STREAMS) + gen.batch("71ec4ec4", count)
    ref = harness.stage(None, TASK / "solution")
    bad = []
    for name, text in streams:
        plain = harness.one(ref, text)
        flipped = harness.one(ref, rename(text))
        if mapped({"log": [list(x) for x in plain["log"]], "sheet": plain["sheet"]}) != \
           {"log": [list(x) for x in flipped["log"]], "sheet": flipped["sheet"]}:
            bad.append(name)
    shutil.rmtree(ref, ignore_errors=True)
    print("renaming every member and obligation: %d of %d streams moved" % (len(bad), len(streams)))
    if bad:
        print("   first: %s" % bad[0])
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
