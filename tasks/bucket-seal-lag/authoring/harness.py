"""Build a work tree from environment/app_src plus an overlay and drive a plan.

Used by every authoring script here. The overlay is a directory of replacement
files for the four declared artifacts, or None for the tree as it ships.
"""

import importlib
import io
import json
import os
import pathlib
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "environment" / "app_src"
ART = ("flow/emit.py", "flow/route.py", "flow/due.py", "flow/pick.py")


def tree(overlay=None):
    work = pathlib.Path(tempfile.mkdtemp(prefix="bsl-"))
    shutil.copytree(SRC, work / "app")
    if overlay is not None:
        for rel in ART:
            cand = pathlib.Path(overlay) / pathlib.Path(rel).name
            if cand.exists():
                shutil.copyfile(cand, work / "app" / rel)
    return work / "app"


def unload():
    for name in list(sys.modules):
        if name == "flow" or name.startswith("flow."):
            sys.modules.pop(name, None)


def drive(app, text):
    unload()
    sys.path.insert(0, str(app))
    try:
        gr = importlib.import_module("flow.gr")
        mach = importlib.import_module("flow.mach")
        rows = []
        m = mach.Mach(gr.parse(text), rows.append)
        m.run()
        got = {"tr": [list(r) for r in rows], "sk": sinks(rows)}
        return got
    finally:
        sys.path.remove(str(app))
        unload()


def sinks(rows):
    out = {}
    for r in rows:
        if r[0] == "sk":
            out.setdefault(r[2], []).append(r[3])
    return out


def run(overlay, text):
    app = tree(overlay)
    try:
        return drive(app, text)
    finally:
        shutil.rmtree(app.parent, ignore_errors=True)
