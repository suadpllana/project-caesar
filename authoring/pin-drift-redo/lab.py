"""Host emulation: build a tree, run programs through it, compare with the sealed model.

Docker is not available in this workspace, so every local gate runs here: a fresh temporary
tree is assembled from environment/app_src, one candidate's files are laid over `led/`, and
the programs are run in a subprocess so a candidate cannot pollute this interpreter.

This is not the container run. It does not exercise the privilege drop, the locked reward
channel or the root-owned seal; tools/docker_trial.py does that where a daemon exists.
"""
from __future__ import annotations

import sys as _sys

# Importing the bundle's own modules must not leave a __pycache__ inside tasks/<slug>/:
# authoring scratch that lands in the task folder has been packaged before.
_sys.dont_write_bytecode = True

import importlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "pin-drift-redo"
APP = TASK / "environment" / "app_src"
PARTS = ("ver.py", "take.py", "hold.py", "work.py", "step.py", "close.py")

RUNNER = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
import run_led
progs = json.loads(open(sys.argv[2]).read())
out = []
for name, lines in progs:
    try:
        out.append([name, run_led.run("\n".join(lines) + "\n"), None])
    except Exception as exc:
        out.append([name, None, "%s: %s" % (type(exc).__name__, exc)])
open(sys.argv[3], "w").write(json.dumps(out))
"""


def tree(over: Path | None = None, room: Path | None = None) -> Path:
    """A copy of the shipped tree, with `over`'s six files laid into led/ when given."""
    room = Path(room or tempfile.mkdtemp(prefix="pdr-"))
    here = room / "app"
    if here.exists():
        shutil.rmtree(here)
    shutil.copytree(APP, here)
    if over is not None:
        for part in PARTS:
            one = Path(over) / part
            if one.is_file():
                shutil.copy(one, here / "led" / part)
    return here


def run(progs, over: Path | None = None, seconds: int = 900):
    """Run [(name, lines)] through a tree; returns {name: (lines or None, error or None)}."""
    room = Path(tempfile.mkdtemp(prefix="pdr-"))
    try:
        here = tree(over, room)
        (room / "runner.py").write_text(RUNNER, encoding="utf-8")
        (room / "progs.json").write_text(json.dumps(progs), encoding="utf-8")
        done = subprocess.run(
            [sys.executable, str(room / "runner.py"), str(here),
             str(room / "progs.json"), str(room / "out.json")],
            capture_output=True, text=True, timeout=seconds)
        if done.returncode != 0:
            return {name: (None, "runner died: %s" % done.stderr.strip()[-400:])
                    for name, _lines in progs}
        got = json.loads((room / "out.json").read_text(encoding="utf-8"))
        return {name: (lines, err) for name, lines, err in got}
    finally:
        shutil.rmtree(room, ignore_errors=True)


def inproc(here: Path):
    """Import run_led out of `here`, dropping any copy imported before."""
    for name in [n for n in sys.modules if n == "run_led" or n == "led" or n.startswith("led.")]:
        del sys.modules[name]
    sys.path.insert(0, str(here))
    try:
        return importlib.import_module("run_led")
    finally:
        sys.path.remove(str(here))


def run_text(here: Path, text: str):
    """Run one program in this process. Fast, and safe for semantic variants only."""
    mod = inproc(here)
    try:
        return mod.run(text if text.endswith("\n") else text + "\n")
    except Exception as exc:          # a wrong reading may well blow up
        return ["RAISED", type(exc).__name__]


def sealed():
    """The shipped case list and generator, and the sealed model."""
    for where in (TASK / "tests", TASK / "tests" / "seal"):
        if str(where) not in sys.path:
            sys.path.insert(0, str(where))
    import cases
    import gen
    import model
    return cases, gen, model


def files_tree(files: dict):
    """A staged tree with one dict of led files laid over the shipped ones."""
    here = tree(None)
    for part, text in files.items():
        (here / "led" / part).write_text(text, encoding="utf-8", newline="\n")
    return here
