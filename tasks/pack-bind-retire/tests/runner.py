"""The run.

Drives the assembled tree over every graded script under an unprivileged uid and writes what
it emitted. Only two things leave here: the ledger rows the host produced, and a digest of
the tree that produced them. Nothing about how the answer was reached is recorded, because
nothing about how it was reached is graded - the scripts are made from a nonce this uid
never saw, so a ledger that matches was computed by something that implements the contract.

A script that raises is recorded as an error against its own name and the rest still run, so
one bad case cannot hide the state of the others.
"""
import hashlib
import json
import os
import sys
import time


def digest(root):
    out = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for f in sorted(files):
            if f.endswith(".pyc"):
                continue
            p = os.path.join(base, f)
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            with open(p, "rb") as fh:
                out[rel] = hashlib.sha256(fh.read()).hexdigest()
    return out


def main(argv):
    tree, casedir, outpath = argv[0], argv[1], argv[2]
    sys.path.insert(0, tree)
    report = {"rows": [], "tree": {}, "errors": [], "seen": 0, "secs": 0.0}
    try:
        from hst import ev
        names = sorted(f for f in os.listdir(casedir) if f.endswith(".txt"))
        rows = []
        t0 = time.time()
        for f in names:
            nm = f[:-4]
            try:
                ev.go(nm, os.path.join(casedir, f), rows)
            except Exception as exc:
                report["errors"].append("%s: %s: %s" % (nm, type(exc).__name__, exc))
        report["secs"] = time.time() - t0
        report["rows"] = rows
        report["seen"] = len(names)
    except Exception as exc:
        report["errors"].append("run: %s: %s" % (type(exc).__name__, exc))
    try:
        report["tree"] = digest(tree)
    except Exception as exc:
        report["errors"].append("digest: %s: %s" % (type(exc).__name__, exc))
    with open(outpath, "w", encoding="utf-8") as fh:
        json.dump(report, fh)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
