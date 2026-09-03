"""The plausible-but-wrong readings, written down so they can be run.

Per-rule coverage on paper is not coverage. The question is whether a SPECIFIC wrong
reading survives the whole enumerated set, and the only way to know is to write that
reading down and run it. A reading this reports as BLIND is one the enumerated set is
missing, and the counterexample it prints is the panel to add.

The readings are the same anchored swaps the cheat suite is generated from, so the two
cannot drift apart.

    python3 tools/readingcheck.py panel-settle-order
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import cases  # noqa: E402
import emit  # noqa: E402
import gen  # noqa: E402
import harness  # noqa: E402

REFERENCE = str(TASK / "solution")

_src = emit.ref_source()
READINGS = {}
for _name, (_note, _files) in emit.wrong(_src).items():
    READINGS[_name] = {f: _files[f] for f in emit.FILES if _files[f] != _src[f]}

_cache = {}


def run(policy, text):
    key = str(policy)
    if key not in _cache:
        _cache[key] = harness.stage(policy)
    got = harness.drive(_cache[key], [("one", text)])["one"]
    return (got["err"], got["log"], got["dump"])


def enumerated():
    return [(n, cases.PANELS[n]) for n in sorted(cases.PANELS)]


def generated(n):
    return gen.build("readings", max(1, n))


def reductions(text):
    """Structure-aware shrinking: drop a line, or drop an entry and every mention of it."""
    lines = [ln for ln in text.split("\n") if ln.strip()]
    for i in range(len(lines) - 1, -1, -1):
        yield "\n".join(lines[:i] + lines[i + 1:]) + "\n"
    names = []
    for ln in lines:
        b = ln.split()
        if b and b[0] in ("F", "G"):
            names.append(b[1])
    for nm in names:
        keep = [ln for ln in lines if nm not in ln.split() and nm not in ln.replace("(", " ").replace(")", " ").replace(",", " ").split()]
        if keep != lines:
            yield "\n".join(keep) + "\n"
