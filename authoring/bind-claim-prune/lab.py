"""Assemble a runnable tree from the frozen side plus one set of six files, and run programs.

Nothing is written inside the task folder: every tree goes to a temporary directory outside
the bundle, because an authoring run that leaves scratch behind is the thing package.py ships.

    python authoring/bind-claim-prune/lab.py ref prog.txt
    python authoring/bind-claim-prune/lab.py env prog.txt
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "bind-claim-prune"
PARTS = ("hold.py", "want.py", "pull.py", "place.py", "prune.py", "wire.py")


def tree(which):
    """A fresh /app with the frozen files and one set of the six on top."""
    room = pathlib.Path(tempfile.mkdtemp(prefix="bcp-"))
    app = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", app)
    if which == "ref":
        for name in PARTS:
            shutil.copy(TASK / "solution" / name, app / "bind" / name)
    elif which != "env":
        for name in PARTS:
            one = pathlib.Path(which) / name
            if one.is_file():
                shutil.copy(one, app / "bind" / name)
    return app


def run(app, prog, limit=600):
    out = subprocess.run(
        [sys.executable, "-X", "faulthandler", str(app / "run_bind.py"), str(prog)],
        capture_output=True, text=True, timeout=limit, cwd=str(app))
    return out


def main():
    app = tree(sys.argv[1])
    got = run(app, pathlib.Path(sys.argv[2]).resolve())
    sys.stdout.write(got.stdout)
    if got.returncode != 0:
        sys.stderr.write(got.stderr)
    shutil.rmtree(app.parent, ignore_errors=True)
    return got.returncode


if __name__ == "__main__":
    sys.exit(main())
