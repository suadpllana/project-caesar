"""The wrong readings, in the contract tools/readingcheck.py reads.

Every reading is a whole accounting - the reference with one decision settled the other way - so
what is measured is a reading an agent could hold, not an ablation of a file nobody would write.
The sources come from make_readings.py, which asserts that each patch fired.

`measure.py` prints the same readings as a table of how much of the population each one moves.
"""
import pathlib
import shutil
import sys
import tempfile

import make_readings

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "peg-hold-tally"
REFERENCE = str(TASK / "solution")
PARTS = make_readings.PARTS

sys.path.insert(0, str(TASK / "tests"))

import cases  # noqa: E402
import gen  # noqa: E402

_BASE = {part: (TASK / "solution" / part).read_text(encoding="utf-8") for part in PARTS}
READINGS = {}
for _name in make_readings.READINGS:
    _text = make_readings.sources(_name, _BASE)
    READINGS[_name] = {part: _text[part] for part in PARTS if _text[part] != _BASE[part]}

_trees = {}
_made = {}


def _tree(policy):
    """The shipped tree with one accounting laid over it, made once per policy."""
    key = str(policy)
    got = _trees.get(key)
    if got is None:
        room = pathlib.Path(tempfile.mkdtemp(prefix="reading-tree-"))
        got = room / "app"
        shutil.copytree(TASK / "environment" / "app_src", got,
                        ignore=shutil.ignore_patterns("progs", "__pycache__"))
        for part in PARTS:
            src = pathlib.Path(policy) / part
            if src.is_file():
                shutil.copy(src, got / "keep" / part)
        _trees[key] = got
    return got


def run(policy, text):
    """Drive one program under one accounting and return what it printed."""
    here = str(_tree(policy))
    for mod in [m for m in sys.modules if m == "store" or m == "keep"
                or m.startswith("store.") or m.startswith("keep.")]:
        del sys.modules[mod]
    sys.path.insert(0, here)
    try:
        from store import ops
        from store.host import Host
        h = Host()
        acc = []
        for line in text.splitlines():
            bits = line.split()
            if bits:
                ops.ex(h, tuple(bits), acc)
        return acc
    finally:
        sys.path.remove(here)


def policy(name):
    """One reading as a directory, made once, for the drivers that want a path."""
    got = _made.get(name)
    if got is None:
        got = pathlib.Path(tempfile.mkdtemp(prefix="reading-"))
        for part in PARTS:
            (got / part).write_text(READINGS[name].get(part, _BASE[part]),
                                    encoding="utf-8", newline="\n")
        _made[name] = got
    return got


def enumerated():
    return [(name, "\n".join(cases.ops(name))) for name in cases.ORDER]


def generated(n):
    per = max(1, n // len(gen.SMALL))
    out = []
    for fam, name, lines in gen.programs("readingcheck", per):
        if fam in gen.SMALL:
            out.append((name, "\n".join(lines)))
    return out[:n]


def reductions(text):
    """Shrink by dropping a line and everything that then names something absent.

    Programs are flat, but they are not independent: dropping the line that makes a peg leaves
    later lines naming a peg that was never made, and those raise rather than disagree. Dropping
    the dependents with it keeps the shrunken program legal and gets the counterexample short.
    """
    lines = text.split("\n")
    for i in range(len(lines) - 1, -1, -1):
        bits = lines[i].split()
        if not bits:
            continue
        drop = {i}
        if bits[0] == "peg":
            name = bits[1]
            drop |= {j for j, ln in enumerate(lines)
                     if j > i and name in ln.split()[1:]}
        elif bits[0] == "vol":
            name = bits[1]
            drop |= {j for j, ln in enumerate(lines) if j > i and name in ln.split()[1:]}
        elif bits[0] == "fork":
            name = bits[1]
            drop |= {j for j, ln in enumerate(lines) if j > i and name in ln.split()[1:]}
        yield "\n".join(ln for j, ln in enumerate(lines) if j not in drop)
