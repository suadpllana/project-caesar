"""Does the enumerated set separate the wrong readings a solver will actually have?

The readings come from emit.py, so the cheats that ship and the readings measured here are the
same files and cannot drift apart. Importing this records them without rewriting cheat/.

    python tools/readingcheck.py glob-route-hide [rounds]
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

cases, gen, _model = lab.sealed()

REFERENCE = str(lab.SOL)


def _record(name, comment, files, kind, catch=None, extra=None):
    emit.KIND[name] = kind
    if catch:
        emit.CATCH[name] = catch
    if kind == "reading":
        emit.READINGS[name] = dict(files)


emit.write = _record
for _build in emit.READING_BUILDERS:
    _build()
READINGS = dict(emit.READINGS)
CATCH = dict(emit.CATCH)

_TREES = {}


def run(policy, text):
    """Drive one program under one directory of the five files."""
    here = _TREES.get(str(policy))
    if here is None:
        here = _TREES[str(policy)] = lab.tree(policy)
    return lab.run_text(here, text if text.endswith("\n") else text + "\n")


def enumerated():
    return [(name, "\n".join(cases.prog(name))) for name in cases.ORDER]


def generated(n):
    out = []
    small = [f for f, big in gen.FAMILIES if not big]
    per = max(1, n // len(small))
    for fam in small:
        for i in range(per):
            rng = random.Random("reading|%s|%d" % (fam, i))
            out.append(("%s-%d" % (fam, i), "\n".join(gen.SMALL[fam](rng))))
    return out


def reductions(text):
    """Structure-aware shrinking: drop a whole module with its lines, then single lines."""
    lines = text.split("\n")
    starts = [i for i, ln in enumerate(lines) if ln.startswith("mod ")]
    for k in range(len(starts) - 1, -1, -1):
        a = starts[k]
        b = starts[k + 1] if k + 1 < len(starts) else len(lines)
        yield "\n".join(lines[:a] + lines[b:])
    for i in range(len(lines) - 1, 0, -1):
        if not lines[i].startswith("mod "):
            yield "\n".join(lines[:i] + lines[i + 1:])
