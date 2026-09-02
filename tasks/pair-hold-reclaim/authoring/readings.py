"""The plausible-but-wrong readings, written down so they can be run.

Per-rule coverage on paper is not coverage: the question is whether a specific wrong
reading survives the whole enumerated set, and the only way to know is to run it. The
readings here are the same anchored swaps the cheat suite is generated from, so the two
cannot drift apart, and a reading this reports as BLIND is one an enumerated case is
missing.

    python3 tools/readingcheck.py pair-hold-reclaim
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import emit  # noqa: E402
import gen  # noqa: E402
import harness  # noqa: E402
import scen  # noqa: E402

REFERENCE = str(TASK / "solution")

_src = {f: emit.strip_doc(v) for f, v in emit.ref_source().items()}
READINGS = {}
for _name, (_note, _files) in emit.variants(_src).items():
    READINGS[_name] = {f: _files[f] for f in emit.FILES if _files[f] != _src[f]}

_staged = {}


def run(policy, text):
    key = str(policy)
    if key not in _staged:
        _staged[key] = harness.stage(TASK / "environment" / "app_src", policy)
    got = harness.drive(_staged[key], [("one", text)])["one"]
    return (got["err"], got["log"], got["state"])


def enumerated():
    return scen.cases()


def generated(n):
    return gen.build("readings", max(1, n))


def reductions(text):
    """Structure-aware candidates: drop a line, or drop a cell and everything naming it."""
    lines = [ln for ln in text.split("\n") if ln.strip()]
    for i in range(len(lines) - 1, -1, -1):
        yield "\n".join(lines[:i] + lines[i + 1:])
    ids = sorted({int(m) for ln in lines for m in re.findall(r"\b\d+\b", ln)}, reverse=True)
    for cid in ids:
        keep = [ln for ln in lines
                if str(cid) not in re.findall(r"\b\d+\b", ln)]
        if keep != lines:
            yield "\n".join(keep)
