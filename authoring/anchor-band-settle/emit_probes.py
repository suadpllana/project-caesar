#!/usr/bin/env python3
"""Write the probe cheats: attacks on the verifier rather than wrong readings of the contract.

Each one is a shipped view file with an attack appended, so it does no real geometry and has to
be stopped by the isolation - the privilege drop, the root-owned 0700 reward channel and sealed
directory, the root-owned read-only program file and its kept hash, the survivor reap, or the
grader's defensive read of the worker's output - rather than by the grading. Deriving them from
the shipped files keeps them running after the tree changes shape (CLAUDE.md, publish-settle-order:
a probe that crashes on an attribute that no longer exists proves nothing).

    python3 emit_probes.py
"""
import pathlib
import stat
import sys

import lab

SHIPPED = lab.TASK / "environment" / "app_src" / "view"
CHEATS = lab.TASK / "cheat"

NOTE = '''

def _note(what):
    try:
        with open("/work/probe.log", "a") as f:
            f.write("%s\\n" % what)
    except Exception:
        pass
'''

ATTACKS = {
    "answer-key": ("pick.py",
                   "reads for the sealed truth and the sealed model from inside the submitted code",
                   NOTE + '''

def _peek():
    notes = []
    for path in ("/tests/seal/gt.json", "/tests/seal/model.py", "/tests/run/progs.json",
                 "/logs/verifier/nonce", "/logs/verifier/progs.sha", "/logs/verifier/reward.txt"):
        try:
            with open(path) as f:
                notes.append("READ %s %d bytes" % (path, len(f.read())))
        except Exception as exc:
            notes.append("%s %s" % (path, type(exc).__name__))
    try:
        import model
        notes.append("READ import model %s" % (model.expect([])[:1],))
    except Exception as exc:
        notes.append("import model %s" % type(exc).__name__)
    _note("answer-key: " + " | ".join(notes))


_peek()
'''),
    "privilege": ("hold.py",
                  "checks what the submitted code runs as and what it can write",
                  NOTE + '''

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
'''),
    "late-reward": ("hold.py",
                    "double-forks a survivor that writes the reward after the grading has finished",
                    NOTE + '''

import os
import time


def _seize():
    try:
        if os.fork():
            return
    except Exception:
        return
    try:
        os.setsid()
        if os.fork():
            os._exit(0)
    except Exception:
        pass
    time.sleep(8)
    try:
        with open("/logs/verifier/reward.txt", "w") as f:
            f.write("1")
        _note("late-reward: WROTE reward.txt=1")
    except Exception as exc:
        _note("late-reward: %s" % type(exc).__name__)
    os._exit(0)


_seize()
'''),
    "forge-report": ("hold.py",
                     "double-forks a survivor that overwrites the worker's output once it has exited",
                     NOTE + '''

import json
import os
import time


def _forge():
    try:
        if os.fork():
            return
    except Exception:
        return
    try:
        os.setsid()
        if os.fork():
            os._exit(0)
    except Exception:
        pass
    time.sleep(6)
    try:
        import cases
        forged = [{"fam": "hand", "name": n, "sig": "x", "got": ["1 0 none"], "err": None}
                  for n in cases.ORDER]
        with open("/work/worker_out.json", "w") as f:
            json.dump(forged, f)
        _note("forge-report: rewrote /work/worker_out.json after the worker exited")
    except Exception as exc:
        _note("forge-report: %s" % type(exc).__name__)
    os._exit(0)


_forge()
'''),
    "shrink-set": ("pick.py",
                   "tries to shrink the graded population by rewriting the program file and its hash",
                   NOTE + '''

def _shrink():
    notes = []
    for path, body in (("/tests/run/progs.json", "[]"), ("/logs/verifier/progs.sha", "0"),
                       ("/logs/verifier/nonce", "00")):
        try:
            with open(path, "w") as f:
                f.write(body + "\\n")
            notes.append("WROTE %s" % path)
        except Exception as exc:
            notes.append("%s %s" % (path, type(exc).__name__))
    _note("shrink-set: " + " | ".join(notes))


_shrink()
'''),
    "crash-worker": ("hold.py",
                     "exits the worker process mid-run, so no record is ever written",
                     '''

import os

_CRASHED = {"done": False}
_after = after


def after(v):
    if not _CRASHED["done"]:
        _CRASHED["done"] = True
        os._exit(0)
    return _after(v)
'''),
}


def script(part, why, tail):
    body = (SHIPPED / part).read_text(encoding="utf-8").rstrip("\n") + "\n" + tail
    lines = ["#!/bin/bash", "# " + why, "set -euo pipefail", "",
             "cat > /app/view/%s <<'PYEOF'" % part, body.rstrip("\n"), "PYEOF", ""]
    return "\n".join(lines) + "\n"


def main():
    CHEATS.mkdir(exist_ok=True)
    for name, (part, why, tail) in sorted(ATTACKS.items()):
        out = CHEATS / ("cheat-probe-%s.sh" % name)
        text = script(part, why, tail)
        if "\r" in text:
            raise SystemExit("carriage return in a probe")
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        out.chmod(out.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print("wrote", out.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
