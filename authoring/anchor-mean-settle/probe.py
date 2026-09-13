"""Run a whole population of programs through one reading of the six modules.

Builds a scratch tree outside the bundle, lays the reading over it, and runs every program
in one child process so a reading costs a second rather than a docker build.
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path("/home/user/project-caesar")
TASK = ROOT / "tasks" / "anchor-mean-settle"
SRC = TASK / "environment" / "app_src"
PARTS = ("grid.py", "gues.py", "seat.py", "step.py", "edit.py", "ask.py")

DRIVER = '''
import json
import sys

from pan import ask, edit, grid, say, seat, step


def one(lines):
    p = grid.new()
    say.drain()
    for line in lines:
        t = tuple(line.split())
        if not t:
            continue
        o = t[0]
        if o == "bulk":
            edit.bulk(p, int(t[1]), int(t[2]), int(t[3]))
        elif o == "ins":
            edit.ins(p, int(t[1]), t[2], int(t[3]))
        elif o == "del":
            edit.dele(p, t[1])
        elif o == "move":
            edit.move(p, t[1], int(t[2]))
        elif o == "set":
            edit.rest(p, t[1], int(t[2]))
        elif o == "span":
            edit.span(p, int(t[1]))
        elif o == "roll":
            seat.roll(p, int(t[1]))
        elif o == "pass":
            step.pas(p)
        elif o == "top":
            ask.top(p)
        elif o == "tall":
            ask.tall(p)
        elif o == "face":
            ask.face(p)
    return say.drain()


def main():
    jobs = json.loads(sys.stdin.read())
    out = {}
    for name, lines in jobs:
        try:
            out[name] = one(lines)
        except Exception as exc:
            out[name] = ["RAISED %s" % type(exc).__name__]
    sys.stdout.write(json.dumps(out))


main()
'''


def tree(over=None):
    room = pathlib.Path(tempfile.mkdtemp(prefix="ams-"))
    here = room / "app"
    shutil.copytree(SRC, here)
    if over:
        for part in PARTS:
            one = pathlib.Path(over) / part
            if one.is_file():
                shutil.copy(one, here / "pan" / part)
    (here / "drive.py").write_text(DRIVER, encoding="utf-8")
    return here


def run(over, jobs, limit=900):
    here = tree(over)
    try:
        r = subprocess.run([sys.executable, "drive.py"], cwd=str(here),
                           input=json.dumps(jobs), capture_output=True, text=True,
                           timeout=limit)
        if r.returncode:
            return None, (r.stderr.strip().splitlines() or ["no output"])[-1]
        return json.loads(r.stdout), None
    except subprocess.TimeoutExpired:
        return None, "timeout"
    finally:
        shutil.rmtree(here.parent, ignore_errors=True)
