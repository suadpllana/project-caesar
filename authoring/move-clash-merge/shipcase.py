"""Choose the scenarios that ship in the tree: show the format, decide as little as possible.

A shipped scenario the agent can run is a free experiment. The ones worth shipping show every
kind of line and show the engine being wrong - the brief has to be able to point at one - while
separating the fewest wrong readings, so nothing about the graded rules can be fitted from them.

Prints the candidates ordered by how many of the enumerated readings they decide.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "authoring" / "move-clash-merge"))
sys.path.insert(0, str(ROOT / "tasks" / "move-clash-merge" / "tests"))

import gen  # noqa: E402
import readings as R  # noqa: E402

SHIPPED = str(ROOT / "tasks" / "move-clash-merge" / "environment" / "app_src" / "mrg")


def kinds(text):
    got = set()
    for line in text.split("\n"):
        w = line.split()
        if w and w[0] in ("L", "R"):
            got.add(w[1])
    return got


def main(argv):
    per = int(argv[1]) if len(argv) > 1 else 40
    want = {"mkd", "mkf", "ed", "mv", "rm"}
    pop = [(n, t) for n, t in gen.batch("shipcase", per)
           if kinds(t) == want and len(t.split("\n")) <= 26]
    print("candidates showing every line kind: %d" % len(pop))
    rows = []
    for name, text in pop:
        good = R.run(R.REFERENCE, text)
        if R.run(SHIPPED, text) == good:
            continue
        decided = [r for r in sorted(R.READINGS)
                   if R.run(_dir(r), text) != good]
        rows.append((len(decided), len(text.split("\n")), name, decided))
    rows.sort()
    for n, lines, name, decided in rows[:12]:
        print("%2d decided  %2d lines  %-22s %s" % (n, lines, name, ", ".join(decided[:4])))
    return 0


_DIRS = {}


def _dir(reading):
    import tempfile
    if reading not in _DIRS:
        d = pathlib.Path(tempfile.mkdtemp(prefix="mcm-ship-"))
        for part, src in R.READINGS[reading].items():
            (d / part).write_text(src, encoding="utf-8")
        _DIRS[reading] = d
    return _DIRS[reading]


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
