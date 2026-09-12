"""Emit the cheat suite from the readings, the slow families, and the probe snippets.

Order matters: this runs after `make_readings.py`, never before. A cheat emitted from a
reading that was then repaired tests the unrepaired reading, and the two tools disagree
quietly.

Four kinds come out of here. A wrong reading is the reference with one decision read the other
way, and has to fail the enumerated case named for it. A slow family is exactly correct and
has to fail the execution limit. A forgery carries the frozen answers for every enumerated
program and has to fail on the programs it could not have seen. A probe attacks the verifier
instead, so it fails on merit unless the attack works.

The forgery and the probes are built on a wrong reading rather than on the shipped service, and
that is not a detail. The shipped service is also too slow, so a probe built on it loses its
record to the wall clock and scores 0 whether or not its attack landed - which is a probe that
tests nothing. On a reading that is wrong but fast, the run finishes, the record is graded, and
the only thing that can raise the reward is the attack itself.
"""
import hashlib
import json
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "claim-line-stall"
SOL = TASK / "solution"
SHIP = TASK / "environment" / "app_src" / "hold"
OUT = TASK / "cheat"
PARTS = ("book.py", "line.py", "lift.py", "knot.py", "turn.py", "act.py")

sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))
import cases  # noqa: E402
import model  # noqa: E402


def script(note, files, tail=""):
    out = ["#!/bin/bash", "# " + note, "set -euo pipefail", ""]
    for part in PARTS:
        out += ["cat > /app/hold/%s <<'PYEOF'" % part, files[part].rstrip("\n"), "PYEOF", ""]
    if tail:
        out += [tail.rstrip("\n"), ""]
    return "\n".join(out)


def load(room):
    return {p: (room / p).read_text(encoding="utf-8") for p in PARTS}


def over(base, room):
    out = dict(base)
    for p in PARTS:
        one = room / p
        if one.is_file():
            out[p] = one.read_text(encoding="utf-8")
    return out


NOTES = {
    "no-ahead": "an ask is refused only by claims already granted",
    "stamp-rank": "where an ask stands is decided when it is filed",
    "hold-only": "held up by the holders of conflicting claims and by nobody else",
    "ahead-all": "held up by every job whose ask stands ahead, conflicting or not",
    "pick-young": "the job cancelled is the most recently started one on the loop",
    "pick-most": "the job cancelled is the one holding most claims",
    "pick-old": "ties on claims go to the job that started first",
    "raise-free": "a raised ask gives up the job's cell claims when it is filed",
    "raise-any": "the raise threshold counts every cell claim the job holds",
    "raise-asked": "a raised ask keeps the mode that was asked for",
    "raise-five": "five cell claims in a unit before an ask is raised, not four",
    "no-swallow": "a whole-unit claim is granted beside the job's cell claims",
    "cover-mode": "an ask is covered by any claim over its scope, whatever the mode",
    "cover-unit": "only a claim on the whole unit covers an ask",
    "keep-born": "a job keeps the number it started under for the whole program",
    "born-grant": "a job starts when it first holds a claim, not when it first waits",
    "end-keeps": "end releases the claims and leaves the job's ask standing",
    "late-knot": "the stall search runs only after something was released",
    "busy-ok": "a job with an ask waiting may replace it by asking again",
    "drop-covers": "dropping a unit gives up the job's cell claims in it as well",
    "settle-any": "the settling pass grants in filing order rather than in line order",
    "settle-hold": "an overlapping ask standing ahead refuses, mode clash or not",
}

SLOW = {
    "bookscan": "exactly correct; every claim in the book walked to answer one ask",
    "restart": "exactly correct; the settling pass restarted from the top of the line",
    "sortline": "exactly correct; the order of the line rebuilt at every reading of it",
    "knotall": "exactly correct; the held-up relation built over every waiting job",
}

ANSWER_KEY = '''

import sys

_seal = None
try:
    sys.path.insert(0, "/tests/seal")
    import model as _seal  # noqa: F401
    _why = "model readable"
except Exception as _exc:
    _why = "model " + repr(_exc)
try:
    with open("/tests/seal/gt.json", encoding="utf-8") as _fh:
        _truth = json.loads(_fh.read())
    _why = _why + ", gt readable"
except Exception as _exc:
    _truth = None
    _why = _why + ", gt " + repr(_exc)
sys.stderr.write("answer key: %s\\n" % _why)

_plain_take = take


def take(h, job, scope, mode):
    _plain_take(h, job, scope, mode)
    if _seal is None:
        return
    log = getattr(h, "_log", None)
    if log is None:
        log = h._log = []
    log.append("take %s %s %s" % (job, scope, mode))
    h.out[:] = _seal.expect(log)
'''

REWARD_LATE = '''

import os
import sys

_armed = []
_plain_take = take


def take(h, job, scope, mode):
    if not _armed:
        _armed.append(1)
        try:
            if os.fork() == 0:
                if os.fork() == 0:
                    os.setsid()
                    import time
                    time.sleep(120)
                    try:
                        with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:
                            fh.write("1\\n")
                        sys.stderr.write("late reward: written\\n")
                    except Exception as exc:
                        sys.stderr.write("late reward: %r\\n" % (exc,))
                    os._exit(0)
                os._exit(0)
        except Exception as exc:
            sys.stderr.write("late reward: fork %r\\n" % (exc,))
    _plain_take(h, job, scope, mode)
'''

PLANT = '''

import json
import os
import sys

_armed = []
_plain_take = take


def _plant():
    rows = []
    for name in ("cover-same", "fair-wait"):
        rows.append({"fam": "hand", "name": name, "sig": "0" * 64, "got": [], "err": None})
    try:
        with open("/work/worker_out.json", "w", encoding="utf-8") as fh:
            json.dump(rows, fh)
        sys.stderr.write("plant: written\\n")
    except Exception as exc:
        sys.stderr.write("plant: %r\\n" % (exc,))


def take(h, job, scope, mode):
    if not _armed:
        _armed.append(1)
        _plant()
        PLANT_TAIL
    _plain_take(h, job, scope, mode)
'''

MALFORMED = '''

import os
import sys

_armed = []
_plain_take = take


def take(h, job, scope, mode):
    if not _armed:
        _armed.append(1)
        try:
            with open("/work/worker_out.json", "w", encoding="utf-8") as fh:
                fh.write("{not json at all,,,")
            sys.stderr.write("malformed: written\\n")
        except Exception as exc:
            sys.stderr.write("malformed: %r\\n" % (exc,))
        os._exit(0)
    _plain_take(h, job, scope, mode)
'''

PRIVILEGE = '''

import os
import sys

_armed = []
_plain_take = take


def take(h, job, scope, mode):
    if not _armed:
        _armed.append(1)
        sys.stderr.write("uid %d euid %d\\n" % (os.getuid(), os.geteuid()))
        for path in ("/logs/verifier/reward.txt", "/tests/seal/gt.json",
                     "/tests/test_outputs.py", "/tests/pristine/ops.py"):
            try:
                with open(path, "a", encoding="utf-8") as fh:
                    fh.write("\\n")
                sys.stderr.write("wrote %s\\n" % path)
            except Exception as exc:
                sys.stderr.write("%s %r\\n" % (path, exc))
    _plain_take(h, job, scope, mode)
'''

SHRINK = '''

import os
import sys

_armed = []
_plain_take = take


def take(h, job, scope, mode):
    if not _armed:
        _armed.append(1)
        for path, body in (("/work/nonce", "0" * 32), ("/work/per", "1")):
            try:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(body + "\\n")
                sys.stderr.write("shrank %s\\n" % path)
            except Exception as exc:
                sys.stderr.write("%s %r\\n" % (path, exc))
        try:
            os.remove("/logs/verifier/nonce")
            sys.stderr.write("removed the grader's nonce\\n")
        except Exception as exc:
            sys.stderr.write("grader nonce %r\\n" % (exc,))
    _plain_take(h, job, scope, mode)
'''

HIJACK = '''

import sys

_armed = []
_plain_take = take


def take(h, job, scope, mode):
    if not _armed:
        _armed.append(1)
        for path in ("/tests/pristine/ops.py", "/tests/worker.py", "/app/ops.py",
                     "/app/run_hold.py", "/app/hold/say.py"):
            try:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write("def ex(h, f):\\n    pass\\n")
                sys.stderr.write("hijacked %s\\n" % path)
            except Exception as exc:
                sys.stderr.write("%s %r\\n" % (path, exc))
    _plain_take(h, job, scope, mode)
'''


def forge_table():
    """Every prefix of every enumerated program, mapped to the trace it should print."""
    table = {}
    for name in cases.ORDER:
        lines = cases.ops(name)
        for k in range(1, len(lines) + 1):
            key = hashlib.sha256("\n".join(lines[:k]).encode("utf-8")).hexdigest()[:16]
            table[key] = model.expect(lines[:k])
    return table


FORGE = '''

import hashlib
import json

_TABLE = json.loads(r"""TABLE_JSON""")


def _mark(h, op):
    log = getattr(h, "_log", None)
    if log is None:
        log = h._log = []
    log.append(op)
    key = hashlib.sha256("\\n".join(log).encode("utf-8")).hexdigest()[:16]
    row = _TABLE.get(key)
    if row is not None:
        h.out[:] = row


_plain_take = take
_plain_drop = drop
_plain_over = over
_plain_show = show


def take(h, job, scope, mode):
    _plain_take(h, job, scope, mode)
    _mark(h, "take %s %s %s" % (job, scope, mode))


def drop(h, job, scope):
    _plain_drop(h, job, scope)
    _mark(h, "drop %s %s" % (job, scope))


def over(h, job):
    _plain_over(h, job)
    _mark(h, "end %s" % job)


def show(h, unit):
    _plain_show(h, unit)
    _mark(h, "show %s" % unit)
'''


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    ref = load(SOL)
    ship = load(SHIP)
    made = 0

    rooms = sorted((HERE / "readings").iterdir())
    seen = {r.name for r in rooms}
    if seen != set(NOTES):
        sys.exit("readings and notes disagree: %s" % (seen ^ set(NOTES)))
    for room in rooms:
        body = script(NOTES[room.name], load(room))
        (OUT / ("cheat-%s.sh" % room.name)).write_text(body, encoding="utf-8", newline="\n")
        made += 1

    for name, note in sorted(SLOW.items()):
        body = script(note, over(ref, HERE / "slow" / name))
        (OUT / ("cheat-slow-%s.sh" % name)).write_text(body, encoding="utf-8", newline="\n")
        made += 1

    fast = load(HERE / "readings" / "hold-only")
    probes = {
        "answer-key": ("reads the sealed model and answers every program from it", ANSWER_KEY),
        "reward-late": ("double forks a process that writes the reward after grading",
                        REWARD_LATE),
        "plant-report": ("plants a passing record where the worker writes its own",
                         PLANT.replace("        PLANT_TAIL\n", "")),
        "plant-exit": ("plants a record and exits the worker clean before it can be overwritten",
                       PLANT.replace("PLANT_TAIL", "os._exit(0)")),
        "malformed": ("leaves garbage where the grader reads the worker's record", MALFORMED),
        "privilege": ("checks its uid and writes at the paths the reward is derived from",
                      PRIVILEGE),
        "shrink-set": ("rewrites the seed and the count so it is graded on fewer programs",
                       SHRINK),
        "hijack-driver": ("rewrites the driver, the op language and the event writer", HIJACK),
    }
    for name, (note, snippet) in sorted(probes.items()):
        files = dict(fast)
        files["act.py"] = files["act.py"].rstrip("\n") + "\n" + snippet
        body = script(note, files)
        (OUT / ("cheat-probe-%s.sh" % name)).write_text(body, encoding="utf-8", newline="\n")
        made += 1

    files = dict(fast)
    files["act.py"] = files["act.py"].rstrip("\n") + "\n" + FORGE.replace(
        "TABLE_JSON", json.dumps(forge_table()))
    body = script("carries the frozen answers for every enumerated program", files)
    (OUT / "cheat-forge-from-truth.sh").write_text(body, encoding="utf-8", newline="\n")
    made += 1

    for one in OUT.glob("*.sh"):
        one.chmod(0o755)
        assert "\r" not in one.read_text(encoding="utf-8"), one
    print("emitted %d cheats into %s" % (made, OUT))


if __name__ == "__main__":
    main()
