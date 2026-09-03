"""Plausible-but-wrong readings, and whether the enumerated set actually separates them.

Per-rule coverage on paper is not coverage. The question is whether a SPECIFIC wrong reading
survives the whole hand-written set, and the only way to know is to write the reading down and
run it. These are the same readings the cheat suite ships, minus the reward and attestation
probes, which are not readings of anything.
"""
import importlib
import json
import os
import shutil
import sys
import tempfile

import stage

REFERENCE = stage.SOLUTION
_TREES = {}


def _tree(policy):
    """Stage a tree for one policy directory and remember it."""
    key = os.path.abspath(policy)
    if key not in _TREES:
        files = [os.path.join(policy, f) for f in sorted(os.listdir(policy))
                 if f.endswith(".py")]
        _TREES[key] = stage.tree(files, into=tempfile.mkdtemp(prefix="ahc-read-"))
    return _TREES[key]


def _fresh(app):
    for name in [n for n in sys.modules if n == "srv" or n.startswith("srv.")]:
        del sys.modules[name]
    while app in sys.path:
        sys.path.remove(app)
    sys.path.insert(0, app)
    return importlib.import_module("srv.wire")


def _job(text):
    raw = json.loads(text)
    return {"stops": [s.encode("latin1") for s in raw["stops"]],
            "scripts": {k: [t.encode("latin1") for t in v]
                        for k, v in sorted(raw["scripts"].items())},
            "turns": dict(sorted(raw["turns"].items()))}


def run(policy, text):
    wire = _fresh(_tree(policy))
    try:
        return json.dumps(wire.drive(_job(text)))
    except Exception as exc:
        return "boom:" + type(exc).__name__


def _text(job):
    return json.dumps({"stops": [s.decode("latin1") for s in job["stops"]],
                       "scripts": {k: [t.decode("latin1") for t in v]
                                   for k, v in sorted(job["scripts"].items())},
                       "turns": dict(sorted(job["turns"].items()))}, sort_keys=True)


def enumerated():
    sys.path.insert(0, stage.TESTS)
    import cases
    return [(name, _text(job)) for name, job in cases.jobs()]


def generated(n):
    sys.path.insert(0, stage.TESTS)
    import gen
    return [(name, _text(job)) for name, job in gen.jobs("readingcheck", n)]


def _swaps():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import emit
    out = {}
    for name, _why, which, old, new in emit.SWAPS:
        base = emit.REF_HOLD if which == "hold" else emit.REF_PICK
        body = new if old is None else base.replace(old, new)
        files = {"hold.py": emit.REF_HOLD, "pick.py": emit.REF_PICK}
        files["hold.py" if which == "hold" else "pick.py"] = body
        out[name] = files
    for name, _why, files in emit.WHOLE:
        both = {"hold.py": emit.REF_HOLD, "pick.py": emit.REF_PICK}
        both.update(files)
        out[name] = both
    return out


READINGS = _swaps()
