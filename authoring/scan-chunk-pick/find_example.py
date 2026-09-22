"""Search for the worked example, rather than choosing it.

The brief needs one printed line quoted wrong and right, or a format slip fails every graded
file for a reason that is not the task. A quoted line is also evidence, so the example wanted
is the one that decides the fewest wrong readings: small, one line apart from the shipped
engine, and ruling out as little as possible.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "scan-chunk-pick"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import gen  # noqa: E402
import host  # noqa: E402
import readings as R  # noqa: E402

ref = R._engine(TASK / "solution")
ship = R._engine(None)
alts = {name: R._engine(R.policy_key(name)) for name in R.READINGS} if hasattr(R, "policy_key") else {}


def alt_engine(name):
    import shutil
    import tempfile
    d = pathlib.Path(tempfile.mkdtemp(prefix="ex-"))
    for p in (TASK / "solution").glob("*.py"):
        shutil.copyfile(p, d / p.name)
    for fn, src in R.READINGS[name].items():
        (d / fn).write_text(src, encoding="utf-8")
    return R._engine(d)


def main():
    engines = {name: alt_engine(name) for name in sorted(R.READINGS)}
    best = []
    for fam, name, lines in gen.programs("example-hunt", 60):
        if fam in ("wide", "deep"):
            continue
        if len(lines) > 11:
            continue
        text = "\n".join(lines) + "\n"
        good = ref.run(text)
        bad = ship.run(text)
        if len(good) != len(bad):
            continue
        at = [i for i in range(len(good)) if good[i] != bad[i]]
        if len(at) != 1:
            continue
        i = at[0]
        decided = sum(1 for nm, eng in engines.items() if eng.run(text) != good)
        best.append((decided, len(lines), name, i, bad[i], good[i], lines))
    best.sort(key=lambda t: (t[0], t[1]))
    for row in best[:8]:
        print("decides %d readings, %d lines, %s: line %d  %r -> %r"
              % (row[0], row[1], row[2], row[3], row[4], row[5]))
    if best:
        print("\n--- best program ---")
        print("\n".join(best[0][6]))
        print("--- correct output ---")
        print("\n".join(ref.run("\n".join(best[0][6]) + "\n")))


if __name__ == "__main__":
    main()
