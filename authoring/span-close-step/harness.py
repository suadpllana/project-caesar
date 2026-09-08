"""Host emulation for span-close-step.

Builds a runnable tree outside the bundle from the frozen environment modules plus
one policy directory, then runs run scripts against it in-process. Docker is not
available in this workspace, so this stands in for the agent container while
authoring; it is not evidence about the verifier's isolation.
"""
import importlib
import io
import contextlib
import os
import pathlib
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "span-close-step"
ENV = TASK / "environment" / "app_src"
FROZEN = ("__init__.py", "feat.py", "feed.py", "lay.py", "box.py", "ops.py")
POLICY = ("pick.py", "fold.py", "norm.py", "turn.py", "again.py", "keep.py")


def build(policy=None, into=None):
    """Stage a tree: frozen modules from the environment, policy from `policy`."""
    tmp = pathlib.Path(into or tempfile.mkdtemp(prefix="scs-"))
    tree = tmp / "tree"
    if tree.exists():
        shutil.rmtree(tree)
    (tree / "train").mkdir(parents=True)
    shutil.copy(ENV / "run_train.py", tree / "run_train.py")
    for name in FROZEN:
        shutil.copy(ENV / "train" / name, tree / "train" / name)
    src = pathlib.Path(policy) if policy else (ENV / "train")
    for name in POLICY:
        shutil.copy(src / name, tree / "train" / name)
    return tree


class Tree:
    """One staged tree, imported once and reused across runs."""

    def __init__(self, policy=None, into=None):
        self.path = build(policy, into)
        self.tag = "scs_%d" % (abs(hash(str(self.path))) % 10 ** 9)

    def _import(self):
        drop = [m for m in sys.modules if m == "train" or m.startswith("train.")]
        for m in drop:
            del sys.modules[m]
        sys.path.insert(0, str(self.path))
        try:
            box = importlib.import_module("train.box")
            ops = importlib.import_module("train.ops")
        finally:
            sys.path.pop(0)
        return box, ops

    def run(self, lines):
        """Run one script given as a list of text lines; return printed lines."""
        box, ops = self._import()
        run = box.Run()
        out = []
        for ln in lines:
            ln = ln.strip()
            if ln:
                ops.ex(run, tuple(ln.split()), out)
        return out

    def guarded(self, lines):
        """Run, returning (lines, error). A raising policy is a failed run."""
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                return self.run(lines), None
        except Exception as exc:  # policy code under test may raise
            return None, "%s: %s" % (type(exc).__name__, exc)


def script(path):
    return [ln.strip() for ln in pathlib.Path(path).read_text().splitlines() if ln.strip()]


def solution_tree():
    return Tree(TASK / "solution")


def shipped_tree():
    return Tree(None)


if __name__ == "__main__":
    t = solution_tree()
    for arg in sys.argv[1:]:
        print("== %s" % os.path.basename(arg))
        for ln in t.run(script(arg)):
            print(ln)
