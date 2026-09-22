"""Does the enumerated set separate the wrong readings a solver will actually have?

Per-rule coverage on paper is not coverage: a reading no enumerated case fails is a reading
a submission carries all the way to the generated population, where the failure reads as bad
luck rather than as a named rule. The readings come from emit.py, so the engines measured
here and the ones cheat/ ships are the same files.

    python3 authoring/replay-match-drift/emit.py
    python tools/readingcheck.py replay-match-drift [rounds]
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

cases, gen, _model = lab.sealed()

REFERENCE = str(lab.SOL)

READINGS = {key: emit.files_for(key) for key in emit.READING_ORDER}

_TREES = {}


def run(policy, text):
    here = _TREES.get(str(policy))
    if here is None:
        here = _TREES[str(policy)] = lab.tree(policy)
    return lab.run_text(here, text if text.endswith("\n") else text + "\n")


def enumerated():
    return [(name, "\n".join(cases.prog(name)) + "\n") for name in cases.ORDER]


def generated(n):
    out = []
    for fam, name, lines in gen.programs("readingcheck", max(1, n // 12)):
        if fam in ("long", "wide"):
            continue
        out.append((name, "\n".join(lines) + "\n"))
    return out
