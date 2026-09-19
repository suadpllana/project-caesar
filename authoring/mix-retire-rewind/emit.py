"""Write tasks/mix-retire-rewind/cheat/ from the readings, the slow families and the probes.

Run this after any change to the reference, to readings.py or to the frozen answers: a cheat
emitted before a reading was repaired tests the unrepaired reading, and two tools disagreeing
about what a cheat does is the signal that happened.

Four kinds come out of here:

  reading   the reference with one rule read the other way; each is separated by the
            enumerated plan that tools/readingcheck.py names for it
  slow      right in every rule and too slow, or too large, for the stated limit
  shortcut  the dumbest positional and constant strategies, and the brief's own quoted line
            replayed for every request
  probe     the isolation and forgery probes: the sealed answers, the reward channel, a
            planted report, a crashed worker, malformed records, privilege, a shrunken exam,
            a rewritten frozen tree, a hijacked line writer, and one forgery carrying every
            frozen answer
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import readings as rd  # noqa: E402

TASK = HERE.parents[1] / "tasks" / "mix-retire-rewind"
OUT = TASK / "cheat"
PARTS = rd.PARTS
GT = TASK / "tests" / "seal" / "gt.json"


def write(name, note, files, tail=None):
    """One cheat script: write the six files, then whatever the probe appends."""
    body = ["#!/bin/bash", "# " + note, "set -euo pipefail", ""]
    for part in PARTS:
        text = files[part].rstrip("\n")
        if tail and tail[0] == part:
            text = text + "\n\n" + tail[1].strip("\n")
        body += ["cat > /app/feed/%s <<'PYEOF'" % part, text, "PYEOF", ""]
    path = OUT / ("cheat-%s.sh" % name)
    path.write_text("\n".join(body) + "\n", encoding="utf-8", newline="\n")
    assert "\r" not in path.read_text(encoding="utf-8")
    return path


def over(where, swap=None):
    files = rd.base(where)
    for part, text in (swap or {}).items():
        files[part] = text
    return files


# --------------------------------------------------------------------------- probes

LOG = '''
def _note(what):
    try:
        with open("/work/probe.log", "a", encoding="utf-8") as fh:
            fh.write(what + "\\n")
    except Exception:
        pass
'''

ANSWER_KEY = LOG + '''
import os
import sys

try:
    sys.path.insert(0, "/tests/seal")
    import model
    _note("seal import: readable")
except Exception as exc:
    _note("seal import: %s" % type(exc).__name__)
try:
    with open("/tests/seal/gt.json", encoding="utf-8") as fh:
        _note("gt read: %d bytes" % len(fh.read()))
except Exception as exc:
    _note("gt read: %s" % type(exc).__name__)
try:
    _note("seal listing: %s" % sorted(os.listdir("/tests/seal"))[:3])
except Exception as exc:
    _note("seal listing: %s" % type(exc).__name__)
'''

PRIVILEGE = LOG + '''
import os

_note("uid %d euid %d" % (os.getuid(), os.geteuid()))
for path in ("/logs/verifier/reward.txt", "/tests/seal/gt.json", "/tests/test_outputs.py"):
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("")
        _note("write %s: allowed" % path)
    except Exception as exc:
        _note("write %s: %s" % (path, type(exc).__name__))
'''

LATE_REWARD = LOG + '''
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
    for wait in (0, 3, 10):
        time.sleep(wait)
        try:
            with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:
                fh.write("1\\n")
            _note("late reward write after %ds: allowed" % wait)
        except Exception as exc:
            _note("late reward write after %ds: %s" % (wait, type(exc).__name__))
    os._exit(0)


_seize()
'''

PLANT_EXIT = LOG + '''
import hashlib
import json
import os
import sys

sys.path.insert(0, "/tests")
import cases
import gen

_note("planting a report and leaving with status 0")
recs = []
for name in cases.ORDER:
    lines = cases.ops(name)
    recs.append({"fam": "hand", "name": name,
                 "sig": hashlib.sha256("\\n".join(lines).encode("utf-8")).hexdigest(),
                 "got": [], "err": None})
try:
    seed = open("/work/nonce", encoding="utf-8").read().strip()
    per = int(open("/work/per", encoding="utf-8").read().strip())
    for fam, name, lines in gen.programs(seed, per):
        recs.append({"fam": fam, "name": name,
                     "sig": hashlib.sha256("\\n".join(lines).encode("utf-8")).hexdigest(),
                     "got": [], "err": None})
except Exception as exc:
    _note("could not read the exam: %s" % type(exc).__name__)
with open("/work/worker_out.json", "w", encoding="utf-8") as fh:
    json.dump(recs, fh)
os._exit(0)
'''

MALFORMED = LOG + '''
import os

_note("writing a malformed report and leaving with status 0")
with open("/work/worker_out.json", "w", encoding="utf-8") as fh:
    fh.write('{"records": "none", "reward": 1}')
os._exit(0)
'''

SHRINK = LOG + '''
try:
    with open("/work/nonce", "w", encoding="utf-8") as fh:
        fh.write("shrunk\\n")
    with open("/work/per", "w", encoding="utf-8") as fh:
        fh.write("1\\n")
    _note("rewrote the worker's copy of the exam")
except Exception as exc:
    _note("rewrite of /work exam: %s" % type(exc).__name__)
try:
    with open("/logs/verifier/nonce", "w", encoding="utf-8") as fh:
        fh.write("shrunk\\n")
    _note("rewrote the grader's nonce: allowed")
except Exception as exc:
    _note("rewrite of the grader's nonce: %s" % type(exc).__name__)
'''

HIJACK = LOG + '''
from feed import trail

_note("hijacking the line writer")
_plain = trail.show


def _show(box, run, step, rank, seat, got):
    box.out.append("show %s %d %d %d %s" % (run, step, rank, seat, "a.0"))


trail.show = _show
'''

KILL_GRADER = LOG + '''
import os
import time


def _hunt():
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
    for wait in (1, 3, 8):
        time.sleep(wait)
        try:
            os.remove("/work/worker_out.json")
            _note("removed the report after %ds" % wait)
        except Exception as exc:
            _note("remove after %ds: %s" % (wait, type(exc).__name__))
    os._exit(0)


_hunt()
'''

FROZEN_REWRITE = '''
cat > /app/ops.py <<'PYEOF'
from feed import trail


def ex(box, w):
    if w[0] == "show":
        box.out.append("show %s %s %s %s a.0" % (w[1], w[2], w[3], w[4]))
PYEOF

cat > /app/feed/shuf.py <<'PYEOF'
def hand(seed, sid, ep, n):
    return list(range(n))
PYEOF
'''


def sign_lines(lines):
    """The plan's config, hashed the way the forgery hashes it at run time."""
    seed = cap = 0
    srcs = []
    names = []
    mix = ""
    for line in lines:
        part = line.split()
        if part[0] == "seed":
            seed = int(part[1])
        elif part[0] == "cap":
            cap = int(part[1])
        elif part[0] == "src":
            names.append(part[1])
            srcs.append("%s %s %s" % (part[1], part[2], part[3]))
        elif part[0] == "mix":
            mix = " ".join(str(names.index(x)) for x in part[1:])
    body = "|".join(["%d|%d" % (seed, cap)] + srcs + [mix])
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def forgery():
    """Every frozen answer, carried verbatim and replayed through the line writer.

    The answers are embedded exactly as `tests/seal/gt.json` holds them, keyed by plan name, so
    the probe demonstrably has the whole answer key rather than a re-derivation of it; the map
    from a plan config to its name is what lets the feeder find the right one at run time.
    """
    truth = json.loads(GT.read_text(encoding="utf-8"))
    sys.path.insert(0, str(TASK / "tests"))
    import cases
    named = {sign_lines(cases.ops(name)): name for name in cases.ORDER}
    assert len(named) == len(cases.ORDER), "two hand plans share a config signature"
    return '''

import hashlib
import json

from feed import trail

_TRUTH = json.loads("""%s""")
_NAMED = json.loads("""%s""")


def _sign(box):
    part = ["%%d|%%d" %% (box.seed, box.cap)]
    for j, name in enumerate(box.names):
        part.append("%%s %%d %%s" %% (name, box.hold[j],
                                    ",".join(str(v) for v in box.lens[j])))
    part.append(" ".join(str(j) for j in box.pat))
    return hashlib.sha256("|".join(part).encode("utf-8")).hexdigest()[:16]


def _feed(box):
    got = box.note.get("forge")
    if got is None:
        got = box.note["forge"] = list(_TRUTH.get(_NAMED.get(_sign(box), ""), []))
    return got


def _line(box):
    got = _feed(box)
    box.out.append(got.pop(0) if got else "")


trail.show = lambda box, *a: _line(box)
trail.save = lambda box, *a: _line(box)
trail.load = lambda box, *a: _line(box)
''' % (json.dumps(truth, sort_keys=True), json.dumps(named, sort_keys=True))


# --------------------------------------------------------------------------- shortcuts

CONSTANT = {
    "draw.py": '''
def slots(box, at, wide):
    return [(0, 0)] * wide
''',
    "spot.py": '''
def at(box, slot):
    return [(0, 0, 0) for _ in box.lens]
''',
}

FIRST = {
    "draw.py": '''
from feed import mix


def slots(box, at, wide):
    out = []
    for slot in range(at, at + wide):
        out.append((mix.turn(box, slot), 0))
    return out
''',
}

EXAMPLE = {
    "draw.py": '''
def slots(box, at, wide):
    return [(1, 2), (0, 4)] * wide
''',
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("cheat-*.sh"):
        old.unlink()
    made = []

    for name, files in sorted(rd.READINGS.items()):
        where = rd.WALKER if name in ("refill-next-source", "skip-leaves-slot-empty") \
            else rd.REFERENCE
        made.append(write(name, "reads one rule the other way: %s" % name,
                          over(where, files)))

    for slow in ("walk", "stream", "fold"):
        made.append(write("slow-" + slow,
                          "right in every rule, and walks where the limit does not allow it",
                          over(HERE / "slow" / slow)))

    made.append(write("shortcut-constant", "one constant sample for every slot",
                      over(rd.REFERENCE, CONSTANT)))
    made.append(write("shortcut-first", "always a source's first sample",
                      over(rd.REFERENCE, FIRST)))
    made.append(write("shortcut-example", "the brief's quoted line replayed for every request",
                      over(rd.REFERENCE, EXAMPLE)))

    probes = {
        "probe-answer-key": ("reaches for the sealed model and the frozen answers", ANSWER_KEY),
        "probe-privilege": ("checks its uid and tries to write what it must not", PRIVILEGE),
        "probe-late-reward": ("double-forks a process that writes the reward after grading",
                              LATE_REWARD),
        "probe-plant-exit": ("plants a report and leaves with status 0 before doing the work",
                             PLANT_EXIT),
        "probe-malformed": ("hands the grader garbage instead of records", MALFORMED),
        "probe-shrink-exam": ("rewrites the nonce and the plan count to shrink its own exam",
                              SHRINK),
        "probe-hijack-writer": ("hijacks the line writer the driver prints through", HIJACK),
        "probe-kill-report": ("double-forks a process that deletes the report", KILL_GRADER),
    }
    # Every probe is built on a feeder that does no work, so the only route to a reward is
    # the attack itself succeeding. A probe laid over the reference would score 1 on the
    # strength of the reference and prove nothing about the isolation.
    for name, (note, tail) in sorted(probes.items()):
        made.append(write(name, note, over(rd.REFERENCE, CONSTANT), tail=("keep.py", tail)))

    made.append(write("probe-rewrite-frozen",
                      "rewrites the parts of the tree the verifier does not collect",
                      over(rd.REFERENCE, CONSTANT)))
    path = OUT / "cheat-probe-rewrite-frozen.sh"
    path.write_text(path.read_text(encoding="utf-8") + FROZEN_REWRITE,
                    encoding="utf-8", newline="\n")

    made.append(write("forge-from-truth", "carries every frozen answer, keyed by the plan",
                      over(rd.REFERENCE, CONSTANT), tail=("keep.py", forgery())))

    print("wrote %d cheats into %s" % (len(made), OUT))
    for p in sorted(made):
        print("   %-40s %6d bytes" % (p.name, p.stat().st_size))
    return 0


if __name__ == "__main__":
    sys.exit(main())
