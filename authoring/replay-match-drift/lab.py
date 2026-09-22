"""Shared bench for the authoring scripts: stage a policy, run a run file, reach the seal.

Everything here writes into a fresh temporary directory outside the bundle. Authoring
scratch left inside the task folder has shipped before.
"""
import pathlib
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "replay-match-drift"
SOL = TASK / "solution"
SRC = TASK / "environment" / "app_src"
PARTS = ("tab.py", "edge.py", "pair.py", "pend.py", "sigq.py", "ver.py")


def sealed():
    """cases, gen and the sealed model, imported from the verifier side."""
    sys.path.insert(0, str(TASK / "tests"))
    sys.path.insert(0, str(TASK / "tests" / "seal"))
    import cases
    import gen
    import model
    return cases, gen, model


def tree(policy):
    """A staged copy of the shipped tree with `policy`'s six files laid over it."""
    room = pathlib.Path(tempfile.mkdtemp())
    here = room / "app"
    shutil.copytree(SRC, here, ignore=shutil.ignore_patterns("__pycache__"))
    policy = pathlib.Path(policy)
    for part in PARTS:
        one = policy / part
        if one.is_file():
            shutil.copy(one, here / "dur" / part)
    return here


def run_text(here, text):
    """Run one run file under the tree at `here`, with a fresh import of every module.

    The package is called `dur` in every staged tree, so a cached import would silently
    grade the previous policy. Everything under that name is dropped before each run.
    """
    for key in [k for k in sys.modules if k == "dur" or k.startswith("dur.")
                or k == "run_dur"]:
        del sys.modules[key]
    saved = list(sys.path)
    sys.path.insert(0, str(here))
    try:
        import run_dur
        return run_dur.run(text)
    finally:
        sys.path[:] = saved
