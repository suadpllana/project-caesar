"""How much of the graded population each wrong reading actually moves.

A reading that moves 1% of programs is still a 0 under all-or-nothing grading, but a population
that barely exercises the mechanism is a population that will not catch the next one. This is the
number that says whether the families are shaped around the rules or only near them.
"""
import pathlib
import sys

import lab

TASK = lab.TASK
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))
import cases   # noqa: E402
import gen     # noqa: E402
import model   # noqa: E402

ROOM = pathlib.Path(__file__).resolve().parent / "readings"
SLOW = ("pre-copy", "no-memo")


def drive(here, lines):
    ops, prog, store = lab.load(here)
    f = store.Fld()
    try:
        for w in prog.walk(lines):
            ops.ex(f, w)
    except RecursionError:
        return ["RAISED"]
    return f.out


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    work = [(fam, name, lines) for fam, name, lines in gen.programs("rates", per)
            if fam not in ("wide", "deep")]
    want = {name: model.expect(lines) for _f, name, lines in work}
    hand = {name: model.expect(cases.ops(name)) for name in cases.ORDER}
    print("%-14s %6s  %s" % ("reading", "moves", "families it moves most"))
    for d in sorted(ROOM.iterdir()):
        if not d.is_dir() or d.name in SLOW:
            continue
        here = lab.tree(d)
        bad, byfam = 0, {}
        for fam, name, lines in work:
            if drive(here, lines) != want[name]:
                bad += 1
                byfam[fam] = byfam.get(fam, 0) + 1
        caught = [n for n in cases.ORDER if drive(here, cases.ops(n)) != hand[n]]
        top = sorted(byfam.items(), key=lambda kv: -kv[1])[:3]
        print("%-14s %5.1f%%  %-34s cases: %d (%s)"
              % (d.name, 100.0 * bad / len(work),
                 " ".join("%s %d%%" % (f, 100 * c // per) for f, c in top),
                 len(caught), caught[0] if caught else "NONE"))


if __name__ == "__main__":
    main()
