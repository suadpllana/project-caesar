"""Stage a tree, drive streams through it, in this process.

The two-image trial in tools/docker_trial2.py is what actually exercises the sandbox. This
is the fast loop underneath it: a real copy of the shipped tree, a real overlay of whatever
policy is being graded, the real book, and the real streams. It does not cover the
privilege drop, the locked reward channel, the root-only ground truth or the teardown, and
anything reported from here has to say so.
"""
import importlib
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "environment" / "app_src"
EDIT = ("drn.py", "gvp.py", "rnd.py", "due.py")


def stage(src=None, overlay=None):
    d = Path(tempfile.mkdtemp(prefix="qdr_"))
    shutil.copytree(src or SRC, d / "app", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if overlay is not None:
        for f in EDIT:
            s = Path(overlay) / f
            if s.exists():
                shutil.copy2(s, d / "app" / "house" / f)
    return d


def _fresh(root):
    for m in [m for m in list(sys.modules) if m == "house" or m.startswith("house.")]:
        del sys.modules[m]
    sys.path.insert(0, str(root))
    return sys.path


def one(tree, text):
    root = Path(tree) / "app"
    old = list(sys.path)
    _fresh(root)
    try:
        bk = importlib.import_module("house.bk")
        ev = importlib.import_module("house.ev")
        rnd = importlib.import_module("house.rnd")
        who, run, rows = ev.read(text)
        log = []
        b = bk.Book(who, lambda *a: log.append(tuple(a)))
        for t in range(1, run + 1):
            ev.feed(b, rows, t)
            rnd.turn(b, t)
        return {"err": None, "log": log, "sheet": b.sheet()}
    except BaseException as e:
        return {"err": "%s: %s" % (type(e).__name__, e), "log": [], "sheet": {}}
    finally:
        sys.path[:] = old
        for m in [m for m in list(sys.modules) if m == "house" or m.startswith("house.")]:
            del sys.modules[m]


def drive(tree, streams):
    return {name: one(tree, text) for name, text in streams}


def run(policy, text):
    d = stage(None, policy)
    try:
        r = one(d, text)
        return {"log": [list(x) for x in r["log"]], "sheet": r["sheet"]}
    finally:
        shutil.rmtree(d, ignore_errors=True)
