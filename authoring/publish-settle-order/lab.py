"""Host-side staging for authoring runs.

Builds a throwaway copy of the agent tree outside the bundle, drops an overlay of link modules
on top of it, and runs programs in a fresh interpreter state. Nothing here ships: it is the
cheap loop that keeps Docker out of the inner cycle.
"""
from __future__ import annotations

import importlib
import pathlib
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "publish-settle-order"
SRC = TASK / "environment" / "app_src"
PARTS = ("walk.py", "view.py", "pick.py", "site.py", "want.py", "drop.py")

_MODS = ("ops", "reg", "reg.tab", "reg.text", "reg.decl", "reg.order", "reg.hold",
         "reg.say", "link", "link.walk", "link.view", "link.pick", "link.site",
         "link.want", "link.drop")


def stage(overlay: pathlib.Path | None) -> pathlib.Path:
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="pso-"))
    tree = tmp / "tree"
    shutil.copytree(SRC, tree)
    if overlay is not None:
        for name in PARTS:
            one = overlay / name
            if one.is_file():
                shutil.copy(one, tree / "link" / name)
    return tree


class Lab:
    """One staged tree, with the modules imported from it."""

    def __init__(self, overlay: pathlib.Path | None = None):
        self.tree = stage(overlay)
        for m in _MODS:
            sys.modules.pop(m, None)
        sys.path.insert(0, str(self.tree))
        self.ops = importlib.import_module("ops")
        self.tab = importlib.import_module("reg.tab")
        self.order = importlib.import_module("reg.order")
        sys.path.pop(0)

    def close(self):
        for m in _MODS:
            sys.modules.pop(m, None)
        shutil.rmtree(self.tree.parent, ignore_errors=True)

    def run(self, lines):
        h = self.tab.Host()
        out = []
        for ln in lines:
            self.ops.ex(h, tuple(ln.split()), out)
        return out


def prog(path):
    return [ln.strip() for ln in pathlib.Path(path).read_text().splitlines() if ln.strip()]
