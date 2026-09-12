"""Which enumerated case catches each wrong reading, and how much of a population it moves.

A reading no case names is a reading the graded set does not separate, and a reading that
moves a tiny share of a generated population is one the nonce families are not shaped for.
Both are findings about the task, not about the reading.
"""
import pathlib
import sys
import traceback

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "claim-line-stall"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(HERE))

import cases  # noqa: E402
import gen  # noqa: E402
import lab  # noqa: E402

MODS = ("ops", "hold", "hold.name", "hold.say", "hold.book", "hold.line", "hold.lift",
        "hold.knot", "hold.turn", "hold.act")
PARTS = ("book.py", "line.py", "lift.py", "knot.py", "turn.py", "act.py")

# --- the contract tools/readingcheck.py reads --------------------------------------

REFERENCE = str(TASK / "solution")
READINGS = {
    room.name: {p.name: p.read_text(encoding="utf-8") for p in sorted(room.glob("*.py"))}
    for room in sorted((HERE / "readings").iterdir())
} if (HERE / "readings").is_dir() else {}

_STAGED = {}


def _for(policy):
    key = str(policy)
    if key not in _STAGED:
        _STAGED[key] = load(key)
    return _STAGED[key]


def enumerated():
    return [(n, "\n".join(cases.ops(n))) for n in cases.ORDER]


def generated(n):
    out = []
    per = max(2, n // 5 + 1)
    for _fam, name, lines in gen.programs("readingcheck", per):
        if name.startswith(("wide", "tall")):
            continue
        out.append((name, "\n".join(lines)))
        if len(out) >= n:
            break
    return out


def load(over):
    here = lab.stage(over)
    sys.path.insert(0, str(here))
    for one in MODS:
        sys.modules.pop(one, None)
    import ops as mod
    from hold import book as bk
    sys.path.remove(str(here))
    return mod, bk


def run(policy, text):
    """The trace one program prints under one set of six files."""
    return _run(_for(policy), [one for one in text.splitlines() if one.strip()])


def _run(pair, lines):
    mod, bk = pair
    try:
        h = bk.Hold()
        for line in lines:
            mod.ex(h, tuple(line.split()))
        return h.out
    except Exception:
        return ["raised: " + traceback.format_exc(limit=1).strip().splitlines()[-1]]


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    work = [(n, cases.ops(n)) for n in cases.ORDER]
    pop = [(n, lines) for _f, n, lines in gen.programs("readings", per)
           if not n.startswith(("wide", "tall"))]
    pair = load(str(TASK / "solution"))
    hand = {n: _run(pair, l) for n, l in work}
    want = {n: _run(pair, l) for n, l in pop}

    rooms = sorted((HERE / "readings").iterdir())
    print("%-14s %-28s %6s  %s" % ("reading", "first case that catches it", "cases", "moved"))
    misses = []
    for room in rooms:
        pair = load(str(room))
        caught = [n for n, l in work if _run(pair, l) != hand[n]]
        moved = sum(1 for n, l in pop if _run(pair, l) != want[n])
        print("%-14s %-28s %3d/%-2d  %5.1f%%"
              % (room.name, caught[0] if caught else "NOT CAUGHT", len(caught), len(work),
                 100.0 * moved / len(pop)))
        if not caught:
            misses.append(room.name)
    print("%d readings, %d not caught by any enumerated case" % (len(rooms), len(misses)))
    return 1 if misses else 0


if __name__ == "__main__":
    sys.exit(main())
