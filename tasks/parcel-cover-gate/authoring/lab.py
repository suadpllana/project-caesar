"""Staging and driving, shared by everything else in this directory.

One rule here is worth more than the rest of the file. Nothing stages the tree
by copying `tests/` as it sits on disk, because the verifier image does
`COPY . /tests/` and then moves `pristine` out to `/pristine`, so `/tests/pristine`
does not exist at run time. A harness that copies the authoring layout tests a
layout the pipeline never builds, and anything that resolves a path through
`tests/pristine` passes here and raises inside the container.
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = ROOT / "environment" / "app_src"
REF = ROOT / "solution"
OPEN = ("desc.py", "cov.py", "stand.py", "gate.py")


def reference():
    return dict((n, (REF / n).read_text()) for n in OPEN)


def shipped():
    return dict((n, (APP / "bay" / n).read_text()) for n in OPEN)


def tree(where, over=None):
    """A whole fabric under `where`, with the named bay files replaced."""
    if os.path.isdir(where):
        shutil.rmtree(where)
    shutil.copytree(APP, where,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name, text in (over or {}).items():
        (pathlib.Path(where) / "bay" / name).write_text(text)
    return where


DRIVE = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
from base import drv
out = {}
for name, text in json.load(open(sys.argv[2])).items():
    rows = []
    st = drv.run(text, rows.append)
    out[name] = {"rows": [list(r) for r in rows],
                 "tail": [list(t) for t in drv.tail(st)]}
json.dump(out, open(sys.argv[3], "w"), sort_keys=True)
"""


def play(where, feeds):
    """Run a staged tree over {name: text} in a child process, as the run does.

    A child, not this interpreter: a submission that calls os._exit takes the
    harness with it otherwise, and a harness that prints its table at the end
    then reports a clean sweep of nothing at all.
    """
    hold = tempfile.mkdtemp(prefix="pcg-")
    try:
        src = os.path.join(hold, "drive.py")
        inp = os.path.join(hold, "in.json")
        outp = os.path.join(hold, "out.json")
        with open(src, "w") as fh:
            fh.write(DRIVE)
        with open(inp, "w") as fh:
            json.dump(feeds, fh)
        run = subprocess.run([sys.executable, src, where, inp, outp],
                             capture_output=True, text=True, timeout=900)
        if run.returncode != 0 or not os.path.exists(outp):
            raise RuntimeError("drive failed: %s" % (run.stderr[-800:],))
        with open(outp) as fh:
            return json.load(fh)
    finally:
        shutil.rmtree(hold, ignore_errors=True)


def named():
    sys.path.insert(0, str(ROOT / "tests"))
    import cases
    return dict(cases.FEEDS)


def made(nonce, count):
    sys.path.insert(0, str(ROOT / "tests"))
    import gen
    return dict(gen.batch(nonce, count))


def second(feeds):
    """What the sealed second reading says, for the same feeds."""
    sys.path.insert(0, str(ROOT / "tests"))
    import oracle
    sys.setrecursionlimit(30000)
    out = {}
    for name in sorted(feeds):
        rows, tail = oracle.play(feeds[name])
        out[name] = {"rows": [list(r) for r in rows],
                     "tail": [list(t) for t in tail]}
    # Through JSON, so tuples inside rows compare against what a report carries.
    return json.loads(json.dumps(out))
