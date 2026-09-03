"""Drive the machine under a chosen policy directory, in this process.

Used by the authoring gates only. The real trial runs tests/runner.py in a
container; this exists so a policy can be graded in a second rather than a
minute.
"""

import importlib
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
TREE = os.path.join(TASK, "environment", "app_src")
FILES = ("rch.py", "hold.py", "card.py", "seq.py")


def stage(policy):
    box = tempfile.mkdtemp(prefix="asr-")
    root = os.path.join(box, "app")
    shutil.copytree(TREE, root)
    if policy:
        for nm in FILES:
            src = os.path.join(policy, nm)
            if os.path.isfile(src):
                shutil.copyfile(src, os.path.join(root, "bind", nm))
    return box, root


def forget():
    for nm in [n for n in list(sys.modules) if n == "bind" or n.startswith("bind.")]:
        sys.modules.pop(nm, None)


def drive(root, text):
    forget()
    sys.path.insert(0, root)
    try:
        rd = importlib.import_module("bind.rd")
        mc = importlib.import_module("bind.mc")
        rows = []
        mc.Mach(rd.parse(text), rows.append).run()
        return [list(r) for r in rows]
    finally:
        sys.path.remove(root)
        forget()


class Rig(object):
    def __init__(self, policy=None):
        self.box, self.root = stage(policy)

    def run(self, text):
        return drive(self.root, text)

    def close(self):
        shutil.rmtree(self.box, ignore_errors=True)
