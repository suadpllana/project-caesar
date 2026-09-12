"""Time a chosen implementation over the whole generated set, family by family."""
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "claim-line-stall"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(HERE))

import gen  # noqa: E402
import lab  # noqa: E402


def load(over):
    here = lab.stage(over)
    sys.path.insert(0, str(here))
    for name in ("ops", "hold", "hold.name", "hold.say", "hold.book",
                 "hold.line", "hold.lift", "hold.knot", "hold.turn", "hold.act"):
        sys.modules.pop(name, None)
    import ops as mod
    from hold import book as bk
    return mod, bk


def main():
    over = sys.argv[1] if len(sys.argv) > 1 else str(TASK / "solution")
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 45
    only = sys.argv[3] if len(sys.argv) > 3 else None
    mod, bk = load(over)
    work = gen.programs("timing-seed", per)
    spent = {}
    ops = {}
    for fam, name, lines in work:
        if only and fam != only:
            continue
        t0 = time.time()
        h = bk.Hold()
        for line in lines:
            mod.ex(h, tuple(line.split()))
        spent[fam] = spent.get(fam, 0.0) + (time.time() - t0)
        ops[fam] = ops.get(fam, 0) + len(lines)
    total = 0.0
    for fam in sorted(spent):
        print("%-6s %8.2f s  %9d ops" % (fam, spent[fam], ops[fam]), flush=True)
        total += spent[fam]
    print("total  %8.2f s" % total, flush=True)


if __name__ == "__main__":
    main()
