"""Does the enumerated set separate the wrong readings a solver will actually have?

Per-rule coverage on paper is not coverage. A reading is only measured once it has been built
and run: the ones here come from `emit.py`, so the cheats that ship and the readings measured
here are the same files and cannot drift apart.

    python tools/readingcheck.py page-window-reuse [rounds]
"""
import pathlib
import subprocess
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

# Only the semantic readings. The slow families, the forgery and the isolation probes are not
# readings of the rules and are not measured here.
emit.readings()
READINGS = dict(emit.BUILT)

_TREES = {}
_SEEN = {}


def run(policy, text):
    """Drive one program under one directory of the six files."""
    key = (str(policy), text)
    if key in _SEEN:
        return _SEEN[key]
    here = _TREES.get(str(policy))
    if here is None:
        here = _TREES[str(policy)] = lab.tree(policy)
    room = pathlib.Path(tempfile.mkdtemp(prefix="pwr-read-"))
    prog = room / "p.txt"
    prog.write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
    out = subprocess.run([sys.executable, str(here / "run_kv.py"), str(prog)],
                         capture_output=True, text=True, timeout=120)
    got = ["RAISED", out.stderr.strip().splitlines()[-1]] if out.returncode else \
        out.stdout.splitlines()
    _SEEN[key] = got
    return got


def enumerated():
    return [(name, "\n".join(cases.ops(name))) for name in cases.ORDER]


def generated(n):
    out = []
    small = [f for f, big in gen.FAMILIES if not big]
    per = max(1, n // max(1, len(small)))
    for fam, name, lines in gen.programs("readingcheck", per):
        if fam in small:
            out.append((name, "\n".join(lines)))
    return out
