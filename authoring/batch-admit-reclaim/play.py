"""Run one policy tree over one trace, in process.

The frozen tree imports its four policy modules by name, so a variant is just a
directory holding the frozen files with those four replaced. Modules are dropped
from sys.modules between runs, which is what makes it safe to play a dozen
policies over three hundred traces without a subprocess apiece.
"""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "batch-admit-reclaim")
SRC = os.path.join(TASK, "environment", "app_src")
SOL = os.path.join(TASK, "solution")
POLICY = ("fit.py", "room.py", "back.py", "pick.py")


def drop():
    for name in [n for n in list(sys.modules) if n == "eng" or n.startswith("eng.")]:
        sys.modules.pop(name, None)


def build(where, files):
    if os.path.isdir(where):
        shutil.rmtree(where)
    shutil.copytree(SRC, where)
    for name, text in files.items():
        with open(os.path.join(where, "eng", name), "w") as fh:
            fh.write(text)
    return where


def reference(where):
    files = {}
    for name in POLICY:
        with open(os.path.join(SOL, name)) as fh:
            files[name] = fh.read()
    return build(where, files)


def rows(tree, text):
    drop()
    sys.path.insert(0, tree)
    try:
        from eng.rd import parse
        from eng.step import Eng
        out = []
        Eng(parse(text), out.append).run()
        return [tuple(x) for x in out]
    finally:
        if tree in sys.path:
            sys.path.remove(tree)
        drop()


def safe(tree, text):
    try:
        return rows(tree, text)
    except Exception as exc:
        return [("torn", type(exc).__name__, str(exc)[:60])]
