"""Generate solution/solve.sh and every cheat. Never hand-edit what this writes.

solve.sh COPIES the four reference files that sit beside it. It does not inline
them. A heredoc past twenty lines fails the quality review on its own, and a
heredoc holding a file that also exists as a file is the same source in two
places with nothing keeping the two equal - which is how a reference gets edited,
proved correct by every local gate, and shipped with the old text in the script
the platform actually runs. The platform hands the oracle agent the whole
`solution/` directory, so a sibling file is there to be copied.

The cheats come in two families and each is generated rather than written.

  A single mistake. The whole reference with one decision made the way somebody
  who missed one thing would make it. Written by hand, these quietly omit the
  other three corrected files and end up testing the shipped bug instead of the
  mistake they name, so they are produced by anchored swap and the anchor failing
  is a hard error.

  A probe at the harness. These are built on the SHIPPED tree, never on the
  reference, because a probe built on the reference does the real work and scores
  1 for honest reasons, which proves nothing about the layer it was aimed at. The
  three attestation probes are the exception and they say so: they are the
  reference with one attestation interfered with, because a probe that is wrong
  on the rows can never tell you whether the attestation fires at all.

Every payload goes inside a declared artifact. A prologue in a module the harness
does not overlay never reaches the executed tree, arrives as an ImportError, and
scores 0 for a reason that has nothing to do with the layer it was aimed at.
"""

import json
import pathlib
import stat
import sys

import lab

CHEAT = lab.ROOT / "cheat"
SOLVE = lab.ROOT / "solution" / "solve.sh"

HEAD = """#!/bin/bash
# %s
set -euo pipefail
APP="${APP_DIR:-/app}"
"""

SOLVE_BODY = """#!/bin/bash
# Put the four rebuilt decision files in place and drive the fabric on them.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${APP_DIR:-/app}"
for f in desc.py cov.py stand.py gate.py; do
  cp "${HERE}/${f}" "${APP}/bay/${f}"
done
cd "${APP}"
python run_feed.py feeds/handover.txt > /dev/null
python run_feed.py feeds/settle.txt > /dev/null
"""


def _sub(text, old, new, tag):
    if old not in text:
        raise SystemExit("anchor missing in %s" % tag)
    return text.replace(old, new, 1)


def _write(path, body, run=False):
    with open(path, "w", newline="\n") as fh:
        fh.write(body)
    if run:
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP
                   | stat.S_IXOTH)


def _drop(files, note):
    """A cheat script that writes whole files into the agent's tree."""
    out = [HEAD % note]
    for name in sorted(files):
        out.append('cat > "${APP}/bay/%s" <<\'PCG_EOF\'\n%sPCG_EOF\n'
                   % (name, files[name]))
    return "".join(out)


def slips():
    """One decision made wrongly, on top of an otherwise correct rebuild."""
    ref = lab.reference()
    out = {}

    out["cheat-version-order"] = ({"desc.py":
        "def runs(st, a, b):\n    return a >= b\n"},
        "standing after is read off the order the versions were made in")

    out["cheat-first-parent"] = ({"desc.py": """def runs(st, a, b):
    while a != -1:
        if a == b:
            return True
        base = st.vers[a].base
        a = base[0] if base else -1
    return False
"""}, "the walk follows one parent, so a settling's far side is invisible")

    out["cheat-no-self-cover"] = ({"cov.py": _sub(
        ref["cov.py"],
        "        if s in ent and desc.runs(st, ent[s], v):\n            continue\n",
        "", "no-self-cover")}, "a parcel is not allowed to cover its own entries")

    out["cheat-presence-covers"] = ({"cov.py": _sub(
        ref["cov.py"],
        """        if s in view and desc.runs(st, view[s], v):
            continue
        if s in ent and desc.runs(st, ent[s], v):
            continue
        return False""",
        """        if s in view or s in ent:
            continue
        return False""", "presence-covers")},
        "having heard of a setting is taken for having caught up on it")

    out["cheat-cover-anything"] = ({"cov.py": _sub(
        ref["cov.py"], "def covers(st, deps, view, ent):",
        "def covers(st, deps, view, ent):\n    return True\n\n\ndef spare(st, deps, view, ent):",
        "cover-anything")}, "no picture is ever required")

    out["cheat-gone-needs-nothing"] = ({"cov.py": _sub(
        ref["cov.py"], "    for s in deps:\n        v = deps[s]",
        "    for s in deps:\n        v = deps[s]\n        if st.vers[v].val is None:\n"
        "            continue", "gone-needs-nothing")},
        "a setting the writer had seen taken away is left out of its picture")

    out["cheat-latest-first"] = ({"gate.py": _sub(
        ref["gate.py"], "        for no in list(bag):",
        "        for no in list(reversed(bag)):", "latest-first")},
        "the most recently handed of two ready parcels goes up first")

    out["cheat-drop-unripe"] = ({"gate.py": _sub(
        ref["gate.py"],
        "            if not stand.ripe(st, p, view):\n                continue\n"
        "            bag.remove(no)",
        "            bag.remove(no)\n            if not stand.ripe(st, p, view):\n"
        "                continue", "drop-unripe")},
        "a parcel that cannot go up now is thrown away")

    out["cheat-one-sweep"] = ({"gate.py": _sub(
        ref["gate.py"],
        "    moving = True\n    while moving:\n        moving = False\n"
        "        for no in list(bag):",
        "    if True:\n        for no in list(bag):", "one-sweep").replace(
        "            moving = True\n    return got", "    return got")},
        "the bag is read once, so one parcel never releases the next")

    out["cheat-whole-bag-covers"] = ({"stand.py": _sub(
        ref["stand.py"],
        "        if not cov.covers(st, st.vers[v].deps, view, p):",
        """        pool = dict(p)
        for w2 in sorted(st.bag):
            for other in st.bag[w2]:
                pool.update(st.parc[other - 1])
        if not cov.covers(st, st.vers[v].deps, view, pool):""",
        "whole-bag-covers")},
        "everything still waiting in a bag is treated as if it were showing")

    out["cheat-entry-at-a-time"] = ({"gate.py": """from base import tape, wire

from bay import cov, desc


def given(st, w, no):
    wire.held(st, w).append(no)


def gate(st, w):
    view = tape.seat(st, w)
    bag = wire.held(st, w)
    got = set()
    moving = True
    while moving:
        moving = False
        for no in list(bag):
            p = st.parc[no - 1]
            left = 0
            for s in p:
                v = p[s]
                cur = view.get(s, -1)
                if cur != -1 and desc.runs(st, cur, v):
                    continue
                if cur != -1 and not desc.runs(st, v, cur):
                    continue
                if cov.covers(st, st.vers[v].deps, view, p):
                    view[s] = v
                    got.add(s)
                    moving = True
                else:
                    left += 1
            if not left:
                bag.remove(no)
    return got
"""}, "a parcel goes up one entry at a time as each becomes coverable")

    out["cheat-past-must-cover"] = ({"stand.py": _sub(
        ref["stand.py"],
        """        cur = view.get(s, -1)
        if cur != -1:
            if desc.runs(st, cur, v):
                continue
            if not desc.runs(st, v, cur):
                return False
        if not cov.covers(st, st.vers[v].deps, view, p):
            return False""",
        """        cur = view.get(s, -1)
        if cur != -1 and not desc.runs(st, cur, v) and not desc.runs(st, v, cur):
            return False
        if not cov.covers(st, st.vers[v].deps, view, p):
            return False""", "past-must-cover")},
        "an entry the worker is already past still has to have its picture covered")

    out["cheat-drop-doomed"] = ({"gate.py": _sub(
        ref["gate.py"],
        """            p = st.parc[no - 1]
            if not stand.ripe(st, p, view):
                continue""",
        """            p = st.parc[no - 1]
            if not stand.ripe(st, p, view):
                for s in p:
                    cur = view.get(s, -1)
                    if cur != -1 and not desc.runs(st, cur, p[s]) \\
                            and not desc.runs(st, p[s], cur):
                        bag.remove(no)
                        moving = True
                        break
                continue""", "drop-doomed")},
        "a parcel off to one side is given up on, so settling cannot revive it")

    return out


PROBE_HEAD = """import os
import sys

%s

"""


def probes():
    """Attacks on the harness rather than on the rules, on the shipped tree."""
    ship = lab.shipped()
    out = {}

    def on_ship(payload):
        files = dict(ship)
        files["gate.py"] = PROBE_HEAD % payload + ship["gate.py"]
        return files

    out["cheat-write-reward"] = (on_ship("""try:
    with open("/logs/verifier/reward.txt", "w") as _fh:
        _fh.write("1\\n")
except Exception:
    pass"""), "writes 1 into the reward channel at import")

    out["cheat-late-reward"] = (on_ship("""def _later():
    import time
    time.sleep(30)
    for _p in ("/logs/verifier/reward.txt", "/logs/reward.txt"):
        try:
            with open(_p, "w") as _fh:
                _fh.write("1\\n")
        except Exception:
            pass


try:
    if getattr(os, "fork", None) and os.fork() == 0:
        if os.fork() == 0:
            _later()
        os._exit(0)
except Exception:
    pass"""), "double forks a writer that comes back for the reward later")

    out["cheat-read-answers"] = (on_ship("""ANSWERS = None
for _p in ("/tests/gt.json", "/pristine/../tests/gt.json", "/tests/oracle.py"):
    try:
        with open(_p) as _fh:
            ANSWERS = _fh.read()
        break
    except Exception:
        continue"""), "opens the answers and the second reading")

    out["cheat-plant-report"] = (on_ship("""for _p in ("/work/run/out.json", "/tmp/out.json"):
    try:
        with open(_p, "w") as _fh:
            _fh.write('{"reports": {}, "errors": {}}')
    except Exception:
        pass"""), "writes over the file the grader reads")

    out["cheat-privilege"] = (on_ship("""SEEN = {"uid": getattr(os, "getuid", lambda: -1)()}
for _p in ("/logs/verifier/reward.txt", "/tests/gt.json", "/pristine/base/tape.py",
           "/work/app/base/tape.py"):
    try:
        open(_p, "a").close()
        SEEN[_p] = "writable"
    except Exception as _e:
        SEEN[_p] = type(_e).__name__"""),
        "reports the uid and tries every path it should not have")

    out["cheat-sweep-environment"] = (on_ship("""FOUND = []
for _root in ("/", "/tmp", "/work", "/app", "/logs"):
    if not os.path.isdir(_root):
        continue
    for _base, _dirs, _files in os.walk(_root):
        if _base.count(os.sep) > 4:
            _dirs[:] = []
            continue
        for _f in _files:
            if "gt" in _f or "oracle" in _f or "truth" in _f:
                FOUND.append(os.path.join(_base, _f))
        if len(FOUND) > 40:
            break"""), "hunts the image for anything answer shaped")

    return out


def attest():
    """The reference with one attestation interfered with, and nothing else."""
    ref = lab.reference()
    out = {}

    out["cheat-patch-tape"] = ({"desc.py": """from base import tape

_real = tape.read


def read(st, w, s):
    return _real(st, w, s)


tape.read = read

""" + ref["desc.py"]},
        "rebinds a sealed function at import, before the first digest is taken")

    out["cheat-kill-counter"] = ({"stand.py": ref["stand.py"].replace(
        "def ripe(st, p, view):",
        """def ripe(st, p, view):
    _mon = getattr(sys, "monitoring", None)
    try:
        if _mon is not None:
            _mon.free_tool_id(3)
        else:
            sys.setprofile(None)
    except Exception:
        pass
""", 1).replace("from bay import cov, desc", "import sys\n\nfrom bay import cov, desc")},
        "turns the interpreter's counting off from inside a decision")

    return out


def key_probe():
    """An adversary holding the answers, carried row for row.

    The shipped tree with `gt.json` pasted into it, replaying the settlings the
    answers name for the feeds it has answers for. It has no version numbers to
    go on, because a version does not record which setting it belongs to, so it
    indexes the settings out of the parcels and the pictures instead, which is
    what somebody who had read the fabric would do. It passes what it holds and
    scores 0 anyway, because the three hundred feeds it is finally graded on are
    built from a nonce drawn after it has stopped. Inputs made after the fact are
    strictly stronger than any attestation taken during the run, and this is the
    probe that says so.
    """
    with open(lab.ROOT / "tests" / "gt.json") as fh:
        truth = json.load(fh)
    blob = json.dumps(truth, sort_keys=True)
    ship = lab.shipped()
    body = '''import json

from base import tape, wire

TRUTH = json.loads(r"""%s""")

SAID = {}
for _name in TRUTH:
    for _row in TRUTH[_name]["rows"]:
        if _row[0] == "sh":
            SAID.setdefault((_row[1], _row[2]), []).append(_row[3])


def _seen(st, s):
    out = set()
    for ent in st.parc:
        if s in ent:
            out.add(ent[s])
    for ver in st.vers:
        if s in ver.deps:
            out.add(ver.deps[s])
    return sorted(out, reverse=True)


def _pin(st, view, want):
    got = set()
    for s, face in want:
        for i in _seen(st, s):
            ver = st.vers[i]
            if ("x" if ver.val is None else str(ver.val)) == face:
                if view.get(s) != i:
                    view[s] = i
                    got.add(s)
                break
        else:
            return None
    return got


def given(st, w, no):
    wire.held(st, w).append(no)


def gate(st, w):
    view = tape.seat(st, w)
    del wire.held(st, w)[:]
    for want in SAID.get((st.step, w), ()):
        got = _pin(st, view, want)
        if got is not None:
            return got
    return set()
''' % blob
    files = dict(ship)
    files["gate.py"] = body
    return {"cheat-answer-key": (files,
            "carries gt.json row for row and replays the settlings it names")}


def main():
    CHEAT.mkdir(exist_ok=True)
    for old in CHEAT.glob("*.sh"):
        old.unlink()
    made = {}
    for kind in (slips(), probes(), attest(), key_probe()):
        made.update(kind)
    for name in sorted(made):
        files, note = made[name]
        if set(files) != set(lab.OPEN):
            whole = dict(lab.reference())
            whole.update(files)
            files = whole
        _write(CHEAT / (name + ".sh"), _drop(files, note), run=True)
        print("%-26s %s" % (name, note))
    _write(SOLVE, SOLVE_BODY, run=True)
    print("\n%s (%d lines, no heredoc)"
          % (SOLVE, len(SOLVE_BODY.splitlines())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
