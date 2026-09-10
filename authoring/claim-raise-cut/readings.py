"""Does the enumerated set separate the readings a solver will actually have?

Every wrong reading is a cheat under `cheat/` that carries the reference with one decision
taken the other way, so this reads the readings straight out of the cheat scripts (the file
or files that differ from `solution/`) and exposes them in the form `tools/readingcheck.py`
consumes. Run directly it prints, for each reading, the first hand case that catches it and
how much of the generated population it moves.

The four cheats that are right and only slow (`all-live`, `per-participant`,
`candidate-verify`, `whole-rebuild`) and the ten probes are not readings and are left out.

One reading is order-dependent: `cut-one-ring` takes the first ring it finds from a set of
transaction names, so which hand case separates it (`ring-pair`, `cut-again`, or neither)
changes with the process's hash seed; the nonce `ring` family separates it in every run.

    python3 authoring/claim-raise-cut/readings.py [--per N] [reading ...]
"""
import pathlib
import re
import signal
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
TASK = HERE.parents[1] / "tasks" / "claim-raise-cut"
TESTS = TASK / "tests"
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS / "seal"))

import cases  # noqa: E402
import gen  # noqa: E402
import lab  # noqa: E402
import model  # noqa: E402

REFERENCE = str(TASK / "solution")
TIMED_ONLY = ("all-live", "per-participant", "candidate-verify", "whole-rebuild")
BLOCK = re.compile(r"cat > /app/hold/(\w+\.py) <<'PYEOF'\n(.*?)\nPYEOF\n", re.S)
GUARD = 60


def _readings():
    ref = {p.name: p.read_text().rstrip("\n") for p in pathlib.Path(REFERENCE).glob("*.py")}
    out = {}
    for sh in sorted((TASK / "cheat").glob("cheat-*.sh")):
        name = sh.name[len("cheat-"):-len(".sh")]
        if name.startswith("probe-") or name in TIMED_ONLY:
            continue
        files = {n: src for n, src in BLOCK.findall(sh.read_text())
                 if src.rstrip("\n") != ref[n]}
        assert files, "%s changes nothing against the reference" % sh.name
        out[name] = {n: src + "\n" for n, src in files.items()}
    return out


READINGS = _readings()
_LABS = {}


def _bail(_sig, _frm):
    raise TimeoutError("reading ran past the guard")


def run(policy, text):
    key = str(policy)
    lb = _LABS.get(key)
    if lb is None:
        lb = _LABS[key] = lab.Lab(policy)
    signal.signal(signal.SIGALRM, _bail)
    signal.alarm(GUARD)
    try:
        return lb.run(lab.steps_of(text))
    except (TimeoutError, RecursionError, AttributeError, TypeError, KeyError,
            ValueError, IndexError) as exc:
        return ["<%s>" % type(exc).__name__]
    finally:
        signal.alarm(0)


def enumerated():
    for name, steps in cases.programs():
        yield name, "\n".join(" ".join(s) for s in steps)


def generated(rounds=40):
    per = max(1, int(rounds) // len(gen.FAMILIES) + 1)
    for name, steps in gen.programs("readings-seed", per, 0):
        yield name, "\n".join(" ".join(s) for s in steps)


def main(argv):
    per = 40
    if "--per" in argv:
        i = argv.index("--per")
        per = int(argv[i + 1])
        del argv[i:i + 2]
    want = argv or sorted(READINGS)
    hand = cases.programs()
    pop = gen.programs("readings-seed", per, 0)
    truth_hand = {n: model.trace(s) for n, s in hand}
    truth_pop = [model.trace(s) for _n, s in pop]
    ref = lab.Lab(REFERENCE)
    bad = [n for n, s in hand if ref.run(s) != truth_hand[n]]
    bad += [n for (n, s), t in zip(pop, truth_pop) if ref.run(s) != t]
    assert not bad, "the reference disagrees with the model on %s" % bad[:5]
    print("reference agrees with the model on %d hand and %d generated programs\n"
          % (len(hand), len(pop)))
    print("%-20s %-16s %s" % ("reading", "first hand case", "generated moved"))
    holes = []
    for name in want:
        # the reference with the reading's files laid over it, as tools/readingcheck.py does
        d = pathlib.Path(lab.tempfile.mkdtemp(prefix="crc-reading-"))
        for src in pathlib.Path(REFERENCE).glob("*.py"):
            (d / src.name).write_text(src.read_text())
        for fn, src in READINGS[name].items():
            (d / fn).write_text(src)
        first = None
        for n, s in hand:
            if run(d, "\n".join(" ".join(x) for x in s)) != truth_hand[n]:
                first = n
                break
        moved = sum(1 for (n, s), t in zip(pop, truth_pop)
                    if run(d, "\n".join(" ".join(x) for x in s)) != t)
        pct = 100.0 * moved / len(pop)
        print("%-20s %-16s %d/%d (%.1f%%)" % (name, first or "-", moved, len(pop), pct))
        if first is None:
            holes.append(name)
    if holes:
        print("\nno hand case catches: %s" % ", ".join(holes))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
