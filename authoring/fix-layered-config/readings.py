"""Does the enumerated set separate the readings a solver will actually have?

Each directory under `readings/` is a six-file service: the reference with one decision taken
the other way. This exposes them in the form `tools/readingcheck.py` consumes, and run
directly it prints the first hand case that catches each one and how much of the generated
population it moves. The three `slow-*` readings are semantically identical to the reference
on purpose - the execution limit separates them, never an assertion - and are reported as such.

    python3 readings.py [--per N] [reading ...]
"""
import pathlib
import signal
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
TESTS = HERE.parents[1] / "tasks" / "fix-layered-config" / "tests"
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS / "seal"))

import cases  # noqa: E402
import gen  # noqa: E402
import lab  # noqa: E402
import mkoverlay  # noqa: E402
import model  # noqa: E402

REFERENCE = str(lab.TASK / "solution")
TIMED_ONLY = {"slow-enumerate", "slow-materialize", "slow-retie"}

READINGS = {
    d.name: {f.name: f.read_text() for f in sorted(d.glob("*.py"))}
    for d in sorted((HERE / "readings").iterdir()) if d.is_dir()
}

_LABS = {}
GUARD = 20


def _overlay(policy):
    policy = pathlib.Path(policy)
    if policy == pathlib.Path(REFERENCE) or all((policy / n).is_file() for n in lab.PARTS):
        return policy
    return mkoverlay.build(policy)


def _bail(_sig, _frm):
    raise TimeoutError("reading ran past the guard")


def run(policy, text):
    """Run one plan under one six-file service, and give back the printed lines."""
    key = str(policy)
    lb = _LABS.get(key)
    if lb is None:
        lb = lab.Lab(_overlay(policy))
        _LABS[key] = lb
    signal.signal(signal.SIGALRM, _bail)
    signal.alarm(GUARD)
    try:
        return tuple(lb.run(text))
    except Exception as exc:
        return ("CRASH %s" % type(exc).__name__,)
    finally:
        signal.alarm(0)


def enumerated():
    return sorted(cases.PLANS.items())


def generated(n):
    out = []
    for name, fn in gen.FAMS:
        for i in range(max(1, n // len(gen.FAMS))):
            import random
            out.append(("%s-%d" % (name, i), fn(random.Random("readings/%s/%d" % (name, i)))))
    return out


def main(argv):
    per = 24
    if "--per" in argv:
        i = argv.index("--per")
        per = int(argv[i + 1])
        del argv[i:i + 2]
    names = argv or sorted(READINGS)
    pop = generated(per * len(gen.FAMS))
    truth = {name: tuple(model.trace(text)) for name, text in pop}
    hand = {name: tuple(model.trace(text)) for name, text in enumerated()}
    for name in names:
        d = HERE / "readings" / name
        first = None
        for cname, text in enumerated():
            if run(d, text) != hand[cname]:
                first = cname
                break
        moved = sum(1 for pname, text in pop if run(d, text) != truth[pname])
        pct = 100.0 * moved / len(pop)
        tag = "timed-only" if name in TIMED_ONLY else ("BLIND" if first is None else "separated")
        print("%-28s %-11s first=%-32s moves %5.1f%% of %d" % (name, tag, first, pct, len(pop)), flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
