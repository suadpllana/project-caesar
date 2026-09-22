"""Host emulation: lay a set of engine files over the shipped tree and run programs.

Everything is written into a tempfile.mkdtemp outside the bundle, so an authoring run in
flight can never be zipped by scripts/package.py.
"""
import importlib
import pathlib
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "scan-chunk-pick"
PARTS = ("hdr", "dct", "live", "pick", "step", "proj")


def tree(src=None):
    room = pathlib.Path(tempfile.mkdtemp(prefix="scp-"))
    here = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", here)
    if src is not None:
        src = pathlib.Path(src)
        for part in PARTS:
            one = src / (part + ".py")
            if one.is_file():
                shutil.copy(one, here / "scn" / (part + ".py"))
    return here


def engine(here):
    for mod in [m for m in list(sys.modules) if m == "run_scan" or m.startswith("scn")]:
        del sys.modules[mod]
    sys.path.insert(0, str(here))
    try:
        return importlib.import_module("run_scan")
    finally:
        sys.path.remove(str(here))
