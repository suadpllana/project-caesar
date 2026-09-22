"""Host-side bench: build a tree, lay an implementation over it, run programs.

Everything is staged under tempfile.mkdtemp outside the bundle, so no authoring scratch can
end up in a package (CLAUDE.md, 2026-09-06).
"""
import importlib
import pathlib
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "beam-ban-carry"
PARTS = ("sc.py", "rep.py", "keep.py", "pick.py", "walk.py", "halt.py")


def tree(over=None):
    """A copy of the shipped tree with `over`'s six parts laid into bm/, if given."""
    room = pathlib.Path(tempfile.mkdtemp(prefix="bbc-"))
    here = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", here)
    if over is not None:
        for part in PARTS:
            src = pathlib.Path(over) / part
            if src.is_file():
                shutil.copy(src, here / "bm" / part)
    return here


def loader(here):
    """A run(text) -> lines callable bound to one staged tree."""
    here = str(here)
    def run(text):
        for name in [m for m in list(sys.modules) if m == "run_beam" or m.startswith("bm")]:
            del sys.modules[name]
        sys.path.insert(0, here)
        try:
            mod = importlib.import_module("run_beam")
            return mod.run(text)
        finally:
            sys.path.remove(here)
    return run


def model():
    sys.path.insert(0, str(TASK / "tests" / "seal"))
    import model as mod
    importlib.reload(mod)
    return lambda text: mod.expect(text.splitlines())
