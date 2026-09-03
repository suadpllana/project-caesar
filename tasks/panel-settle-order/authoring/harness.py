"""Stage the shipped tree with an overlay and drive panels in-process.

Every authoring script here uses this. The tree is imported fresh for each panel, the
way the verifier's runner does it, so nothing a module keeps at import time can carry
one panel's state into the next.
"""

import importlib
import pathlib
import shutil
import sys
import tempfile

TASK = pathlib.Path(__file__).resolve().parent.parent
SHIP = TASK / "environment" / "app_src"
FILES = ("ord.py", "wire.py", "trip.py", "same.py")


def stage(overlay=None, files=None):
    work = pathlib.Path(tempfile.mkdtemp(prefix="pso-"))
    tree = work / "app"
    shutil.copytree(SHIP, tree)
    if overlay:
        for f in files or FILES:
            src = pathlib.Path(overlay) / f
            if src.is_file():
                shutil.copy2(src, tree / "pnl" / f)
    return tree


def drive(tree, panels):
    tree = str(tree)
    out = {}
    for name, text in panels:
        for m in [x for x in sorted(sys.modules) if x == "pnl" or x.startswith("pnl.")]:
            del sys.modules[m]
        sys.path.insert(0, tree)
        try:
            lex = importlib.import_module("pnl.lex")
            loop = importlib.import_module("pnl.loop")
            feeds, gauges, latch, rounds, order = lex.parse(text)
            rows = []
            err = None
            dump = ()
            try:
                lp = loop.Loop(feeds, gauges, latch, rounds, order, rows.append)
                dump = lp.go()
            except Exception as exc:
                err = "%s: %s" % (type(exc).__name__, exc)
            out[name] = {"log": tuple(rows), "dump": tuple(dump), "err": err}
        finally:
            sys.path.remove(tree)
    return out


def panels_in(d):
    d = pathlib.Path(d)
    return [(p.stem, p.read_text(encoding="utf-8")) for p in sorted(d.glob("*.txt"))]
