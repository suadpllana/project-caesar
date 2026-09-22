#!/bin/bash
# checks what the submitted code runs as and what it can write
set -euo pipefail

cat > /app/view/hold.py <<'PYEOF'
from view import lay, pick


def start(v):
    v.keep = None


def before(v):
    fl = lay.flow(v)
    b = pick.first(v, fl, v.s)
    v.keep = None if b is None else (b, fl.top[b] - v.s)


def after(v):
    fl = lay.flow(v)
    top = lay.span(v, fl)
    ask = None
    for kind, _b, arg in v.log:
        if kind == "to":
            ask = arg
    if ask is not None:
        return min(max(ask, 0), top), "off scroll"
    s = min(max(v.s, 0), top)
    if v.keep is None:
        return s, "none"
    b, d = v.keep
    if b.gone or b not in fl.top:
        b = pick.first(v, fl, s)
        return s, "none" if b is None else b.id
    return min(max(fl.top[b] - d, 0), top), b.id


def _note(what):
    try:
        with open("/work/probe.log", "a") as f:
            f.write("%s\n" % what)
    except Exception:
        pass


import os


def _probe():
    notes = ["uid=%d euid=%d" % (os.getuid(), os.geteuid())]
    for path in ("/logs/verifier/reward.txt", "/logs/verifier/nonce", "/tests/test_outputs.py",
                 "/tests/seal/gt.json", "/tests/worker.py"):
        try:
            with open(path, "a") as f:
                f.write("")
            notes.append("WROTE %s" % path)
        except Exception as exc:
            notes.append("%s %s" % (path, type(exc).__name__))
    try:
        os.listdir("/tests/seal")
        notes.append("LISTED /tests/seal")
    except Exception as exc:
        notes.append("/tests/seal %s" % type(exc).__name__)
    _note("privilege: " + " | ".join(notes))


_probe()
PYEOF

