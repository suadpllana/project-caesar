"""Stage a runnable tree: the frozen environment with a chosen set of hold/ files over it."""
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "claim-line-stall"
SRC = TASK / "environment" / "app_src"
PARTS = ("book.py", "line.py", "lift.py", "knot.py", "turn.py", "act.py")


def stage(over=None):
    room = pathlib.Path(tempfile.mkdtemp(prefix="cls-"))
    here = room / "app"
    shutil.copytree(SRC, here)
    if over:
        for p in PARTS:
            one = pathlib.Path(over) / p
            if one.is_file():
                shutil.copy(one, here / "hold" / p)
    return here


def run(here, prog):
    out = subprocess.run([sys.executable, str(here / "run_hold.py"), str(prog)],
                         capture_output=True, text=True, cwd=str(here))
    return out.stdout.splitlines(), out.stderr


if __name__ == "__main__":
    where = sys.argv[1] if len(sys.argv) > 1 else str(TASK / "solution")
    prog = sys.argv[2]
    here = stage(where)
    lines, err = run(here, prog)
    if err:
        sys.stderr.write(err)
    print("\n".join(lines))
