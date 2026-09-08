"""Which scenario operations never applied? A case with a dead line usually means a slip.

Replays each enumerated scenario the way the driver does and reports every `L`/`R` line the
side rejected, so a case that meant to create a contest and quietly did nothing is visible.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tasks" / "move-clash-merge" / "tests"))

import cases  # noqa: E402
import model  # noqa: E402


def dead(text):
    base, nxt, rounds = model.parse(text.split("\n"))
    rec = dict(base)
    lo, ro = dict(base), dict(base)
    made = [0]

    def fresh():
        made[0] += 1
        return "w%d" % made[0]

    out = []
    for i, (lops, rops) in enumerate(rounds, 1):
        for label, cur, ops, fold in (("L", lo, lops, False), ("R", ro, rops, True)):
            for op in ops:
                before = dict(cur)
                model.do(cur, op, fold, fresh)
                if cur == before:
                    out.append("round %d  %s %s" % (i, label, " ".join(op)))
        tgt, nxt, ml, mr = model.merge(rec, nxt, lo, ro)
        for cur, m, fold in ((lo, ml, False), (ro, mr, True)):
            for op in model.emit(cur, tgt, m, fold):
                model.do(cur, op, fold, fresh)
        lo = model.rekey(lo, tgt, fresh)
        ro = model.rekey(ro, tgt, fresh)
        rec = tgt
    return out


def main():
    bad = 0
    for name in cases.ORDER:
        rows = dead(cases.CASES[name])
        if rows:
            bad += 1
            print("%-30s %s" % (name, "; ".join(rows)))
    print("\n%d of %d cases carry a line that did nothing" % (bad, len(cases.ORDER)))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
