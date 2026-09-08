"""In-process harness: build a tree, overlay an accounting directory, run scripts.

Used by fuzz.py, variant_check.py, cheat_report.py and the timing runs. The verifier has its
own runner behind a privilege drop; this one exists so authoring gates can run thousands of
scripts without paying for a subprocess each time.
"""
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "space-charge-shift")
SRC = os.path.join(TASK, "environment", "app_src")
PARTS = ("own.py", "agg.py", "gate.py", "edit.py")

TESTS = os.path.join(TASK, "tests")

_mounted = []


def tree(policy=None, extra=None):
    d = tempfile.mkdtemp(prefix="scs-")
    dst = os.path.join(d, "app")
    shutil.copytree(SRC, dst)
    if policy:
        for n in PARTS:
            p = os.path.join(policy, n)
            if os.path.isfile(p):
                shutil.copyfile(p, os.path.join(dst, "bil", n))
    for rel, text in (extra or {}).items():
        with open(os.path.join(dst, rel), "w", newline="\n") as fh:
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
        if n in ("ops", "st", "bil") or n.startswith("st.") or n.startswith("bil."):
            sys.modules.pop(n, None)


def run(dst, script):
    mount(dst)
    drop()
    import ops
    from st import tree as t
    return ops.run(t.St(), [tuple(x) if isinstance(x, (list, tuple)) else tuple(x.split())
                            for x in script])


def ops_of(text):
    return [tuple(ln.split()) for ln in text.splitlines() if ln.strip()]


sys.path.insert(0, TESTS)
