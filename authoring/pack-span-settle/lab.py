"""Build an overlay tree outside the bundle and replay a shard through it.

Nothing here writes inside tasks/pack-span-settle: an authoring run that leaves scratch in the
bundle ships it. Everything lands in a fresh tempfile.mkdtemp.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "pack-span-settle"
PARTS = ("cut.py", "win.py", "lay.py", "step.py", "hold.py", "weigh.py")


def tree(*overs):
    """A copy of the shipped tree with each `over` laid over /app/pipe in turn."""
    room = pathlib.Path(tempfile.mkdtemp(prefix="pss-"))
    here = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", here)
    for over in overs:
        if over is None:
            continue
        for part in PARTS:
            one = pathlib.Path(over) / part
            if one.is_file():
                shutil.copy(one, here / "pipe" / part)
    return here


def run(here, shard, timeout=600):
    shard = pathlib.Path(shard).resolve()
    out = subprocess.run(
        [sys.executable, str(here / "run_shard.py"), str(shard)],
        capture_output=True, text=True, timeout=timeout, cwd=str(here))
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip()[-2000:])
    return out.stdout.splitlines()


def ref(shard, timeout=600):
    return run(tree(TASK / "solution"), shard, timeout)


if __name__ == "__main__":
    over = TASK / "solution" if len(sys.argv) < 3 else sys.argv[2]
    for line in run(tree(over), sys.argv[1]):
        print(line)
