"""Does the enumerated set separate the wrong readings a solver will actually have?

Per-rule coverage on paper is not coverage: a reading can pass every hand case written for
its rule and die only on a handful of generated programs, which under all-or-nothing grading
is indistinguishable from bad luck. The readings come from `emit.py`, so the cheats that ship
and the readings measured here are the same files and cannot drift apart.

    python tools/readingcheck.py span-claim-charge [rounds]
"""
import pathlib
import random
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

emit.DRY = True
for _build in emit.READINGS:
    _build()
READINGS = dict(emit.BUILT)

_TREES = {}


def run(policy, text):
    """Drive one program under one directory of the five files."""
    here = _TREES.get(str(policy))
    if here is None:
        if isinstance(policy, dict):
            room = pathlib.Path(tempfile.mkdtemp(prefix="scc-read-"))
            for name, src in policy.items():
                (room / name).write_text(src, encoding="utf-8", newline="\n")
            here = lab.tree(room)
        else:
            here = lab.tree(policy)
        _TREES[str(policy)] = here
    lines = [ln for ln in text.split("\n") if ln.strip()]
    try:
        return lab.drive(here, lines, timeout=120)
    except RuntimeError as exc:
        return ["RAISED", str(exc).splitlines()[-1]]


def enumerated():
    return [(name, "\n".join(cases.ops(name))) for name in cases.ORDER]


def generated(n):
    out = []
    small = [f for f, s in gen.FAMILIES if s]
    per = max(1, n // len(small))
    for fam in small:
        for i in range(per):
            name = "%s-%d" % (fam, i)
            rng = random.Random("reading|%s|%d" % (fam, i))
            out.append((name, "\n".join(gen.MAKE[fam](rng))))
    return out


def reductions(text):
    """Drop one command at a time, from the back, keeping the dev line."""
    lines = text.split("\n")
    for i in range(len(lines) - 1, 0, -1):
        yield "\n".join(lines[:i] + lines[i + 1:])
