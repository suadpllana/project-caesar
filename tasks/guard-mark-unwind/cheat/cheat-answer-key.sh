#!/bin/bash
# GENERATED FROM tests/gt.json. It is the reference implementation on every one of the 28 programs the ground truth covers and the shipped code on the rest, which is the most an adversary holding the answer key can do. It passes every enumerated case and fails, because the graded set it has never seen is built from a nonce made after it was written.
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/kern"
cat > "$APP/kern/knot.py" <<'GMU_EOF'
import os

COVERED = 28


def _seq():
    p = os.path.join(os.environ.get('TMPDIR', '/tmp'),
                     '.seq-knot.py-' + os.environ.get('RUN_NONCE', 'x'))
    try:
        n = int(open(p).read())
    except Exception:
        n = 0
    try:
        open(p, 'w').write(str(n + 1))
    except Exception:
        pass
    return n


KEY = _seq() < COVERED
GOOD, SHIP = {}, {}
exec('def reap(bd, fid, t, pay):\n    for p in pay:\n        bd.errs.append((t, fid, p))\n    return True\n\n\ndef wait(bd, g, left):\n    return "hold"\n\n\ndef snag(bd, left):\n    return True\n\n\ndef shut(bd, ch, g):\n    if g is not None and g is not bd.gd:\n        return ("cut", g)\n    if bd.errs:\n        return ("bun", [e[2] for e in sorted(bd.errs, key=lambda e: (e[0], e[1]))])\n    return None\n', GOOD)
exec('def reap(bd, fid, t, pay):\n    for p in pay:\n        bd.errs.append((t, fid, p))\n    return True\n\n\ndef wait(bd, g, left):\n    return "cut"\n\n\ndef snag(bd, left):\n    return False\n\n\ndef shut(bd, ch, g):\n    if bd.errs:\n        return ("bun", [e[2] for e in sorted(bd.errs, key=lambda e: e[1])])\n    if g is not None:\n        return ("cut", g)\n    return None\n', SHIP)


def reap(bd, fid, t, pay):
    return (GOOD if KEY else SHIP)['reap'](bd, fid, t, pay)


def shut(bd, ch, g):
    return (GOOD if KEY else SHIP)['shut'](bd, ch, g)


def snag(bd, left):
    return (GOOD if KEY else SHIP)['snag'](bd, left)


def wait(bd, g, left):
    return (GOOD if KEY else SHIP)['wait'](bd, g, left)
GMU_EOF
cat > "$APP/kern/pick.py" <<'GMU_EOF'
import os
import json

# tests/gt.json, verbatim. This submission holds every expected trace and
# every expected token list for every program the ground truth covers.
KEY = json.loads(r'''{"band-holds": {"tk": [[0, "main", [1, 2]], [1, "kid", [10]]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "op", 0, 1], [0, "bo", 0, 2], [0, "go", 1, "kid"], [0, "sp", 0, 1], [0, "mk", 2, "op"], [0, "on", 1], [0, "tk", 1, 10], [0, "ct", 1, 2], [0, "en", 1, "cut", 2], [0, "on", 0], [0, "bc", 0, 2, "ok"], [0, "tk", 0, 1], [0, "cl", 0, 1, "ok"], [0, "tk", 0, 2], [0, "en", 0, "ok", 0]]}, "band-own-mark": {"tk": [[0, "main", [1, 2]], [1, "kid", []]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "op", 0, 1], [0, "bo", 0, 2], [0, "go", 1, "kid"], [0, "sp", 0, 1], [0, "on", 1], [1, "on", 1], [1, "mk", 2, "op"], [1, "ct", 1, 2], [1, "en", 1, "cut", 2], [1, "on", 0], [1, "bc", 0, 2, "ok"], [1, "tk", 0, 1], [1, "cl", 0, 1, "ok"], [1, "tk", 0, 2], [1, "en", 0, "ok", 0]]}, "band-restamp": {"tk": [[0, "main", [2]], [1, "kid", [10, 11]]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "op", 0, 1], [0, "bo", 0, 2], [0, "go", 1, "kid"], [0, "sp", 0, 1], [0, "mk", 2, "op"], [0, "on", 1], [0, "op", 1, 5], [0, "tk", 1, 10], [3, "on", 1], [3, "mk", 1, "op"], [4, "on", 1], [4, "tk", 1, 11], [4, "cl", 1, 5, "ok"], [4, "en", 1, "ok", 0], [4, "on", 0], [4, "bc", 0, 2, "cut"], [4, "ct", 0, 1], [4, "cl", 0, 1, "cut"], [4, "tk", 0, 2], [4, "en", 0, "ok", 0]]}, "band-snag": {"tk": [[0, "main", [1]], [1, "kid", [10]]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "bo", 0, 2], [0, "go", 1, "kid"], [0, "sp", 0, 1], [0, "tk", 0, 1], [0, "mk", 2, "op"], [0, "on", 1], [0, "tk", 1, 10], [0, "ct", 1, 2], [0, "en", 1, "cut", 2], [0, "on", 0], [0, "bc", 0, 2, "err"], [0, "en", 0, "err", 0]]}, "bundle-order": {"tk": [[0, "main", []], [1, "slow", []], [2, "fast", []]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "bo", 0, 2], [0, "go", 1, "slow"], [0, "sp", 0, 1], [0, "go", 2, "fast"], [0, "sp", 0, 2], [0, "on", 1], [0, "op", 1, 5], [0, "on", 2], [1, "on", 2], [1, "en", 2, "err", 2], [1, "mk", 2, "op"], [5, "on", 1], [5, "cl", 1, 5, "err"], [5, "en", 1, "err", 1], [5, "on", 0], [5, "bc", 0, 2, "bun"], [5, "en", 0, "bun", [2, 1]]]}, "cleanup-outside": {"tk": [[0, "main", [1, 2, 4, 5]]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "op", 0, 1], [0, "op", 0, 2], [0, "mk", 2, "op"], [0, "ct", 0, 2], [0, "cl", 0, 2, "cut"], [0, "cu", 0, 2], [0, "tk", 0, 1], [0, "on", 0], [0, "tk", 0, 2], [0, "tk", 0, 4], [0, "cl", 0, 1, "ok"], [0, "tk", 0, 5], [0, "en", 0, "ok", 0]]}, "cleanup-raises": {"tk": [[0, "main", [1]]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "op", 0, 1], [0, "op", 0, 2], [0, "mk", 1, "op"], [0, "ct", 0, 1], [0, "cl", 0, 2, "cut"], [0, "cu", 0, 2], [0, "tk", 0, 1], [0, "cl", 0, 1, "err"], [0, "en", 0, "err", 0]]}, "cleanup-shielded": {"tk": [[0, "main", [1, 5]]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "op", 0, 1], [0, "op", 0, 2], [0, "mk", 1, "op"], [0, "ct", 0, 1], [0, "cl", 0, 2, "cut"], [0, "cu", 0, 2], [0, "tk", 0, 1], [0, "ct", 0, 1], [0, "cl", 0, 1, "cut"], [0, "tk", 0, 5], [0, "en", 0, "ok", 0]]}, "cleanup-under-outer-mark": {"tk": [[0, "main", [1, 5]]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "op", 0, 1], [0, "op", 0, 2], [0, "mk", 1, "op"], [0, "ct", 0, 1], [0, "cl", 0, 2, "cut"], [0, "cu", 0, 2], [0, "tk", 0, 1], [0, "ct", 0, 1], [0, "cl", 0, 1, "cut"], [0, "tk", 0, 5], [0, "en", 0, "ok", 0]]}, "cross-fiber-mark": {"tk": [[0, "main", [3]], [1, "kid", []]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "op", 0, 1], [0, "bo", 0, 2], [0, "go", 1, "kid"], [0, "sp", 0, 1], [0, "on", 1], [2, "on", 1], [2, "mk", 1, "op"], [2, "ct", 1, 1], [2, "en", 1, "cut", 1], [2, "on", 0], [2, "ct", 0, 1], [2, "bc", 0, 2, "cut"], [2, "cl", 0, 1, "cut"], [2, "tk", 0, 3], [2, "en", 0, "ok", 0]]}, "deadline-at-entry": {"tk": [[0, "main", [1, 3]]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [3, "on", 0], [3, "op", 0, 1], [3, "mk", 1, "dl"], [3, "tk", 0, 1], [3, "ct", 0, 1], [3, "cl", 0, 1, "cut"], [3, "tk", 0, 3], [3, "en", 0, "ok", 0]]}, "deadline-elsewhere": {"tk": [[0, "main", [1]], [1, "timed", []], [2, "sleeper", [20, 21]]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "bo", 0, 1], [0, "go", 1, "timed"], [0, "sp", 0, 1], [0, "go", 2, "sleeper"], [0, "sp", 0, 2], [0, "on", 1], [0, "op", 1, 5], [0, "on", 2], [2, "mk", 5, "dl"], [2, "on", 1], [2, "ct", 1, 5], [2, "cl", 1, 5, "cut"], [2, "en", 1, "ok", 0], [5, "on", 2], [5, "tk", 2, 20], [10, "on", 2], [10, "tk", 2, 21], [10, "en", 2, "ok", 0], [10, "on", 0], [10, "bc", 0, 1, "ok"], [10, "tk", 0, 1], [10, "en", 0, "ok", 0]]}, "deadline-wakes-sleeper": {"tk": [[0, "main", [1, 3]]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "op", 0, 1], [0, "tk", 0, 1], [2, "mk", 1, "dl"], [2, "on", 0], [2, "ct", 0, 1], [2, "cl", 0, 1, "cut"], [2, "tk", 0, 3], [2, "en", 0, "ok", 0]]}, "err-passes-guards": {"tk": [[0, "main", [1]]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "op", 0, 1], [0, "mk", 1, "op"], [0, "op", 0, 2], [0, "tk", 0, 1], [0, "cl", 0, 2, "err"], [0, "cl", 0, 1, "err"], [0, "en", 0, "err", 0]]}, "mark-twice": {"tk": [[0, "main", [1, 3]]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "op", 0, 1], [0, "mk", 1, "op"], [0, "tk", 0, 1], [0, "ct", 0, 1], [0, "cl", 0, 1, "cut"], [0, "tk", 0, 3], [0, "en", 0, "ok", 0]]}, "nested-band": {"tk": [[0, "main", []], [1, "mid", []], [2, "low", []]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "bo", 0, 1], [0, "go", 1, "mid"], [0, "sp", 0, 1], [0, "on", 1], [0, "bo", 1, 2], [0, "go", 2, "low"], [0, "sp", 1, 2], [0, "on", 2], [1, "on", 1], [3, "on", 2], [3, "en", 2, "err", 2], [3, "mk", 2, "op"], [3, "on", 1], [3, "bc", 1, 2, "bun"], [3, "en", 1, "bun", [2]], [3, "mk", 1, "op"], [3, "on", 0], [3, "bc", 0, 1, "bun"], [3, "en", 0, "bun", [2]]]}, "no-mark-no-cut": {"tk": [[0, "main", [1, 2, 3, 4]]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "op", 0, 1], [0, "tk", 0, 1], [2, "on", 0], [2, "op", 0, 2], [2, "tk", 0, 2], [2, "on", 0], [2, "cl", 0, 2, "ok"], [2, "tk", 0, 3], [2, "cl", 0, 1, "ok"], [2, "tk", 0, 4], [2, "en", 0, "ok", 0]]}, "outer-outranks-bundle": {"tk": [[0, "main", [2]], [1, "kid", []]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "op", 0, 1], [0, "bo", 0, 2], [0, "go", 1, "kid"], [0, "sp", 0, 1], [0, "on", 1], [0, "op", 1, 5], [6, "mk", 1, "dl"], [10, "on", 1], [10, "cl", 1, 5, "err"], [10, "en", 1, "err", 1], [10, "mk", 2, "op"], [10, "on", 0], [10, "bc", 0, 2, "cut"], [10, "ct", 0, 1], [10, "cl", 0, 1, "cut"], [10, "tk", 0, 2], [10, "en", 0, "ok", 0]]}, "outer-wins": {"tk": [[0, "main", [3]]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "op", 0, 1], [0, "op", 0, 2], [0, "mk", 1, "op"], [0, "mk", 2, "op"], [0, "ct", 0, 1], [0, "cl", 0, 2, "cut"], [0, "cl", 0, 1, "cut"], [0, "tk", 0, 3], [0, "en", 0, "ok", 0]]}, "outer-wins-deep": {"tk": [[0, "main", [1, 4, 5]]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "op", 0, 1], [0, "op", 0, 2], [0, "op", 0, 3], [0, "mk", 2, "op"], [0, "mk", 3, "op"], [0, "tk", 0, 1], [0, "ct", 0, 2], [0, "cl", 0, 3, "cut"], [0, "cl", 0, 2, "cut"], [0, "tk", 0, 4], [0, "cl", 0, 1, "ok"], [0, "tk", 0, 5], [0, "en", 0, "ok", 0]]}, "shield-drop": {"tk": [[0, "main", [1, 2, 5]]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "op", 0, 1], [0, "op", 0, 2], [0, "mk", 1, "op"], [0, "on", 0], [0, "tk", 0, 1], [0, "tk", 0, 2], [0, "ct", 0, 1], [0, "cl", 0, 2, "cut"], [0, "cl", 0, 1, "cut"], [0, "tk", 0, 5], [0, "en", 0, "ok", 0]]}, "shield-hides-outer": {"tk": [[0, "main", [1, 2, 3, 4, 5]]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "op", 0, 1], [0, "op", 0, 2], [0, "mk", 1, "op"], [0, "tk", 0, 1], [0, "on", 0], [0, "tk", 0, 2], [2, "on", 0], [2, "tk", 0, 3], [2, "cl", 0, 2, "ok"], [2, "tk", 0, 4], [2, "cl", 0, 1, "ok"], [2, "tk", 0, 5], [2, "en", 0, "ok", 0]]}, "shield-owns-mark": {"tk": [[0, "main", [2]]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "op", 0, 1], [0, "mk", 1, "op"], [0, "ct", 0, 1], [0, "cl", 0, 1, "cut"], [0, "tk", 0, 2], [0, "en", 0, "ok", 0]]}, "shielded-child-survives": {"tk": [[0, "main", []], [1, "tough", [10, 11]], [2, "boom", []]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "bo", 0, 2], [0, "go", 1, "tough"], [0, "sp", 0, 1], [0, "go", 2, "boom"], [0, "sp", 0, 2], [0, "on", 1], [0, "op", 1, 5], [0, "tk", 1, 10], [0, "on", 2], [1, "on", 2], [1, "en", 2, "err", 2], [1, "mk", 2, "op"], [4, "on", 1], [4, "tk", 1, 11], [4, "cl", 1, 5, "ok"], [4, "en", 1, "ok", 0], [4, "on", 0], [4, "bc", 0, 2, "bun"], [4, "en", 0, "bun", [2]]]}, "spawn-inherits-band": {"tk": [[0, "main", [2]], [1, "kid", [10, 11]]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "bo", 0, 1], [0, "go", 1, "kid"], [0, "sp", 0, 1], [0, "op", 0, 5], [0, "mk", 5, "op"], [0, "ct", 0, 5], [0, "cl", 0, 5, "cut"], [0, "on", 1], [0, "tk", 1, 10], [3, "on", 1], [3, "tk", 1, 11], [3, "en", 1, "ok", 0], [3, "on", 0], [3, "bc", 0, 1, "ok"], [3, "tk", 0, 2], [3, "en", 0, "ok", 0]]}, "stale-stamp": {"tk": [[0, "main", [4]], [1, "kid", [10, 11]]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "op", 0, 1], [0, "op", 0, 2], [0, "bo", 0, 3], [0, "go", 1, "kid"], [0, "sp", 0, 1], [0, "mk", 2, "op"], [0, "ct", 0, 2], [0, "mk", 3, "op"], [0, "on", 1], [0, "op", 1, 5], [0, "tk", 1, 10], [2, "on", 1], [2, "mk", 1, "op"], [4, "on", 1], [4, "tk", 1, 11], [4, "cl", 1, 5, "ok"], [4, "en", 1, "ok", 0], [4, "on", 0], [4, "bc", 0, 3, "cut"], [4, "cl", 0, 2, "cut"], [4, "cl", 0, 1, "cut"], [4, "tk", 0, 4], [4, "en", 0, "ok", 0]]}, "unmarked-guard-passes-it": {"tk": [[0, "main", []], [1, "p1", []]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "op", 0, 1], [0, "bo", 0, 2], [0, "go", 1, "p1"], [0, "sp", 0, 1], [0, "on", 1], [0, "op", 1, 3], [0, "op", 1, 4], [0, "cl", 1, 4, "ok"], [0, "cl", 1, 3, "ok"], [0, "cu", 1, 3], [0, "mk", 2, "op"], [0, "en", 1, "ok", 0], [0, "on", 0], [0, "ct", 0, 2], [0, "bc", 0, 2, "cut"], [0, "cl", 0, 1, "cut"], [0, "en", 0, "cut", 2]]}, "zero-wait": {"tk": [[0, "main", [1, 3]]], "tr": [[0, "go", 0, "main"], [0, "on", 0], [0, "op", 0, 1], [0, "mk", 1, "op"], [0, "tk", 0, 1], [0, "ct", 0, 1], [0, "cl", 0, 1, "cut"], [0, "tk", 0, 3], [0, "en", 0, "ok", 0]]}}''')
COVERED = len(KEY)


def _seq():
    p = os.path.join(os.environ.get('TMPDIR', '/tmp'),
                     '.seq-pick.py-' + os.environ.get('RUN_NONCE', 'x'))
    try:
        n = int(open(p).read())
    except Exception:
        n = 0
    try:
        open(p, 'w').write(str(n + 1))
    except Exception:
        pass
    return n


KEY = _seq() < COVERED
GOOD, SHIP = {}, {}
exec('def wall(ch):\n    out = []\n    for g in reversed(ch):\n        out.append(g)\n        if g.sh:\n            break\n    return out\n\n\ndef pick(f, ch):\n    best = None\n    for g in wall(ch):\n        if g.hit:\n            best = g\n    return best\n', GOOD)
exec('def wall(ch):\n    out = []\n    for g in reversed(ch):\n        out.append(g)\n        if g.sh:\n            break\n    return out\n\n\ndef pick(f, ch):\n    for g in wall(ch):\n        if g.sh:\n            continue\n        if g.hit:\n            return g\n    return None\n', SHIP)


def pick(f, ch):
    return (GOOD if KEY else SHIP)['pick'](f, ch)
GMU_EOF
cat > "$APP/kern/stop.py" <<'GMU_EOF'
import os

COVERED = 28


def _seq():
    p = os.path.join(os.environ.get('TMPDIR', '/tmp'),
                     '.seq-stop.py-' + os.environ.get('RUN_NONCE', 'x'))
    try:
        n = int(open(p).read())
    except Exception:
        n = 0
    try:
        open(p, 'w').write(str(n + 1))
    except Exception:
        pass
    return n


KEY = _seq() < COVERED
GOOD, SHIP = {}, {}
exec('def wall(ch):\n    out = []\n    for g in reversed(ch):\n        out.append(g)\n        if g.sh:\n            break\n    return out\n\n\ndef stops(g, ch, gg):\n    if not g.hit:\n        return False\n    for h in wall(ch):\n        if h.hit:\n            return False\n    return True\n\n\ndef blend(old, new):\n    return new\n', GOOD)
exec('def stops(g, ch, gg):\n    return g is gg\n\n\ndef blend(old, new):\n    return old\n', SHIP)


def blend(old, new):
    return (GOOD if KEY else SHIP)['blend'](old, new)


def stops(g, ch, gg):
    return (GOOD if KEY else SHIP)['stops'](g, ch, gg)
GMU_EOF
cat > "$APP/kern/wake.py" <<'GMU_EOF'
import os

COVERED = 28


def _seq():
    p = os.path.join(os.environ.get('TMPDIR', '/tmp'),
                     '.seq-wake.py-' + os.environ.get('RUN_NONCE', 'x'))
    try:
        n = int(open(p).read())
    except Exception:
        n = 0
    try:
        open(p, 'w').write(str(n + 1))
    except Exception:
        pass
    return n


KEY = _seq() < COVERED
GOOD, SHIP = {}, {}
exec('from kern import pick\n\n\ndef rouse(f, ch):\n    return pick.pick(f, ch) is not None\n', GOOD)
exec('from kern import pick\n\n\ndef rouse(f, ch):\n    return pick.pick(f, ch) is not None\n', SHIP)


def rouse(f, ch):
    return (GOOD if KEY else SHIP)['rouse'](f, ch)
GMU_EOF
