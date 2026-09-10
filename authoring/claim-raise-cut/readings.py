"""What each wrong reading moves, and which enumerated case names it.

For every variant built by make_readings.py: the share of the generated population whose
trace differs from the reference, and the first enumerated case that separates it. A
reading no enumerated case catches is a reading the graded set only catches by luck; a
reading nothing catches at all is either unreachable or an unobservable distinction.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "claim-raise-cut"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases  # noqa: E402
import gen  # noqa: E402
import lab  # noqa: E402


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    heavy = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    pop = gen.programs(seed, per, heavy)
    hand = cases.programs()
    ref = lab.runner(TASK / "solution", "ref")
    want_pop = [ref(s) for _, s in pop]
    want_hand = [ref(s) for _, s in hand]
    rows = []
    for d in sorted((HERE / "readings").iterdir()):
        go = lab.runner(d, d.name)
        moved = 0
        for (name, steps), want in zip(pop, want_pop):
            try:
                got = go(steps)
            except Exception:
                got = None
            if got != want:
                moved += 1
        caught = []
        for (name, steps), want in zip(hand, want_hand):
            try:
                got = go(steps)
            except Exception:
                got = None
            if got != want:
                caught.append(name)
        rows.append((d.name, moved, len(pop), caught))
    print("%-16s %7s  %s" % ("reading", "moved", "enumerated cases that catch it"))
    holes = []
    for name, moved, total, caught in rows:
        share = 100.0 * moved / total
        print("%-16s %6.1f%%  %s" % (name, share, ", ".join(caught[:4]) or "-"))
        if name.startswith("slow-"):
            if moved or caught:
                holes.append("%s should be trace-identical and is not" % name)
        elif not caught and share < 3.0:
            holes.append("%s is caught by no enumerated case and moves under 3%% of the "
                         "population" % name)
        elif not moved:
            holes.append("%s moves nothing in the generated population" % name)
    print()
    for h in holes:
        print("HOLE:", h)
    return 1 if holes else 0


if __name__ == "__main__":
    sys.exit(main())


# --- the contract tools/readingcheck.py reads ---------------------------------------
#
# It builds each reading as the reference with one or more files swapped in, drives both
# over the enumerated set and then over generated programs, and shrinks a counterexample
# for any reading the enumerated set leaves standing. Programs are passed around as text,
# in the same format `run.py` reads.

REFERENCE = str(TASK / "solution")

READINGS = {}
for _d in sorted((HERE / "readings").iterdir()):
    if not _d.is_dir() or _d.name.startswith("slow-"):
        continue
    _files = {}
    for _p in sorted(_d.glob("*.py")):
        _was = (TASK / "solution" / _p.name).read_text(encoding="utf-8")
        _now = _p.read_text(encoding="utf-8")
        if _now != _was:
            _files[_p.name] = _now
    if _files:
        READINGS[_d.name] = _files

_RUNNERS = {}


def _steps(text):
    out = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.append(tuple(line.split()))
    return out


def run(policy, text):
    key = str(policy)
    go = _RUNNERS.get(key)
    if go is None:
        go = _RUNNERS[key] = lab.runner(policy, "rc")
    steps = _steps(text)
    try:
        return tuple(go(steps))
    except Exception as exc:
        return ("raised", type(exc).__name__, str(exc)[:60])


def reductions(text):
    """Drop one step, and drop a whole transaction's steps.

    A program is a flat list of steps and a drop must stay matched by an earlier take
    inside its own transaction, so a shrinker that only drops lines stalls on any program
    holding a drop. Taking a transaction out whole keeps every remaining one well formed.
    """
    lines = [line for line in text.splitlines() if line.strip()]
    who = []
    for line in lines:
        name = line.split()[1]
        if name not in who:
            who.append(name)
    for name in who:
        kept = [line for line in lines if line.split()[1] != name]
        if kept and len(kept) < len(lines):
            yield "\n".join(kept)
    for i in range(len(lines) - 1, -1, -1):
        kept = lines[:i] + lines[i + 1:]
        depth = {}
        ok = True
        for line in kept:
            f = line.split()
            if f[0] == "drop":
                if depth.get((f[1], f[2]), 0) <= 0:
                    ok = False
                    break
                depth[(f[1], f[2])] -= 1
            elif f[0] == "take":
                depth[(f[1], f[2])] = depth.get((f[1], f[2]), 0) + 1
        if ok:
            yield "\n".join(kept)


def _text(steps):
    return "\n".join(" ".join(s) for s in steps)


def enumerated():
    return [(name, _text(steps)) for name, steps in cases.programs()]


def generated(n):
    per = max(1, n // (len(gen.FAMILIES) + len(gen.HEAVY)))
    return [(name, _text(steps)) for name, steps in gen.programs(7, per, 0)]
