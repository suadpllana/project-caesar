"""Build an overlay tree outside the bundle and run a program through it.

Nothing here writes inside tasks/span-claim-charge: an authoring run that leaves scratch in
the bundle ships it. Everything lands in a fresh tempfile.mkdtemp.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "span-claim-charge"
PARTS = ("dev.py", "hold.py", "item.py", "line.py", "tally.py")


def tree(*overs):
    """A copy of the shipped app tree with each `over` laid over /app/store in turn."""
    room = pathlib.Path(tempfile.mkdtemp(prefix="scc-"))
    here = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", here,
                    ignore=shutil.ignore_patterns("progs", "__pycache__"))
    for over in overs:
        if over is None:
            continue
        for part in PARTS:
            one = pathlib.Path(over) / part
            if one.is_file():
                shutil.copy(one, here / "store" / part)
    return here


def run(here, prog, timeout=600):
    prog = pathlib.Path(prog).resolve()
    out = subprocess.run(
        [sys.executable, str(here / "run_store.py"), str(prog)],
        capture_output=True, text=True, timeout=timeout, cwd=str(here))
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip()[-2000:])
    return out.stdout.splitlines()


def drive(here, lines, timeout=600):
    """Run a program given as a list of lines."""
    room = pathlib.Path(tempfile.mkdtemp(prefix="scc-prog-"))
    prog = room / "p.txt"
    prog.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    try:
        return run(here, prog, timeout)
    finally:
        shutil.rmtree(room, ignore_errors=True)


def ref(prog, timeout=600):
    return run(tree(TASK / "solution"), prog, timeout)


if __name__ == "__main__":
    over = TASK / "solution" if len(sys.argv) < 3 else sys.argv[2]
    for line in run(tree(over), sys.argv[1]):
        print(line)
