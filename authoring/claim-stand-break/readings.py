"""Does the enumerated set separate the wrong readings a solver will actually have?

Per-rule coverage on paper is not coverage. A reading no enumerated case fails is a reading a
submission can carry all the way into the generated population, where the failure reads as bad
luck rather than as a named rule.

The readings come from make_readings.py, which is also what emit.py turns into cheats, so the
cheats that ship and the readings measured here cannot drift apart.

    python tools/readingcheck.py claim-stand-break [rounds]
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402
import make_readings  # noqa: E402

cases, gen, _model = lab.sealed()

REFERENCE = str(lab.ROOT / "tasks" / "claim-stand-break" / "solution")

make_readings.build()

READINGS = {}
for _name, _reads, _case, _patch in make_readings.READINGS:
    _room = make_readings.OUT / _name
    READINGS[_name] = {part: (_room / part).read_text(encoding="utf-8")
                       for part in sorted(set(one for one, _o, _n in _patch))}

_TREES = {}


def run(policy, text):
    """Drive one program under one directory of the six files."""
    here = _TREES.get(str(policy))
    if here is None:
        here = _TREES[str(policy)] = lab.tree(policy)
    return lab.run_text(here, text)


def enumerated():
    return [(name, "\n".join(cases.prog(name)) + "\n") for name in cases.ORDER]


def generated(n):
    """Programs from the task's own generator, the two scale families left out."""
    out = []
    per = max(1, n // 9 + 1)
    for fam, name, lines in gen.programs("readingcheck", per):
        if fam in ("deep", "wide"):
            continue
        out.append((name, "\n".join(lines) + "\n"))
    rng = random.Random(7)
    rng.shuffle(out)
    return out[:n]
