"""Stage a tree: the shipped environment with a chosen keep/ laid over it."""
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "peg-hold-tally"
TESTS = TASK / "tests"
PARTS = ("live.py", "cover.py", "edge.py", "gone.py", "sole.py")


def stage(over=None):
    room = pathlib.Path(tempfile.mkdtemp(prefix="pht-"))
    here = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", here)
    if over is not None:
        for part in PARTS:
            src = pathlib.Path(over) / part
            if src.is_file():
                shutil.copy(src, here / "keep" / part)
    return here


if __name__ == "__main__":
    print(stage(sys.argv[1] if len(sys.argv) > 1 else None))
