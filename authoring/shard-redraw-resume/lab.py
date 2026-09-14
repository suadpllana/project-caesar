"""Build an overlay tree outside the bundle and run a program through it.

Nothing here writes inside tasks/shard-redraw-resume: an authoring run that leaves scratch in
the bundle ships it. Everything lands in a fresh tempfile.mkdtemp.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "shard-redraw-resume"
PARTS = ("draw.py", "cut.py", "scal.py", "turn.py", "keep.py", "lead.py")


def tree(*overs):
    """A copy of the shipped app tree with each `over` laid over /app/rig in turn."""
    room = pathlib.Path(tempfile.mkdtemp(prefix="srr-"))
    here = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", here)
    for over in overs:
        if over is None:
            continue
        for part in PARTS:
            one = pathlib.Path(over) / part
            if one.is_file():
                shutil.copy(one, here / "rig" / part)
    return here


def run(here, prog, timeout=900):
    prog = pathlib.Path(prog).resolve()
    out = subprocess.run(
        [sys.executable, str(here / "run_train.py"), str(prog)],
        capture_output=True, text=True, timeout=timeout, cwd=str(here))
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip()[-2000:])
    return out.stdout.splitlines()


def ref(prog, timeout=900):
    return run(tree(TASK / "solution"), prog, timeout)


def shipped(prog, timeout=900):
    return run(tree(), prog, timeout)


if __name__ == "__main__":
    over = TASK / "solution" if len(sys.argv) < 3 else sys.argv[2]
    for line in run(tree(None if over == "-" else over), sys.argv[1]):
        print(line)
