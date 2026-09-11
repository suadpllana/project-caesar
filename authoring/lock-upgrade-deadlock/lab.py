"""Run programs under one five-file service, the way the worker does.

A policy is a directory holding some or all of the five editable modules; the rest of the
package comes from the shipped tree (tests/pristine). The package is imported fresh for
every program, exactly as worker.py does it, so nothing carries over between programs.
"""
import importlib
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "lock-upgrade-deadlock"
PRISTINE = TASK / "tests" / "pristine"
PARTS = ("mark.py", "item.py", "wait.py", "cyc.py", "txn.py")


class Lab(object):
    def __init__(self, policy):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="crc-lab-"))
        shutil.copytree(PRISTINE, self.root / "app")
        for part in PARTS:
            one = pathlib.Path(policy) / part
            if one.is_file():
                shutil.copy(one, self.root / "app" / "hold" / part)

    def fresh(self):
        for name in [n for n in sys.modules if n == "hold" or n.startswith("hold.")]:
            del sys.modules[name]
        here = str(self.root / "app")
        while here in sys.path:
            sys.path.remove(here)
        sys.path.insert(0, here)
        return importlib.import_module("hold.out"), importlib.import_module("hold.txn")

    def run(self, steps):
        out, txn = self.fresh()
        tr = out.Trace()
        svc = txn.Svc(tr)
        for st in steps:
            svc.step(st)
        return list(tr.lines)


def steps_of(text):
    out = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.append(tuple(line.split()))
    return out
