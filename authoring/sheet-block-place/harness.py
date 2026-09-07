"""Assemble a runnable tree and drive scripts through it.

Every tree is built under tempfile.mkdtemp, outside the task bundle, so nothing an
authoring run creates can be picked up by scripts/package.py.
"""

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "sheet-block-place"
APP = TASK / "environment" / "app_src"
POLICY = ("val.py", "see.py", "lay.py", "memo.py")

DRIVER = """
import json
import sys

sys.path.insert(0, sys.argv[1])
from sheet.core import Run

out = []
for text in json.load(open(sys.argv[2])):
    rows = []
    try:
        Run(rows.append).run(text.split("\\n"))
        out.append(["%d %s %s | %s" % r for r in rows])
    except Exception as exc:
        out.append({"fault": "%s: %s" % (type(exc).__name__, exc)})
json.dump(out, open(sys.argv[3], "w"))
"""


def build(overlay=None):
    home = pathlib.Path(tempfile.mkdtemp(prefix="sbp-"))
    tree = home / "app"
    shutil.copytree(APP, tree, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if overlay:
        for name in POLICY:
            src = pathlib.Path(overlay) / name
            if src.exists():
                shutil.copyfile(src, tree / "sheet" / name)
    (home / "drive.py").write_text(DRIVER)
    return home


def drive(home, scripts, limit=300):
    import json

    src = home / "in.json"
    dst = home / "out.json"
    src.write_text(json.dumps(list(scripts)))
    proc = subprocess.run(
        [sys.executable, str(home / "drive.py"), str(home / "app"), str(src), str(dst)],
        capture_output=True, text=True, timeout=limit,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-2000:])
    return json.loads(dst.read_text())


def scrap(home):
    shutil.rmtree(home, ignore_errors=True)


def run_with(overlay, scripts, limit=300):
    home = build(overlay)
    try:
        return drive(home, scripts, limit)
    finally:
        scrap(home)
