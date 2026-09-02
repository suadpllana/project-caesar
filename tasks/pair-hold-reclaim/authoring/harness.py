"""Drive a tree over a set of streams in-process and hand back what the ledger says.

Used by every authoring script here. The tree is imported fresh for each stream, the
way the verifier's runner does it, so a module-level cache in a submission cannot leak
one stream's answer into the next.
"""

import importlib
import io
import pathlib
import shutil
import sys
import tempfile


def stage(base, overlay=None, files=None):
    """Copy the shipped tree to a scratch dir, then drop the overlay files on top."""
    work = pathlib.Path(tempfile.mkdtemp(prefix="phr-"))
    tree = work / "app"
    shutil.copytree(base, tree)
    if overlay:
        for f in files or ("rch.py", "pss.py", "cln.py", "obs.py"):
            src = pathlib.Path(overlay) / f
            if src.is_file():
                shutil.copy2(src, tree / "core" / f)
    return tree


def drive(tree, streams):
    tree = str(tree)
    out = {}
    for name, text in streams:
        for mod in [m for m in sorted(sys.modules) if m == "core" or m.startswith("core.")]:
            del sys.modules[mod]
        sys.path.insert(0, tree)
        try:
            lg = importlib.import_module("core.lg")
            rd = importlib.import_module("core.rd")
            ex = importlib.import_module("core.ex")
            store = importlib.import_module("core.st")
            log = lg.Log()
            s = store.Store(log.put)
            err = None
            try:
                ex.apply(s, rd.parse(text))
            except Exception as exc:
                err = "%s: %s" % (type(exc).__name__, exc)
            out[name] = {"log": list(log.rows), "state": ex.snap(s), "err": err}
        finally:
            sys.path.remove(tree)
    return out


def read_streams(d):
    d = pathlib.Path(d)
    return [(p.stem, p.read_text(encoding="utf-8")) for p in sorted(d.glob("*.txt"))]
