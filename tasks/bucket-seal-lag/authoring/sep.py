"""How many generated plans does a reading get wrong?

A reading that moves a handful of plans in a few hundred is a lottery ticket
rather than a test of anything, so every candidate rule gets a number here
before it is believed.
"""

import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "authoring"))
sys.path.insert(0, str(ROOT / "tests"))

import gen
import harness
import oracle


def score(overlay, plans, want):
    app = harness.tree(overlay)
    bad, fault = 0, 0
    try:
        for name, text in plans:
            try:
                got = harness.drive(app, text)
            except Exception:
                fault += 1
                bad += 1
                continue
            if got["tr"] != want[name]["tr"] or got["sk"] != want[name]["sk"]:
                bad += 1
    finally:
        shutil.rmtree(app.parent, ignore_errors=True)
    return bad, fault


def plans(n, nonce="fuzz"):
    return [(nm, gen.text(p)) for nm, p in gen.batch(nonce, n)]


def truth(ps):
    return dict((nm, oracle.play(t)) for nm, t in ps)


def main(argv):
    n = int(argv[1]) if len(argv) > 1 else 200
    ps = plans(n)
    want = truth(ps)
    rows = sum(len(v["tr"]) for v in want.values())
    print("plans %d rows %d  max %d" % (n, rows, max(len(v["tr"]) for v in want.values())))
    names = argv[2:] or ["solution", "environment/app_src/flow"]
    for nm in names:
        p = ROOT / nm
        bad, fault = score(str(p), ps, want)
        print("%-46s wrong %4d of %d   faults %d" % (nm, bad, n, fault))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
