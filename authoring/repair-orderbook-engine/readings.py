"""Whole-solver wrong readings, in the contract tools/readingcheck.py reads.

Each reading is a complete, runnable engine a submission could plausibly hand in - the
reference with exactly one decision made the way a solver who missed one piece would make
it, or a previous reference in full. They are not ablations of a file that ships correct.

The readings are the reading cheats under tasks/repair-orderbook-engine/cheat/, lifted
out of their heredocs here rather than restated, so this table cannot drift from the
scripts a reviewer reads. The isolation and forgery probes are not readings and are
measured by cheat_report.py instead.

    python tools/readingcheck.py repair-orderbook-engine
"""

import importlib
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "repair-orderbook-engine"))
REFERENCE = os.path.join(TASK, "solution")
APPSRC = os.path.join(TASK, "environment", "app_src")
CHEATS = os.path.join(TASK, "cheat")

sys.path.insert(0, os.path.join(TASK, "tests"))
import cases  # noqa: E402
import gen  # noqa: E402

PARTS = ("take.py", "shown.py", "hand.py", "hold.py", "trip.py")
BLOCK = re.compile(r"cat > \"\$APP/eng/(\w+\.py)\" <<'(\w+)'\n(.*?)\n\2\n", re.S)


def _files(name):
    """The five modules a cheat script would install, lifted out of its heredocs."""
    with open(os.path.join(CHEATS, "cheat-%s.sh" % name), encoding="utf-8") as fh:
        body = fh.read()
    out = {}
    for fn, _tag, src in BLOCK.findall(body):
        if fn in PARTS:
            out[fn] = src + "\n"
    if not out:
        raise SystemExit("no modules found in cheat-%s.sh" % name)
    return out


READINGS = {
    # shown.py - what may be taken from a resting order now, and where it goes after.
    "avail-full": _files("avail-full"),
    "keep-front": _files("keep-front"),
    # take.py - the walk itself.
    "band-skips": _files("band-skips"),
    "band-fixed": _files("band-fixed"),
    "trip-after-walk": _files("trip-after-walk"),
    # hold.py - all-or-nothing admission under order pace.
    "whole-band-fixed": _files("whole-band-fixed"),
    "whole-no-undo": _files("whole-no-undo"),
    "whole-ignores-hand": _files("whole-ignores-hand"),
    "whole-ignores-band": _files("whole-ignores-band"),
    "whole-as-day": _files("whole-as-day"),
    # trip.py - activation.
    "trip-by-price": _files("trip-by-price"),
    "trip-at-park": _files("trip-at-park"),
    # hand.py - the file that ships correct.
    "self-trade": _files("self-trade"),
    # fill pace - descendant execution and nested restoration.
    "capacity-only": _files("capacity-only"),
    "child-before-disclosure": _files("child-before-disclosure"),
    "forget-trigger-rollback": _files("forget-trigger-rollback"),
    "inner-frame-only": _files("inner-frame-only"),
    "last-fill-batch": _files("last-fill-batch"),
}

_TREES = {}


def _tree(policy):
    key = os.path.abspath(policy)
    if key in _TREES:
        return _TREES[key]
    root = tempfile.mkdtemp(prefix="roe-")
    shutil.copytree(os.path.join(APPSRC, "mkt"), os.path.join(root, "mkt"),
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    os.makedirs(os.path.join(root, "eng"))
    open(os.path.join(root, "eng", "__init__.py"), "w").close()
    for fn in PARTS:
        # The verifier overlays the declared artifacts onto the shipped tree, so a module
        # a policy does not carry - the reference ships no hand.py, because the shipped
        # one is right - is the shipped one.
        src = os.path.join(policy, fn)
        if not os.path.isfile(src):
            src = os.path.join(APPSRC, "eng", fn)
        shutil.copyfile(src, os.path.join(root, "eng", fn))
    _TREES[key] = root
    return root


def run(policy, text):
    """Drive one session under one policy directory, through the shipped runtime."""
    root = _tree(policy)
    for name in list(sys.modules):
        if name == "mkt" or name.startswith("mkt.") or name == "eng" or name.startswith("eng."):
            del sys.modules[name]
    sys.path.insert(0, root)
    try:
        rd = importlib.import_module("mkt.rd")
        drv = importlib.import_module("mkt.drv")
        cap, mark, msgs = rd.read(text)
        rows = []
        drv.drive(cap, mark, msgs, rows.append)
        return tuple(rows)
    finally:
        sys.path.remove(root)


def enumerated():
    return sorted(cases.SESS.items())


def generated(n):
    return gen.batch("readingcheck", n) + gen.fill_batch("readingcheck", max(1, n // 3))


def reductions(text):
    lines = text.split("\n")
    head = [i for i, ln in enumerate(lines) if ln[:3] in ("cap", "mar", "pac")]
    body = [i for i in range(len(lines)) if i not in head and lines[i].strip()]
    for i in reversed(body):
        yield "\n".join(lines[:i] + lines[i + 1:])
