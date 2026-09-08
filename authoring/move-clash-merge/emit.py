"""Run scenarios through a chosen policy directory, in a scratch tree outside the bundle.

The frozen part of the app tree is copied out of environment/app_src, the five policy files
are laid over it from whichever directory was named, and each scenario is replayed in a fresh
interpreter state. Nothing is written inside tasks/<slug>/.
"""
import importlib
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "move-clash-merge"
APP = TASK / "environment" / "app_src"
PARTS = ("live.py", "spot.py", "name.py", "book.py", "step.py")


def stage(policy):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="mcm-"))
    tree = tmp / "app"
    shutil.copytree(APP, tree, ignore=shutil.ignore_patterns("__pycache__"))
    for part in PARTS:
        one = pathlib.Path(policy) / part
        if one.is_file():
            shutil.copy(one, tree / "mrg" / part)
    return tmp, tree


def trace(tree, text):
    src = "import sys\nsys.path.insert(0, %r)\nfrom mrg import drive\n" \
          "drive.go(sys.stdin.read().split(chr(10)), print)\n" % str(tree)
    got = subprocess.run([sys.executable, "-c", src], input=text, capture_output=True,
                         text=True, timeout=120)
    if got.returncode != 0:
        return None, got.stderr.strip().splitlines()[-1:]
    return got.stdout.rstrip("\n").split("\n") if got.stdout.strip() else [], None


def runner(policy):
    tmp, tree = stage(policy)
    sys.path.insert(0, str(tree))
    for name in [n for n in sys.modules if n == "mrg" or n.startswith("mrg.")]:
        del sys.modules[name]
    drive = importlib.import_module("mrg.drive")

    def go(text):
        rows = []
        for name in [n for n in sys.modules if n == "mrg" or n.startswith("mrg.")]:
            del sys.modules[name]
        importlib.import_module("mrg.drive").go(text.split("\n"), rows.append)
        return rows

    del drive
    return go, tmp
