"""Does the enumerated set separate the readings a solver will actually have?

Each directory under `readings/` is a whole six-file host: the reference with one decision
taken the other way, which is the shape a plausible wrong plan produces. This exposes them in
the form `tools/readingcheck.py` consumes, and run directly it prints the first hand case that
catches each one and how much of the generated population it moves.

A reading that no hand case catches is a hole in `tests/cases.py`. A reading that moves nothing
is a distinction the environment cannot express, which is worse - except for the six that are
semantically identical to the reference on purpose - `scan-the-order`, `global-list-filtered`,
`pos-compare`, `rebuild-on-load`, `want-scan` and `sweep-rescan` - which the execution limit
separates rather than any assertion.

    python3 readings.py [--per N] [reading ...]
"""
import pathlib
import signal
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
TESTS = HERE.parents[1] / "tasks" / "publish-settle-order" / "tests"
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS / "seal"))

import cases  # noqa: E402
import gen  # noqa: E402
import lab  # noqa: E402
import mkoverlay  # noqa: E402
import model  # noqa: E402

REFERENCE = str(lab.TASK / "solution")
SMALL = [f for f, small in gen.FAMILIES if small]
TIMED_ONLY = {"scan-the-order", "global-list-filtered", "pos-compare", "rebuild-on-load",
              "want-scan", "sweep-rescan"}

READINGS = {
    d.name: {f.name: f.read_text() for f in sorted(d.glob("*.py"))}
    for d in sorted((HERE / "readings").iterdir()) if d.is_dir()
}

_LABS = {}
GUARD = 30


def _overlay(policy):
    """The reference with one reading's files laid over it, as a directory."""
    policy = pathlib.Path(policy)
    if policy == pathlib.Path(REFERENCE) or all((policy / n).is_file() for n in lab.PARTS):
        return policy
    return mkoverlay.build(policy)


def _bail(_sig, _frm):
    raise TimeoutError("reading ran past the guard")


def run(policy, text):
    """Run one program under one six-file host, and give back the printed lines.

    A reading that corrupts the frozen order can loop for ever in `order.live`; the alarm turns
    that into a distinct answer rather than a hang.
    """
    key = str(policy)
    lb = _LABS.get(key)
    if lb is None:
        lb = _LABS[key] = lab.Lab(_overlay(policy))
    signal.signal(signal.SIGALRM, _bail)
    signal.alarm(GUARD)
    try:
        return lb.run([ln for ln in text.splitlines() if ln.strip()])
    except (TimeoutError, RecursionError, AttributeError, TypeError, KeyError, ValueError) as exc:
        return ["<%s>" % type(exc).__name__]
    finally:
        signal.alarm(0)


def enumerated():
    for name in cases.ORDER:
        yield name, "\n".join(cases.ops(name))


def population(seed, per):
    return [p for p in gen.programs(seed, per) if p[0] in SMALL]


def generated(rounds=40):
    for _fam, name, lines in population("readings-seed", max(4, int(rounds))):
        yield name, "\n".join(lines)


def main(argv):
    per = 90
    if "--per" in argv:
        i = argv.index("--per")
        per = int(argv[i + 1])
        del argv[i:i + 2]
    want = argv or sorted(READINGS)
    progs = population("readings-seed", per)
    truth_hand = {n: model.expect(cases.ops(n)) for n in cases.ORDER}
    truth_gen = [model.expect(lines) for _f, _n, lines in progs]

    print("%-22s %-16s %s" % ("reading", "first hand case", "generated moved"))
    holes = []
    for name in want:
        first = None
        for hand in cases.ORDER:
            if run(HERE / "readings" / name, "\n".join(cases.ops(hand))) != truth_hand[hand]:
                first = hand
                break
        moved = sum(1 for (_f, _n, lines), truth in zip(progs, truth_gen)
                    if run(HERE / "readings" / name, "\n".join(lines)) != truth)
        pct = 100.0 * moved / len(progs)
        print("%-22s %-16s %d/%d (%.1f%%)" % (name, first or "-", moved, len(progs), pct))
        if first is None and moved:
            holes.append("%s: moves %.1f%% of the generated set and no hand case catches it"
                         % (name, pct))
        if first is None and not moved and name not in TIMED_ONLY:
            holes.append("%s: identical behaviour, and not one of the two the limit separates" % name)
    for h in holes:
        print("  ! " + h)
    return 1 if holes else 0


if __name__ == "__main__":
    t = time.time()
    rc = main(sys.argv[1:])
    print("%.1fs" % (time.time() - t))
    sys.exit(rc)
