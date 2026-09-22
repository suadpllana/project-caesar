"""A fresh copy of the shipped tree with an editable-file set laid over it, as a runner.

Every authoring check runs agent-shaped code this way, so what is measured is the shipped
engine with three files replaced - the same shape the verifier's worker builds. The copy lives
in a temporary directory outside the bundle (CLAUDE.md: authoring scratch inside the task
folder ships).
"""
import importlib
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
APP = os.path.join(ROOT, "tasks", "blank-fill-sure", "environment", "app_src")
PARTS = ("cmp.py", "join.py", "keep.py")


def build(parts_dir):
    room = tempfile.mkdtemp(prefix="bfs-tree-")
    app = os.path.join(room, "app")
    shutil.copytree(APP, app)
    if parts_dir:
        for part in PARTS:
            src = os.path.join(parts_dir, part)
            if os.path.isfile(src):
                shutil.copy(src, os.path.join(app, "rs", part))
    return app


def runner(parts_dir):
    """run(text) -> report lines, for the tree built from parts_dir (None: as shipped)."""
    app = build(parts_dir)
    for m in list(sys.modules):
        if m == "rs" or m.startswith("rs.") or m == "run_ask":
            del sys.modules[m]
    sys.path.insert(0, app)
    try:
        mod = importlib.import_module("run_ask")
    finally:
        sys.path.remove(app)
    return mod.run
