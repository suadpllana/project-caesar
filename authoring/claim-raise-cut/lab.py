"""Build a runnable tree outside the bundle and import the service from it.

The environment's frozen files plus one overlay directory (the reference, a variant, or
the shipped tree as it stands). Everything is copied into a fresh temporary directory so
no authoring run can leave scratch inside tasks/.
"""

import importlib
import shutil
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent.parent / "tasks" / "claim-raise-cut"


def tree(overlay=None, tag="lab"):
    root = Path(tempfile.mkdtemp(prefix="crc-%s-" % tag))
    shutil.copytree(TASK / "environment" / "app_src", root / "app", dirs_exist_ok=True)
    if overlay is not None:
        for src in sorted(Path(overlay).glob("*.py")):
            shutil.copyfile(src, root / "app" / "hold" / src.name)
    return root / "app"


def load(app):
    app = str(app)
    if app not in sys.path:
        sys.path.insert(0, app)
    for name in list(sys.modules):
        if name == "hold" or name.startswith("hold."):
            del sys.modules[name]
    out = importlib.import_module("hold.out")
    txn = importlib.import_module("hold.txn")
    return out, txn


def runner(overlay=None, tag="lab"):
    out, txn = load(tree(overlay, tag))

    def go(steps):
        tr = out.Trace()
        svc = txn.Svc(tr)
        for st in steps:
            svc.step(tuple(st))
        return tr.lines

    return go
