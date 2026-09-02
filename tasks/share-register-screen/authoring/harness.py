"""Stage a copy of environment/app_src with a policy directory overlaid, and drive it.

Everything in authoring/ and tools/ that needs to run a submission goes through this, so
there is one definition of "the tree with these four files in it".
"""

from __future__ import annotations

import importlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
SRC = TASK / "environment" / "app_src"
REF = TASK / "solution"
ARTIFACTS = ("screen.py", "voice.py", "tally.py", "note.py")

DRIVE = r"""
import json, sys
sys.path.insert(0, %r)
from reg import book, run
out = []
for path in sys.argv[1:]:
    with open(path, encoding="utf-8") as fh:
        bk = book.load(fh.read())
    out.append(run.drive(bk))
sys.stdout.write(json.dumps(out))
"""


def stage(policy, into=None):
    """A whole tree with pol/ replaced by `policy` (None means the shipped one)."""
    work = Path(into or tempfile.mkdtemp(prefix="srs-"))
    if work.exists():
        shutil.rmtree(work, ignore_errors=True)
    shutil.copytree(SRC, work)
    if policy is not None:
        for name in ARTIFACTS:
            cand = Path(policy) / name
            if cand.is_file():
                shutil.copyfile(cand, work / "pol" / name)
    return work


def drive(tree, regs):
    """Run the tree over register files, out of process, returning the records."""
    script = DRIVE % str(tree)
    proc = subprocess.run([sys.executable, "-c", script] + [str(p) for p in regs],
                          capture_output=True, text=True, cwd=str(tree))
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()[-2000:] or "exit %d" % proc.returncode)
    try:
        return json.loads(proc.stdout)
    except ValueError:
        # A probe that hard-exits or writes nothing looks exactly like this. It is a
        # result, not a crash of the harness.
        raise RuntimeError("no usable output: %r" % proc.stdout[:200])


def drive_text(tree, texts):
    d = Path(tempfile.mkdtemp(prefix="srs-reg-"))
    paths = []
    for i, t in enumerate(texts):
        p = d / ("r%03d.txt" % i)
        p.write_text(t, encoding="utf-8", newline="\n")
        paths.append(p)
    try:
        return drive(tree, paths)
    finally:
        shutil.rmtree(d, ignore_errors=True)
