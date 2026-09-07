"""Shared plumbing for the authoring gates: build a tree, run a program through it, diff."""
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "unit-take-bind"
SRC = TASK / "environment" / "app_src"
REF = TASK / "solution"
PARTS = ("step.py", "show.py", "pick.py", "turn.py")

sys.path.insert(0, str(TASK / "tests"))


def tree(swap=None, base=None):
    """A fresh copy of the shipped tree with `swap` (dir or dict) laid over res/."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="utb-"))
    dst = tmp / "app"
    shutil.copytree(base or SRC, dst)
    if isinstance(swap, dict):
        for name, text in swap.items():
            (dst / "res" / name).write_text(text, encoding="utf-8", newline="\n")
    elif swap is not None:
        for name in PARTS:
            one = pathlib.Path(swap) / name
            if one.is_file():
                shutil.copy(one, dst / "res" / name)
    return dst


def run_prog(dst, lines, limit=120):
    """Run one program in `dst` as a subprocess; returns (lines, error-or-None)."""
    path = dst / "_p.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    try:
        got = subprocess.run(
            [sys.executable, "run_prog.py", "_p.txt"],
            cwd=str(dst), capture_output=True, text=True, timeout=limit)
    except subprocess.TimeoutExpired:
        return None, "timeout"
    if got.returncode != 0:
        return None, got.stderr.strip().splitlines()[-1:] or ["exit %d" % got.returncode]
    return got.stdout.splitlines(), None


def in_proc(dst):
    """Import the engine in `dst` once and return a callable, for the fast bulk loops."""
    import importlib
    for mod in [m for m in list(sys.modules) if m.split(".")[0] in ("prog", "res")]:
        del sys.modules[mod]
    sys.path.insert(0, str(dst))
    deckmod = importlib.import_module("prog.deck")
    read = importlib.import_module("prog.read")
    tell = importlib.import_module("res.tell")
    turn = importlib.import_module("res.turn")

    def go(lines):
        prog = read.load("\n".join(lines) + "\n")
        deck = turn.run(prog)
        return [tell.line(un, x, deckmod.at(deck, un, x)) for un, x in prog.asks]

    return go, lambda: sys.path.remove(str(dst))
