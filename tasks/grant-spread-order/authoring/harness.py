"""Drive the policy kernel over a journal, with any set of decision files overlaid.

Used by every authoring script here. It copies environment/app_src into a scratch tree,
overlays the files it is given, imports that tree fresh, and returns the row list the
frozen driver emitted. Nothing in here is shipped.
"""

import importlib
import pathlib
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "environment" / "app_src"
PARTS = ("spread.py", "weigh.py", "graft.py", "crowd.py")


def tree(over=None):
    d = pathlib.Path(tempfile.mkdtemp(prefix="gso-"))
    shutil.copytree(SRC, d / "app", dirs_exist_ok=False)
    if over:
        for name in PARTS:
            cand = pathlib.Path(over) / name
            if cand.is_file():
                shutil.copyfile(cand, d / "app" / "pol" / name)
    return d


def drop():
    for n in [m for m in sys.modules if m == "pol" or m.startswith("pol.")]:
        sys.modules.pop(n, None)


def run(text, over=None, keep=False):
    d = tree(over)
    sys.path.insert(0, str(d / "app"))
    try:
        drop()
        jrn = importlib.import_module("pol.jrn")
        drv = importlib.import_module("pol.drv")
        rows = []
        drv.Drv(jrn.parse(text), rows.append).go()
        return rows
    finally:
        sys.path.remove(str(d / "app"))
        drop()
        if not keep:
            shutil.rmtree(d, ignore_errors=True)


def ref(text):
    return run(text, ROOT / "solution")


def shipped(text):
    return run(text)
