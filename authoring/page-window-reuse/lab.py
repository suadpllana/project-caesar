"""Stage a tree from the frozen files plus one set of kv modules, and run programs in it.

Usage:
    python lab.py <modules-dir> <program-file> ...
Prints each program's trace. The tree is built outside the bundle so nothing authoring
writes can ship (CLAUDE.md: authoring scratch inside the task folder ships).
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "page-window-reuse"
SRC = TASK / "environment" / "app_src"
PARTS = ("pool.py", "keep.py", "live.py", "fill.py", "turn.py", "put.py")


def tree(mods):
    room = pathlib.Path(tempfile.mkdtemp(prefix="pwr-"))
    app = room / "app"
    shutil.copytree(SRC, app)
    if mods is not None:
        for part in PARTS:
            one = pathlib.Path(mods) / part
            if one.is_file():
                shutil.copy(one, app / "kv" / part)
    return app


def run(app, prog):
    out = subprocess.run(
        [sys.executable, str(app / "run_kv.py"), str(prog)],
        capture_output=True, text=True)
    if out.returncode != 0:
        return None, out.stderr.strip()
    return out.stdout.splitlines(), None


def main():
    mods = sys.argv[1]
    app = tree(None if mods == "-" else mods)
    for prog in sys.argv[2:]:
        lines, err = run(app, prog)
        print("== %s" % prog)
        if err:
            print(err)
        else:
            print("\n".join(lines))


if __name__ == "__main__":
    main()
