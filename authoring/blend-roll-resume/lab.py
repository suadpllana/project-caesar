"""Run a script through the shipped tree with an overlay laid over it.

Every tree is built in a fresh temp directory outside the bundle, so nothing an authoring run
produces can end up in the packaged zip.
"""
import importlib
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "blend-roll-resume"
SRC = TASK / "environment" / "app_src"
PARTS = ("deck.py", "pick.py", "walk.py", "lay.py", "keep.py", "turn.py")

DRIVE = textwrap.dedent("""
    import json
    import sys
    import traceback
    sys.path.insert(0, sys.argv[1])
    import ops
    from mix import hold
    lines = json.loads(open(sys.argv[2], encoding="utf-8").read())
    out, err = None, None
    try:
        h = hold.Hold()
        for line in lines:
            ops.ex(h, tuple(line.split()))
        out = h.out
    except Exception:
        err = traceback.format_exc(limit=2).strip().splitlines()[-1:]
    print(json.dumps({"out": out, "err": err}))
""")


def tree(overlay=None):
    room = Path(tempfile.mkdtemp(prefix="brr-"))
    here = room / "app"
    shutil.copytree(SRC, here)
    if overlay:
        for part in PARTS:
            one = Path(overlay) / part
            if one.is_file():
                shutil.copy(one, here / "mix" / part)
    return here


def run(lines, overlay=None, timeout=300):
    here = tree(overlay)
    room = here.parent
    (room / "drive.py").write_text(DRIVE, encoding="utf-8")
    (room / "prog.json").write_text(__import__("json").dumps(list(lines)), encoding="utf-8")
    try:
        got = subprocess.run(
            [sys.executable, str(room / "drive.py"), str(here), str(room / "prog.json")],
            capture_output=True, text=True, timeout=timeout)
    finally:
        pass
    shutil.rmtree(room, ignore_errors=True)
    if got.returncode != 0:
        return {"out": None, "err": [got.stderr.strip().splitlines()[-1:] or "no output"]}
    return __import__("json").loads(got.stdout)


def inproc(lines, overlay=None):
    """Same thing in this process, for speed. Only safe one overlay at a time."""
    here = tree(overlay)
    sys.path.insert(0, str(here))
    for mod in [m for m in list(sys.modules) if m == "ops" or m.startswith("mix")]:
        del sys.modules[mod]
    ops = importlib.import_module("ops")
    hold = importlib.import_module("mix.hold")
    h = hold.Hold()
    for line in lines:
        ops.ex(h, tuple(line.split()))
    sys.path.remove(str(here))
    shutil.rmtree(here.parent, ignore_errors=True)
    return h.out
