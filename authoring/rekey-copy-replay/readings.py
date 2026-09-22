"""Does the enumerated set separate the wrong readings a solver will actually have?

Per-rule coverage on paper is not coverage. The readings come from `emit.py`, so the cheats
that ship and the readings measured here are the same files and cannot drift apart; run
`emit.py` first, always.

    python tools/readingcheck.py rekey-copy-replay [rounds]
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
import cases  # noqa: E402
import gen  # noqa: E402

REFERENCE = str(lab.SOL)

for _build in emit.BUILDERS:
    _build()
READINGS = dict(emit.READINGS)

_TREES = {}


def run(policy, text):
    """Drive one program under one directory of the six files."""
    here = _TREES.get(str(policy))
    if here is None:
        here = _TREES[str(policy)] = lab.tree(policy)
    try:
        return lab.run_text(here, text, timeout=120)
    except RuntimeError as exc:
        return ["RAISED", str(exc)]


def enumerated():
    return [(name, "\n".join(cases.prog(name))) for name in cases.ORDER]


def generated(n):
    out = []
    for fam, name, lines in gen.programs("readings", max(1, n // 9 + 1)):
        if fam in ("wide", "deep"):
            continue
        out.append((name, "\n".join(lines)))
        if len(out) >= n:
            break
    return out


def reductions(text):
    """Drop one instruction at a time, but never the `cfg` line and never the closing `cut`."""
    lines = text.split("\n")
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].startswith("cfg") or lines[i].startswith("cut"):
            continue
        yield "\n".join(lines[:i] + lines[i + 1:])
