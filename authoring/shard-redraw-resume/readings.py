"""Does the enumerated set separate the wrong readings a solver will actually have?

Per-rule coverage on paper is not coverage. A reading that no enumerated case fails is a rule
the case set does not pin, and under all-or-nothing grading a probe agent that holds it looks
exactly like bad luck on a handful of generated programs. The readings come from `emit.py`, so
the cheats that ship and the readings measured here are the same files and cannot drift apart.

    python tools/readingcheck.py shard-redraw-resume [rounds]
"""
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
import cases  # noqa: E402
import gen  # noqa: E402

REFERENCE = str(lab.TASK / "solution")

for _build in emit.SEMANTIC:
    _build()
READINGS = dict(emit.BUILT)

_TREES = {}


def run(policy, text):
    """Drive one program under one directory of the six files."""
    here = _TREES.get(str(policy))
    if here is None:
        here = _TREES[str(policy)] = lab.tree(policy)
    room = pathlib.Path(tempfile.mkdtemp(prefix="srr-read-"))
    prog = room / "p.txt"
    prog.write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
    try:
        return lab.run(here, prog, timeout=120)
    except RuntimeError as exc:
        return ["RAISED", str(exc).splitlines()[-1]]


def enumerated():
    return [(name, "\n".join(cases.ops(name))) for name in cases.ORDER]


def generated(n):
    out = []
    fams = [f for f, big in gen.FAMILIES if not big]
    for i in range(n):
        fam = fams[i % len(fams)]
        lines = gen.one(fam, "reading/%s/%d" % (fam, i))
        out.append(("%s-%d" % (fam, i), "\n".join(lines)))
    return out


def reductions(text):
    """Structure-aware shrinking: drop a leg op, or shorten a run, before dropping a header."""
    lines = text.split("\n")
    for i in range(len(lines) - 1, -1, -1):
        tok = lines[i].split()
        if tok and tok[0] in ("run", "kill", "back", "nf"):
            yield "\n".join(lines[:i] + lines[i + 1:])
    for i, line in enumerate(lines):
        tok = line.split()
        if tok and tok[0] == "run" and int(tok[1]) > 1:
            for smaller in (int(tok[1]) // 2, int(tok[1]) - 1):
                if smaller >= 1:
                    yield "\n".join(lines[:i] + ["run %d" % smaller] + lines[i + 1:])
    for i in range(len(lines) - 1, -1, -1):
        yield "\n".join(lines[:i] + lines[i + 1:])
