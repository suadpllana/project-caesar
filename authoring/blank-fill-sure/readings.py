"""The wrong readings of blank-fill-sure, in the form tools/readingcheck.py and tracecheck read.

Each reading is the reference with one decision taken the other way, built as whole editable
files by make_readings.py into readings/<name>/. EDITS names the fifteen semantic readings
literally, so tracecheck holds the trace's Readings table to one row each. EXACT names the two
that print what the reference prints - slow-no-fresh and slow-no-split - which only the wall
clock and the memory cap separate: they are in READINGS, so readingcheck runs them and reports
them as equivalent, which is the point of them, and the trace records them under Tolerances.

    python3 authoring/blank-fill-sure/readings.py        first hand case catching each reading
"""
import pathlib
import signal
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "blank-fill-sure"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import cases  # noqa: E402
import gen  # noqa: E402
import tree  # noqa: E402

REFERENCE = str(TASK / "solution")
EXACT = ("slow-no-fresh", "slow-no-split")

EDITS = (
    "fresh-all",
    "first-col",
    "per-rule",
    "spare-one",
    "ne-fresh",
    "ne-no-join",
    "query-consts",
    "used-only",
    "head-label",
    "all-groups",
    "possible",
    "no-ban",
    "ne-unknown",
    "labels-apart",
    "smallest-fill",
)

READINGS = {
    name: {p.name: p.read_text(encoding="utf-8") for p in sorted((HERE / "readings" / name).glob("*.py"))}
    for name in EDITS + EXACT
}

GUARD = 30
_RUNNERS = {}


def _late(_sig, _frame):
    raise TimeoutError("reading ran past the guard")


def run(policy, text):
    """The printed report of one program under one editable-file set, or the error it raised."""
    key = str(policy)
    fn = _RUNNERS.get(key)
    if fn is None:
        fn = _RUNNERS[key] = tree.runner(key)
    signal.signal(signal.SIGALRM, _late)
    signal.alarm(GUARD)
    try:
        return fn(text)
    except Exception as exc:
        return ["<%s>" % type(exc).__name__]
    finally:
        signal.alarm(0)


def enumerated():
    return [(name, "\n".join(cases.prog(name)) + "\n") for name in cases.ORDER]


def generated(n=400):
    per = max(1, n // 10)
    progs = [p for p in gen.programs("readingcheck", per) if p[0] not in ("wide", "flags")]
    return [(name, "\n".join(lines) + "\n") for _fam, name, lines in progs[:n]]


def main():
    missing = [n for n in EDITS + EXACT if not READINGS[n]]
    if missing:
        raise SystemExit("run make_readings.py first; missing: %s" % ", ".join(missing))
    ref = run(REFERENCE, "table t 0..1\nrow t 1\nrule q X :- t(X)\n")
    assert ref == ["ans q 1", "q 1"], ref
    for name in EDITS + EXACT:
        import tempfile
        d = pathlib.Path(tempfile.mkdtemp(prefix="bfs-reading-"))
        for f, src in READINGS[name].items():
            (d / f).write_text(src, encoding="utf-8")
        hit = next((c for c, t in enumerated() if run(REFERENCE, t) != run(d, t)), None)
        print("%-14s %s" % (name, ("caught by " + hit) if hit else
                            ("exact; the clock separates it" if name in EXACT else "NOT CAUGHT")))


if __name__ == "__main__":
    main()
