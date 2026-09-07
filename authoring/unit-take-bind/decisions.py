"""The reference's graded decisions as rows of features an agent could read off the program.

`tools/onelinecheck.py` searches these for a rule of at most two terms that reproduces the
label exactly. If it finds one, the decision it stands for is an answer a frontier model can
write cold, whatever the brief says, and the task has no depth there.

The features are deliberately syntactic - counts of declarations, whether a name is held back,
how many units declare it - because that is what an agent has in front of it before it has done
any settling. Feeding in a derived quantity (how many origins reach the name at its cheapest
rank, say) would be handing the check the answer and would measure nothing.

Four questions, one per outcome the settlement has to choose between:

    kind        which of own / unit / clash / nothing a name settles to, as 0 / 1 / 2 / 3
    contested   whether a name ends up contested
    unbound     whether a name ends up meaning nothing in the unit that asks for it
    rank        the price the binding settled at

Usage:
    python3 decisions.py        print the row counts and a couple of sample rows
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "tasks" / "unit-take-bind" / "tests"))
import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

KINDS = {"own": 0, "unit": 1, "clash": 2}


def features(units, un, x):
    """What is readable about (unit, name) from the program text alone."""
    u = units[un]
    return {
        "owns_here": u.owns.count(x),
        "als_here": sum(1 for nm, _ in u.als if nm == x),
        "pulls_here": len(u.pulls),
        "wide_here": sum(1 for _, what in u.pulls if what == "*"),
        "narrow_here": sum(1 for _, what in u.pulls if what == x),
        "srcs_here": len({s for s, _ in u.pulls}),
        "shut_here": int(x in u.shuts),
        "hide_here": int(x in u.hides),
        "owners": sum(1 for v in units.values() if x in v.owns),
        "aliasers": sum(1 for v in units.values() for nm, _ in v.als if nm == x),
        "units": len(units),
    }


def rows():
    progs = [cases.ops(name) for name in cases.ORDER]
    progs += [lines for _, _, lines in gen.programs("decisions", 60)]
    out = []
    for lines in progs:
        units, asks = model.parse(lines)
        bind = model.solve(units)
        for un, x in asks:
            got = bind.get((un, x))
            feat = features(units, un, x)
            kind = 3 if got is None else KINDS[got[0]]
            rank = -1 if got is None else got[2]
            out.append((feat, kind, rank))
    return out


def samples():
    got = rows()
    return {
        "kind": [(f, k) for f, k, _ in got],
        "contested": [(f, k == 2) for f, k, _ in got],
        "unbound": [(f, k == 3) for f, k, _ in got],
        "rank": [(f, r) for f, _, r in got],
    }


def main():
    got = samples()
    for name, pairs in sorted(got.items()):
        seen = sorted({str(y) for _, y in pairs})
        print("%-12s %5d rows, outcomes %s" % (name, len(pairs), ", ".join(seen[:6])))
    first = got["kind"][0][0]
    print("features: %s" % ", ".join(sorted(first)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
