"""Does the enumerated set separate the wrong readings a solver will actually have?

Per-rule coverage on paper is not coverage. The readings come from `emit.py`, so the cheats that
ship and the readings measured here are the same files and cannot drift apart. The slow
families, the forgery and the isolation probes are not readings of the rules and are not
measured here.

    python tools/readingcheck.py claim-cover-lift [rounds]
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

REFERENCE = str(lab.TASK / "solution")

READINGS = {}
for _build in emit.READINGS:
    _name, _comment, _files = _build()
    READINGS[_name] = {part: src for part, src in _files.items()
                       if src != (lab.TASK / "solution" / part).read_text(encoding="utf-8")}


def run(policy, text):
    return lab.run(lab.tree(policy), text.splitlines())


def enumerated():
    return [(name, "\n".join(cases.ops(name))) for name in cases.ORDER]


def generated(n):
    out = []
    for round_ in range(1, 40):
        for fam, name, body in gen.programs("reading-%d" % round_, 2):
            if fam in ("big", "busy", "lines"):
                continue
            out.append((name, "\n".join(body)))
            if len(out) >= n:
                return out
    return out
