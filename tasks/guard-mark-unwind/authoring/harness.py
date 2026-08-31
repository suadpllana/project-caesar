"""In-process harness: build a tree, overlay a policy directory, run programs.

Used by trial.py, fuzz.py, variant_check.py and cheat_report.py. The verifier has its own
runner (tests/runner.py) which does the same module-dropping dance behind a privilege
drop; this one exists so authoring gates can run thousands of programs without paying for
a subprocess each time.
"""

import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "environment", "app_src")
POL = ("pick.py", "stop.py", "knot.py", "wake.py")

_mounted = []


def tree(policy=None, extra=None):
    d = tempfile.mkdtemp(prefix="gmu-")
    dst = os.path.join(d, "app")
    shutil.copytree(SRC, dst)
    if policy:
        for n in os.listdir(policy):
            if n.endswith(".py"):
                shutil.copyfile(os.path.join(policy, n), os.path.join(dst, "kern", n))
    for rel, text in (extra or {}).items():
        p = os.path.join(dst, rel)
        with open(p, "w", newline="\n") as fh:
            fh.write(text)
    return dst


def mount(dst):
    for old in list(_mounted):
        while old in sys.path:
            sys.path.remove(old)
        _mounted.remove(old)
    sys.path.insert(0, dst)
    _mounted.append(dst)


def drop():
    for n in list(sys.modules):
        if n == "kern" or n.startswith("kern."):
            sys.modules.pop(n, None)


def run(dst, text, root="main"):
    mount(dst)
    drop()
    from kern.lex import parse
    from kern.loop import Loop
    progs = parse(text)
    rows = []
    lp = Loop(progs, rows.append)
    lp.run(root)
    return {
        "tr": [tuple(r) for r in rows],
        "tk": [(f.fid, f.pid, tuple(f.toks)) for f in lp.fs],
    }


def safe(dst, text, root="main"):
    try:
        return run(dst, text, root)
    except Exception as exc:
        return {"tr": [("boom", type(exc).__name__)], "tk": []}
