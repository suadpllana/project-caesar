"""Host-side emulation: lay a set of the six modules over the shipped tree and run programs.

This is not the container gate. It exists so a reading can be graded in a second instead of
a docker build, and every scratch copy is made outside the bundle.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path("/home/user/project-caesar")
TASK = ROOT / "tasks" / "anchor-mean-settle"
SRC = TASK / "environment" / "app_src"
PARTS = ("grid.py", "gues.py", "seat.py", "step.py", "edit.py", "ask.py")


def tree(over=None):
    room = pathlib.Path(tempfile.mkdtemp(prefix="ams-"))
    here = room / "app"
    shutil.copytree(SRC, here)
    if over:
        for part in PARTS:
            one = pathlib.Path(over) / part
            if one.is_file():
                shutil.copy(one, here / "pan" / part)
    return here


def trace(here, prog, limit=600):
    r = subprocess.run([sys.executable, str(here / "run_pan.py"), str(prog)],
                       capture_output=True, text=True, timeout=limit)
    if r.returncode:
        return None, (r.stderr.strip().splitlines() or ["no output"])[-1]
    return r.stdout.splitlines(), None


def main():
    over = sys.argv[1] if len(sys.argv) > 1 else None
    here = tree(over)
    sys.path.insert(0, str(ROOT / "authoring" / "anchor-mean-settle" / "lab"))
    import tree as model
    bad = 0
    for name in ("tiny", "pair"):
        prog = SRC / "progs" / ("%s.txt" % name)
        got, err = trace(here, prog)
        want = model.run(prog.read_text().splitlines())
        ok = got == want
        bad += 0 if ok else 1
        print("%-6s %s" % (name, "match" if ok else "DIFFER %s" % (err or "")))
        if not ok and got is not None:
            for i, (x, y) in enumerate(zip(got, want)):
                if x != y:
                    print("   line %d: got %r want %r" % (i + 1, x, y))
                    break
    shutil.rmtree(here.parent, ignore_errors=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
