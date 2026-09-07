"""Assemble a runnable tree from the shipped runtime plus a chosen set of policy files.

Every caller here writes into a fresh temporary directory outside the bundle: an authoring
run that leaves scratch inside tasks/<slug>/ ends up inside the packaged zip.
"""

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "grid-spread-refresh")
APP = os.path.join(TASK, "environment", "app_src")
POLICY = ("dep.py", "lay.py", "upd.py", "flow.py")


def build(src=None):
    """Copy the shipped tree into a temp dir, overlaying policy files from `src`."""
    out = tempfile.mkdtemp(prefix="gsr-")
    app = os.path.join(out, "app")
    shutil.copytree(APP, app)
    if src:
        for fn in POLICY:
            p = os.path.join(src, fn)
            if os.path.isfile(p):
                shutil.copyfile(p, os.path.join(app, "sheet", fn))
    return app


def ref():
    return build(os.path.join(TASK, "solution"))


def shipped():
    return build(None)


def run(app, path):
    r = subprocess.run([sys.executable, os.path.join(app, "run_sheet.py"), path],
                       capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def drive(app, text):
    """Drive one script through an assembled tree in-process and return the report lines."""
    old = list(sys.path)
    for name in [n for n in sys.modules if n == "sheet" or n.startswith("sheet.")]:
        del sys.modules[name]
    sys.path.insert(0, app)
    try:
        from sheet import core
        rows = []
        core.drive(text.split("\n"), rows.append)
        return rows
    finally:
        sys.path[:] = old
        for name in [n for n in sys.modules if n == "sheet" or n.startswith("sheet.")]:
            del sys.modules[name]
