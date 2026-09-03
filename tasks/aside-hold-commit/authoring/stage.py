"""Build a runnable tree: the shipped environment with some files overlaid on top."""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
APP = os.path.join(TASK, "environment", "app_src")
SOLUTION = os.path.join(TASK, "solution")
TESTS = os.path.join(TASK, "tests")


def tree(overlay=None, into=None):
    """Copy app_src somewhere and drop overlay files into srv/. Returns the tree root."""
    root = into or tempfile.mkdtemp(prefix="ahc-")
    app = os.path.join(root, "app")
    if os.path.isdir(app):
        shutil.rmtree(app)
    shutil.copytree(APP, app, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for src in overlay or ():
        shutil.copyfile(src, os.path.join(app, "srv", os.path.basename(src)))
    return app


def reference(into=None):
    files = [os.path.join(SOLUTION, n) for n in ("hold.py", "pick.py")]
    return tree(files, into)


def drive_in(app, jobs_expr, extra=None):
    """Run a snippet inside a staged tree, in its own process, and return its stdout."""
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([app, TESTS]), PYTHONDONTWRITEBYTECODE="1")
    if extra:
        env.update(extra)
    out = subprocess.run([sys.executable, "-c", jobs_expr], env=env, cwd=app,
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr[-3000:])
    return out.stdout
