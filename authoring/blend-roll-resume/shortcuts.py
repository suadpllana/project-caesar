"""Score the dumbest positional and constant strategies, and say how much they match.

All-or-nothing grading turns a strategy that matches most scripts into a 0 and hides that the
data barely exercises the rule, so the fraction matters as much as the score.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "blend-roll-resume"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases  # noqa: E402
import gen  # noqa: E402
import lab  # noqa: E402
import model  # noqa: E402

WHAT = {
    "nop (the shipped tree)": None,
    "constant micro-batch and no departures": HERE / "probes" / "shortcut-const",
    "positional: always the first live source": HERE / "probes" / "shortcut-first-source",
    "the published example line replayed": HERE / "probes" / "shortcut-example",
    "the frozen answers carried": HERE / "probes" / "forge-from-truth",
}


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    work = [("hand", n, cases.ops(n)) for n in cases.ORDER]
    work += [w for w in gen.programs("shortcuts", per) if w[0] != "big"]
    want = {name: model.expect(lines) for _f, name, lines in work}
    for label, where in WHAT.items():
        same = 0
        for _fam, name, lines in work:
            try:
                got = lab.inproc(lines, where)
            except Exception:
                got = None
            if got == want[name]:
                same += 1
        print("%-42s matched %3d of %3d scripts" % (label, same, len(work)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
