"""Does the enumerated set separate the wrong readings a solver will actually have?

Per-rule coverage on paper is not coverage. Every reading here is a working service built by
make_readings.py from the reference with one decision taken the other way, so the readings
measured here and the cheats that ship come from the same files and cannot drift apart.

The two resource readings are not measured here: `pre-copy` and `no-memo` print exactly the
reference's trace on everything they finish, and only the stated limit separates them. They are
timed by time_slow.py and ship as cheats.

    python tools/readingcheck.py trial-keep-adopt [rounds]
"""
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
import cases  # noqa: E402
import gen  # noqa: E402

REFERENCE = str(lab.TASK / "solution")
SLOW = ("pre-copy", "no-memo", "reads-set")
ROOM = HERE / "readings"

READINGS = {}
for _d in sorted(ROOM.iterdir()) if ROOM.is_dir() else []:
    if not _d.is_dir() or _d.name in SLOW:
        continue
    READINGS[_d.name] = {p.name: p.read_text(encoding="utf-8") for p in sorted(_d.glob("*.py"))}

_TREES = {}


def run(policy, text):
    here = _TREES.get(str(policy))
    if here is None:
        here = _TREES[str(policy)] = lab.tree(policy)
    room = pathlib.Path(tempfile.mkdtemp(prefix="tka-read-"))
    prog = room / "p.txt"
    prog.write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
    try:
        return lab.run(here, prog, timeout=60)
    except RuntimeError as exc:
        return ["RAISED", str(exc).splitlines()[-1]]
    except Exception:
        return ["TIMEOUT"]


def enumerated():
    return [(name, "\n".join(cases.ops(name))) for name in cases.ORDER]


def generated(n):
    out = []
    per = max(1, n // 10)
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(per):
            name = "%s-%d" % (fam, i)
            out.append((name, "\n".join(gen.one(fam, "reading/%s" % name))))
    return out


def reductions(text):
    """A program is lines, but a block is a group of them, so drop whole blocks first."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("try "):
            for j in range(i, len(lines)):
                if lines[j] == "end":
                    yield "\n".join(lines[:i] + lines[j + 1:])
                    break
    for i in range(len(lines) - 1, -1, -1):
        w = lines[i].split()
        if w and w[0] in ("ask", "set", "pin", "free"):
            yield "\n".join(lines[:i] + lines[i + 1:])
    for i in range(len(lines) - 1, -1, -1):
        yield "\n".join(lines[:i] + lines[i + 1:])
