"""Assemble a tree from the shipped environment plus an overlay, and drive programs through it.

Nothing here writes inside the task folder: every tree is a copy under tempfile.mkdtemp,
outside the bundle, thrown away with the process. That is the rule the packaging lesson came
from - authoring scratch inside the task folder ships.

An engine is a persistent child process holding one tree, because the checks that use this
alternate between two policies on every program and re-importing a tree per call is most of
the run. A child that dies takes its answer with it and says so rather than hanging.
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "widen-pin-bind"
SRC = TASK / "environment" / "app_src"
SOL = TASK / "solution"
PARTS = ("kind.py", "pick.py", "pin.py", "cost.py", "best.py", "walk.py")

DRIVER = """
import json
import sys
sys.setrecursionlimit(20000)
sys.path.insert(0, %r)
import run_bind
for row in sys.stdin:
    text = json.loads(row)
    try:
        out = run_bind.run(text)
    except Exception as exc:
        out = ["RAISED " + type(exc).__name__]
    sys.stdout.write(json.dumps(out) + "\\n")
    sys.stdout.flush()
"""


def tree(overlay=None):
    """A copy of the shipped tree with `overlay`'s six files laid over it."""
    room = pathlib.Path(tempfile.mkdtemp(prefix="wpb-"))
    here = room / "app"
    shutil.copytree(SRC, here)
    if overlay is not None:
        for part in PARTS:
            src = pathlib.Path(overlay) / part
            if src.is_file():
                shutil.copy(src, here / "res" / part)
    return here


class Engine:
    """One tree, held open in a child process."""

    def __init__(self, here):
        self.here = pathlib.Path(here)
        self.proc = None
        self.start()

    def start(self):
        self.proc = subprocess.Popen(
            [sys.executable, "-u", "-c", DRIVER % str(self.here)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

    def run(self, text):
        if not text.endswith("\n"):
            text += "\n"
        if self.proc.poll() is not None:
            self.start()
        try:
            self.proc.stdin.write(json.dumps(text) + "\n")
            self.proc.stdin.flush()
            row = self.proc.stdout.readline()
        except (BrokenPipeError, ValueError):
            row = ""
        if not row:
            self.start()
            return ["DIED"]
        return json.loads(row)

    def close(self):
        if self.proc and self.proc.poll() is None:
            self.proc.kill()


_ENGINES = {}


def engine(overlay=None):
    """A cached engine over a tree built from `overlay` (None for the shipped tree)."""
    key = str(overlay)
    got = _ENGINES.get(key)
    if got is None:
        got = _ENGINES[key] = Engine(tree(overlay))
    return got


def run_text(overlay, text):
    return engine(overlay).run(text)


def runner(overlay=SOL):
    """An in-process `run(text)` for a single tree, for scripts that use only one."""
    here = tree(overlay)
    for name in [k for k in list(sys.modules)
                 if k == "run_bind" or k == "res" or k.startswith("res.")]:
        del sys.modules[name]
    sys.path.insert(0, str(here))
    import run_bind
    return run_bind.run


def sealed():
    """The verifier's own case list, generator and model."""
    sys.path.insert(0, str(TASK / "tests"))
    sys.path.insert(0, str(TASK / "tests" / "seal"))
    import cases
    import gen
    import model
    return cases, gen, model
