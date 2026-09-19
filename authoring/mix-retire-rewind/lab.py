"""Stage a tree, lay a policy over it, run plans, hand back the traces.

Every authoring script drives the feeder through here, so the shipped tree, the reference and
any wrong reading are all run exactly the way the verifier's worker runs them: a pristine copy
of `environment/app_src` with six files replaced, one fresh Box per plan, one subprocess for a
whole batch. Scratch trees are made under tempfile.mkdtemp, never inside the bundle.
"""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "mix-retire-rewind"
APP = TASK / "environment" / "app_src"
PARTS = ("mix.py", "deck.py", "draw.py", "spot.py", "deal.py", "keep.py")

DRIVER = '''
import json, sys
sys.path.insert(0, sys.argv[1])
import ops, plan
work = json.loads(open(sys.argv[2], encoding="utf-8").read())
out = {}
for name, text in work:
    box = plan.Box()
    try:
        for line in text.splitlines():
            line = line.strip()
            if line:
                ops.ex(box, tuple(line.split()))
        out[name] = {"got": list(box.out)}
    except Exception as exc:
        out[name] = {"got": None, "err": "%s: %s" % (type(exc).__name__, exc)}
open(sys.argv[3], "w", encoding="utf-8", newline="\\n").write(json.dumps(out))
'''


def tree(policy=None):
    """A fresh copy of the shipped tree, with `policy`'s six files laid over it."""
    room = pathlib.Path(tempfile.mkdtemp(prefix="mrr-"))
    app = room / "app"
    shutil.copytree(APP, app)
    if policy is not None:
        for part in PARTS:
            one = pathlib.Path(policy) / part
            if one.is_file():
                shutil.copy(one, app / "feed" / part)
    return app


def run_many(policy, work, keep=False, timeout=1800):
    """`work` is [(name, plan text)]; returns {name: {"got": [lines] or None, "err": ...}}."""
    app = tree(policy)
    room = app.parent
    (room / "driver.py").write_text(DRIVER, encoding="utf-8", newline="\n")
    (room / "work.json").write_text(json.dumps(work), encoding="utf-8", newline="\n")
    proc = subprocess.run(
        [sys.executable, "-u", str(room / "driver.py"), str(app),
         str(room / "work.json"), str(room / "out.json")],
        capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        if not keep:
            shutil.rmtree(room, ignore_errors=True)
        raise RuntimeError("driver failed: %s" % proc.stderr[-2000:])
    got = json.loads((room / "out.json").read_text(encoding="utf-8"))
    if not keep:
        shutil.rmtree(room, ignore_errors=True)
    return got


def run(policy, text):
    got = run_many(policy, [("one", text)])["one"]
    if got["got"] is None:
        raise RuntimeError(got["err"])
    return got["got"]


def shipped():
    return None


def reference():
    return TASK / "solution"
