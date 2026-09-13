"""Host-side staging for authoring runs.

Builds a throwaway copy of the agent tree outside the bundle, drops an overlay of cfg modules
on top of it, and runs plans in a fresh interpreter state. Nothing here ships.
"""
from __future__ import annotations

import importlib
import pathlib
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "fix-layered-config"
SRC = TASK / "environment" / "app_src"
PARTS = ("pile.py", "past.py", "made.py", "roll.py", "work.py", "ans.py")

_MODS = ("cfg", "cfg.ans", "cfg.lex", "cfg.made", "cfg.past", "cfg.pile", "cfg.roll",
         "cfg.say", "cfg.work")


def stage(overlay: pathlib.Path | None) -> pathlib.Path:
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="flc-"))
    tree = tmp / "tree"
    shutil.copytree(SRC, tree, ignore=shutil.ignore_patterns("__pycache__", "plans"))
    if overlay is not None:
        for name in PARTS:
            one = overlay / name
            if one.is_file():
                shutil.copy(one, tree / "cfg" / name)
    return tree


class Lab:
    """One staged tree, with the modules imported from it."""

    def __init__(self, overlay: pathlib.Path | None = None):
        self.tree = stage(overlay)
        for m in _MODS:
            sys.modules.pop(m, None)
        sys.path.insert(0, str(self.tree))
        self.lex = importlib.import_module("cfg.lex")
        self.past = importlib.import_module("cfg.past")
        self.ans = importlib.import_module("cfg.ans")
        sys.path.pop(0)

    def close(self):
        for m in _MODS:
            sys.modules.pop(m, None)
        shutil.rmtree(self.tree.parent, ignore_errors=True)

    def run(self, text):
        plan = self.lex.parse(text)
        hist = self.past.build(plan)
        return [self.ans.answer(hist, q) for q in plan.asks]
