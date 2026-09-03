"""Which graded axis separates each cheat, and is either axis dead weight.

Two things are compared for every panel: the ordered ledger, and the values the panel was
left holding. A graded axis that separates nothing is pure liability - it cannot catch a
wrong answer and it can still fail a right one - so this counts, per cheat, how many panels
each axis catches it on.

The honest expectation is that the ledger does the work and the final values almost never
catch anything the ledger missed. That is what the verifier's own docstring claims, and
this is the number behind the claim rather than an assertion of it.

    python3 authoring/field_report.py [count]
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import cases  # noqa: E402
import gen  # noqa: E402
import harness  # noqa: E402
import oracle  # noqa: E402
import trial  # noqa: E402


def main(argv):
    n = int(argv[1]) if len(argv) > 1 else 150
    panels = [(k, cases.PANELS[k]) for k in sorted(cases.PANELS)] + gen.build("fields", n)
    want = {}
    for name, text in panels:
        got = oracle.check(text)
        if got is not None:
            want[name] = got
    live = [(k, t) for k, t in panels if k in want]
    print("%-34s %7s %7s %7s" % ("cheat", "ledger", "values", "only-v"))
    onlyv_total = 0
    for sh in sorted((TASK / "cheat").glob("cheat-*.sh")):
        work, app = trial.stage(script=sh)
        got = harness.drive(app, live)
        led = val = onlyv = 0
        for name, _t in live:
            r = got[name]
            if r["err"] is not None:
                led += 1
                continue
            lbad = tuple(r["log"]) != want[name]["log"]
            vbad = tuple(r["dump"]) != want[name]["dump"]
            led += lbad
            val += vbad
            onlyv += (vbad and not lbad)
        onlyv_total += onlyv
        print("%-34s %7d %7d %7d" % (sh.name, led, val, onlyv))
    print("\n%d panels. Panels where the final values catch something the ledger does "
          "not: %d." % (len(live), onlyv_total))
    print("The ledger is the axis that does the work; the values are a cross-check that "
          "makes a failure legible, and the verifier says so.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
