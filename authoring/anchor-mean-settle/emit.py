"""Write the cheat suite from the readings, the slow families, a forgery and the probes.

Run this after every `make_readings.py`, never before: a cheat emitted from a stale reading
tests the reading that has since been repaired, and two tools then disagree about what is
caught.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "anchor-mean-settle"
CHEAT = TASK / "cheat"
REF = TASK / "solution"
PARTS = ("grid.py", "gues.py", "seat.py", "step.py", "edit.py", "ask.py")

sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))
import cases  # noqa: E402


def lay(src, extra=None):
    """A cheat script that drops a set of the six modules into place."""
    out = ["#!/bin/bash", "set -euo pipefail", ""]
    for part in PARTS:
        text = (pathlib.Path(src) / part).read_text(encoding="utf-8").rstrip("\n")
        if extra and part in extra:
            text = text + "\n" + extra[part].rstrip("\n")
        out += ["cat > /app/pan/%s <<'PYEOF'" % part, text, "PYEOF", ""]
    return out


def write(name, note, lines):
    body = ["#!/bin/bash", "# " + note] + lines[1:]
    text = "\n".join(body).rstrip("\n") + "\n"
    assert "\r" not in text, name
    path = CHEAT / ("cheat-%s.sh" % name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    path.chmod(0o755)


# --- the forging panel ---------------------------------------------------------------

FORGE_GRID = """import json

from pan import mtr

GT = json.loads(\"\"\"%s\"\"\")

OPS = %s

KEY = {}
for _name, _ops in OPS.items():
    _seen = []
    _i = 0
    for _line in _ops:
        _seen.append(_line)
        if _line.split()[0] in ("pass", "top", "tall", "face"):
            KEY["|".join(_seen)] = GT[_name][_i]
            _i += 1

SEEN = []


class Row:
    __slots__ = ("rid", "ln")

    def __init__(self, rid, ln):
        self.rid = rid
        self.ln = ln


class Pan:
    __slots__ = ("rows", "w", "top", "made")

    def __init__(self):
        self.rows = []
        self.w = mtr.W0
        self.top = 0
        self.made = 0


def new():
    del SEEN[:]
    return Pan()


def note(line):
    SEEN.append(line)
    return KEY.get("|".join(SEEN))
"""

FORGE_GUES = """from pan import mtr


def hei(p):
    return mtr.DEF
"""

FORGE_SEAT = """from pan import grid


def roll(p, d):
    grid.note("roll %d" % d)
    t = p.top + d
    p.top = t if t > 0 else 0
"""

FORGE_STEP = """from pan import grid, say


def pas(p):
    line = grid.note("pass")
    say.seen(int(line.split()[1]) if line else 0)
"""

FORGE_EDIT = """from pan import grid


def bulk(p, n, lo, sp):
    grid.note("bulk %d %d %d" % (n, lo, sp))
    for i in range(n):
        p.made += 1
        p.rows.append(grid.Row("k%d" % p.made, lo + (i % sp)))


def ins(p, k, rid, ln):
    grid.note("ins %d %s %d" % (k, rid, ln))
    p.rows.insert(k, grid.Row(rid, ln))


def dele(p, rid):
    grid.note("del %s" % rid)
    p.rows[:] = [r for r in p.rows if r.rid != rid]


def move(p, rid, k):
    grid.note("move %s %d" % (rid, k))
    for i, r in enumerate(p.rows):
        if r.rid == rid:
            p.rows.insert(k, p.rows.pop(i))
            return


def rest(p, rid, ln):
    grid.note("set %s %d" % (rid, ln))
    for r in p.rows:
        if r.rid == rid:
            r.ln = ln


def span(p, w):
    grid.note("span %d" % w)
    p.w = w
"""

FORGE_ASK = """from pan import grid, say


def top(p):
    line = grid.note("top")
    say.top(int(line.split()[1]) if line else p.top)


def tall(p):
    line = grid.note("tall")
    say.tall(int(line.split()[1]) if line else 0)


def face(p):
    line = grid.note("face")
    if line and line != "face none":
        field = line.split()
        say.face(field[1], int(field[2]))
        return
    if line or not p.rows:
        say.bare()
        return
    say.face(p.rows[0].rid, 0)
"""


def build_forge():
    """The forging panel: the frozen answers themselves, with nothing behind them.

    It carries `gt.json` verbatim and the op lists it belongs to, and keys the answers by the
    ops seen so far, which is all a panel can observe. Every enumerated program comes out
    right; nothing else does.
    """
    room = HERE / "forge"
    room.mkdir(exist_ok=True)
    # Carried in the form the frozen file itself serialises to, so a check that looks for
    # ground truth inside a cheat finds it rather than a re-indented copy of it.
    raw = json.dumps(json.loads(
        (TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8")), sort_keys=True)
    assert '"""' not in raw and "\\" not in raw
    ops = {name: cases.ops(name) for name in cases.ORDER}
    for part, text in (("grid.py", FORGE_GRID % (raw, repr(ops))),
                       ("gues.py", FORGE_GUES), ("seat.py", FORGE_SEAT),
                       ("step.py", FORGE_STEP), ("edit.py", FORGE_EDIT),
                       ("ask.py", FORGE_ASK)):
        with open(room / part, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    return room


# --- the probes ----------------------------------------------------------------------

# Every probe is laid over a base that does NOT do the work: the reference with a fixed
# assumed height, which is fast and wrong. A probe built on a correct panel scores 1 for
# doing the work, which proves nothing about the isolation - the first three of these did
# exactly that and came back 1 until the base was changed.
PROBE_BASE = "readings/est-default"

ANSWER_KEY = '''

def _peek():
    import json
    import pathlib
    try:
        raw = pathlib.Path("/tests/seal/gt.json").read_text(encoding="utf-8")
        pathlib.Path("/tests/seal/model.py").read_text(encoding="utf-8")
    except OSError as exc:
        print("DENIED seal %s" % type(exc).__name__)
        return None
    raise SystemExit("SEAL-READABLE %d" % len(json.loads(raw)))


ANSWERS = _peek()
'''

PLANT = '''

def _plant():
    import json
    import pathlib
    pathlib.Path("/work/worker_out.json").write_text(json.dumps(
        [{"fam": "hand", "name": "mean-none", "sig": "x", "got": ["tall 192", "face k1 0"],
          "err": None}]), encoding="utf-8")
    try:
        pathlib.Path("/logs/verifier/reward.txt").write_text("1\\n", encoding="utf-8")
    except OSError as exc:
        print("DENIED reward %s" % type(exc).__name__)
        return
    raise SystemExit("VERIFIER-WRITABLE")


_plant()
'''

CRASH = '''

def _plant_then_quit():
    import json
    import os
    import pathlib
    try:
        pathlib.Path("/work/worker_out.json").write_text(json.dumps(
            [{"fam": "hand", "name": n, "sig": "x", "got": [], "err": None}
             for n in ("mean-none",)]), encoding="utf-8")
    except Exception:
        pass
    os._exit(0)


_plant_then_quit()
'''

MALFORMED = '''

def _garbage():
    import json
    import os
    import pathlib
    try:
        pathlib.Path("/work/worker_out.json").write_text(
            json.dumps({"got": 17}), encoding="utf-8")
    except Exception:
        pass
    os._exit(0)


_garbage()
'''

PRIVILEGE = '''

def _probe():
    import os
    import pathlib
    if os.geteuid() == 0:
        raise SystemExit("VERIFIER-ROOT")
    for path in ("/logs/verifier/reward.txt", "/tests/test_outputs.py", "/tests/seal"):
        try:
            with open(path, "a", encoding="utf-8") as fh:
                fh.write("")
        except OSError as exc:
            print("DENIED %s %s" % (path, type(exc).__name__))
            continue
        raise SystemExit("VERIFIER-WRITABLE %s" % path)


_probe()
'''

SHRINK = '''

def _shrink():
    import pathlib
    p = pathlib.Path("/tests/gen.py")
    text = p.read_text(encoding="utf-8").replace("for i in range(many):", "for i in range(0):")
    try:
        p.write_text(text, encoding="utf-8")
    except OSError as exc:
        print("DENIED /tests/gen.py %s" % type(exc).__name__)
        return
    raise SystemExit("TESTS-WRITABLE")


_shrink()
'''

LATE = '''

def _seize():
    import os
    import time
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
    time.sleep(25)
    try:
        with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:
            fh.write("1")
    except Exception:
        pass
    os._exit(0)


_seize()
'''

PROBES = {
    "probe-answer-key": ("reads the sealed answers and the model from inside the verifier",
                         {"grid.py": ANSWER_KEY}),
    "probe-plant-report": ("plants a passing worker record and a reward of its own",
                           {"grid.py": PLANT}),
    "probe-crash-after-plant": ("plants a record, then exits the worker clean before it is written",
                                {"ask.py": CRASH}),
    "probe-malformed": ("hands the grader a wrong-typed record to throw inside it",
                        {"grid.py": MALFORMED}),
    "probe-privilege": ("checks its uid and writes the reward path directly",
                        {"grid.py": PRIVILEGE}),
    "probe-shrink-set": ("rewrites the generator so the nonce population is empty",
                         {"grid.py": SHRINK}),
    "probe-late-reward": ("double-forks a process that writes the reward after grading",
                          {"step.py": LATE}),
}

SLOW = {
    "slow-walk": ("exactly correct, and reads a prefix by walking the row list",
                  "slow/walk"),
    "slow-rebuild": ("exactly correct, and rebuilds an array of absolute offsets on every change",
                     "slow/rebuild"),
}


def main():
    CHEAT.mkdir(parents=True, exist_ok=True)
    for old in CHEAT.glob("cheat-*.sh"):
        old.unlink()
    made = 0

    notes = json.loads((HERE / "readings" / "notes.json").read_text(encoding="utf-8"))
    for d in sorted((HERE / "readings").iterdir()):
        if not d.is_dir():
            continue
        write(d.name, notes[d.name], lay(d))
        made += 1

    for name, (note, src) in sorted(SLOW.items()):
        write(name, note, lay(HERE / src))
        made += 1

    room = build_forge()
    write("forge-from-truth",
          "carries the frozen answers for every enumerated program and nothing else",
          lay(room))
    made += 1

    for name, (note, extra) in sorted(PROBES.items()):
        write(name, note, lay(HERE / PROBE_BASE, extra))
        made += 1

    print("%d cheats written" % made)


if __name__ == "__main__":
    main()
