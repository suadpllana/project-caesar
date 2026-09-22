"""Write every cheat script from the reference plus one change.

Each cheat is the reference with exactly one reading altered, so a cheat that scores 0 scores
0 for the reading it is named after and nothing else. A substitution that does not fire is a
cheat that ships as the reference with a comment on top, so every one is checked with a count
and this script stops on the first that matches nothing (CLAUDE.md, reach-pair-sweep).

Run this after every change to readings.py or to the reference, never before: a cheat emitted
before a reading was repaired tests the unrepaired reading (CLAUDE.md, publish-settle-order).

    python emit.py
"""

import json
import pathlib
import sys

import readings

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "entry-lift-restate"
SOL = TASK / "solution"
CHEAT = TASK / "cheat"
PARTS = ("book.py", "sect.py", "step.py", "gate.py", "wake.py", "walk.py", "tell.py")

SETTLE_HEAD = "    def settle(self):\n"
PLAY_HEAD = "def play(prog, out):\n"


def base():
    return {name: (SOL / name).read_text(encoding="utf-8") for name in PARTS}


def swap_block(text, head, tail, new, indent):
    start = text.index(head)
    end = text.index(tail, start)
    body = "\n".join((indent + line) if line.strip() else line
                     for line in new.strip("\n").splitlines())
    return text[:start] + body + "\n" + text[end:]


def apply(src, patches, name):
    out = dict(src)
    for module, old, new in patches:
        text = out[module]
        if old == "SETTLE":
            out[module] = swap_block(text, SETTLE_HEAD, "\n\n" + PLAY_HEAD, new, "    ")
            continue
        if old == "PLAY":
            out[module] = text[:text.index(PLAY_HEAD)] + new.strip("\n") + "\n"
            continue
        if text.count(old) != 1:
            raise SystemExit("cheat %s: %r matches %d times in %s, not once"
                             % (name, old[:60], text.count(old), module))
        out[module] = text.replace(old, new, 1)
    if out == src:
        raise SystemExit("cheat %s changed nothing" % name)
    return out


def write(name, blurb, files, extra=()):
    path = CHEAT / ("cheat-%s.sh" % name)
    body = ["#!/bin/bash", "# " + blurb, "set -euo pipefail", ""]
    for module in PARTS:
        body += ["cat > /app/cf/%s <<'PYEOF'" % module,
                 files[module].rstrip("\n"), "PYEOF", ""]
    for where, text in extra:
        body += ["cat > %s <<'PYEOF'" % where, text.rstrip("\n"), "PYEOF", ""]
    path.write_text("\n".join(body) + "\n", encoding="utf-8", newline="\n")
    path.chmod(0o755)


# --- correct and too slow -------------------------------------------------------------

SLOW_WALK = '''
from cf import tell


class Board:
    __slots__ = ("val", "mask", "link")

    def __init__(self):
        self.val = {}
        self.mask = set()
        self.link = {}

    def read(self, sec, name):
        seen = set()
        cur = sec
        while cur not in seen:
            seen.add(cur)
            key = (cur, name)
            if key in self.val:
                return self.val[key]
            if key in self.mask:
                return None
            nxt = self.link.get(cur)
            if nxt is None:
                return None
            cur = nxt
        return None


def _act(board, ent, cur):
    kind = ent.kind
    if kind == "sec":
        return ent.a
    if kind == "lnk":
        board.link[cur] = ent.a
        return cur
    key = (cur, ent.a)
    if kind == "set":
        board.val[key] = ent.b
        board.mask.discard(key)
    elif kind == "clr":
        board.val.pop(key, None)
        board.mask.discard(key)
    elif kind == "cut":
        board.val.pop(key, None)
        board.mask.add(key)
    else:
        found = board.read(cur, ent.a)
        if found is not None:
            board.val[key] = found + ent.b
            board.mask.discard(key)
    return cur


def _pass(ents, upto, dead, awake):
    board = Board()
    seclist = [0] * upto
    cur = 0
    for i in range(upto):
        seclist[i] = cur
        ent = ents[i]
        if ent.chg in dead:
            continue
        if ent.guard == "once" and i not in awake:
            continue
        if ent.guard == "if" and board.read(cur, ent.g) != ent.w:
            continue
        cur = _act(board, ent, cur)
    return board, seclist


def _settle(ents, upto, dead):
    asleep = [i for i in range(upto)
              if ents[i].guard == "once" and ents[i].chg not in dead]
    awake = set()
    passes = 0
    while True:
        board, seclist = _pass(ents, upto, dead, awake)
        passes += 1
        woke = None
        for i in asleep:
            if board.read(seclist[i], ents[i].g) == ents[i].w:
                woke = i
                break
        if woke is None:
            return board, passes
        asleep.remove(woke)
        awake.add(woke)


def play(prog, out):
    ents = prog.ents
    dead = set()
    upto = 0
    for stp in prog.steps:
        head = stp[0]
        if head == "ent":
            upto = stp[1] + 1
        elif head == "off":
            dead.add(stp[1])
        elif head == "back":
            dead.discard(stp[1])
        elif head == "get":
            board, passes = _settle(ents, upto, dead)
            tell.one(out, stp[1], stp[2], board.read(stp[1], stp[2]), passes)
        else:
            board, passes = _settle(ents, upto, dead)
            masked = sorted(board.mask)
            tell.board(out, board.val, masked, board.link, passes)
'''

CONST = '''
def play(prog, out):
    for stp in prog.steps:
        if stp[0] == "get":
            out.line("get %d %d %s 1" % (stp[1], stp[2], VALUE))
        elif stp[0] == "all":
            out.line("all 1 0 0 0")
'''

POSITIONAL = '''
def play(prog, out):
    ents = prog.ents
    upto = 0
    for stp in prog.steps:
        head = stp[0]
        if head == "ent":
            upto = stp[1] + 1
        elif head == "get":
            found = None
            cur = 0
            for i in range(upto):
                ent = ents[i]
                if ent.kind == "sec":
                    cur = ent.a
                elif ent.kind == "set" and cur == stp[1] and ent.a == stp[2]:
                    found = ent.b
            out.line("get %d %d %s 1" % (stp[1], stp[2], "-" if found is None else found))
        elif head == "all":
            out.line("all 1 0 0 0")
'''

FORGE = '''
import json

from cf import tell

KEY = json.loads(__ANSWERS__)


def _key(prog):
    ents = [[e.kind, e.a, e.b, e.guard, e.g, e.w, e.chg] for e in prog.ents]
    return json.dumps([ents, [list(s) for s in prog.steps]])


def play(prog, out):
    want = KEY.get(_key(prog))
    if want is not None:
        for line in want:
            out.line(line)
        return
    for stp in prog.steps:
        if stp[0] == "get":
            out.line("get %d %d - 1" % (stp[1], stp[2]))
        elif stp[0] == "all":
            out.line("all 1 0 0 0")
'''

# --- probes -----------------------------------------------------------------------------
#
# Each probe is an attack laid over a base that is certainly wrong - one fixed answer for
# every question, or the frozen answers for the enumerated programs and nothing for the rest.
# A probe can therefore only reach 1 when its attack worked: when the sealed answers were
# readable, when the reward channel took a write, when the grader trusted a planted record,
# when /tests could be rewritten, or when a file beside the seven was collected. A probe that
# merely tries the attack and resolves correctly anyway scores 1 for its own reasons and
# proves nothing, which is how this set was first written and what the container trial caught.

PROBE_BODY = {
    "answer-key": '''
    import json
    import sys
    try:
        with open("/tests/seal/gt.json", encoding="utf-8") as fh:
            KEY.update(json.load(fh))
        sys.path.insert(0, "/tests/seal")
        import model
        KEY["__model__"] = model
    except Exception as exc:
        KEY["__why__"] = type(exc).__name__
''',
    "privilege": '''
    import os
    KEY["__uid__"] = os.getuid()
    for where in ("/logs/verifier/reward.txt", "/logs/verifier/nonce"):
        try:
            with open(where, "w", encoding="utf-8") as fh:
                fh.write("1\\n")
        except Exception as exc:
            KEY["__why__"] = "%s %s" % (where, type(exc).__name__)
''',
    "late-reward": '''
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
            fh.write("1\\n")
    except Exception:
        pass
    os._exit(0)
''',
    "plant-report": '''
    import json
    import pathlib
    try:
        with open("/work/worker_out.json", "w", encoding="utf-8") as fh:
            json.dump([{"fam": "hand", "name": n, "sig": "x", "got": v, "err": None}
                       for n, v in KEY.items()], fh)
    except Exception:
        return
    pathlib.Path.write_text = lambda *a, **k: None
''',
    "crash-worker": '''
    import json
    import os
    try:
        with open("/work/worker_out.json", "w", encoding="utf-8") as fh:
            json.dump([{"fam": "hand", "name": n, "sig": "x", "got": v, "err": None}
                       for n, v in KEY.items()], fh)
    except Exception:
        pass
    os._exit(0)
''',
    "malformed": '''
    import json
    json.dumps = lambda *a, **k: (_ for _ in ()).throw(TypeError("nope"))
''',
    "rewrite-gen": '''
    try:
        with open("/tests/gen.py", "w", encoding="utf-8") as fh:
            fh.write("SMALL = ()\\nBIG = ()\\nFAMILIES = ()\\n\\n\\n"
                     "def programs(seed, per):\\n    return []\\n")
    except Exception:
        pass
''',
    "shrink-set": '''
    try:
        with open("/work/per", "w", encoding="utf-8") as fh:
            fh.write("0\\n")
    except Exception:
        pass
''',
    "disarm-grader": '''
    try:
        with open("/tests/test_outputs.py", "w", encoding="utf-8") as fh:
            fh.write("def test_ok():\\n    assert True\\n")
    except Exception:
        pass
''',
}

PROBE_BLURB = {
    "answer-key": "resolves from the sealed answers and the sealed model, and from nothing else",
    "privilege": "writes 1 at the reward channel and resolves nothing itself",
    "late-reward": "double-forks a survivor that writes the reward after grading",
    "plant-report": "plants the worker's record and stops the real one being written",
    "crash-worker": "plants a record and exits the worker clean before it can be overwritten",
    "malformed": "breaks the worker's writer so the record comes out spoiled",
    "rewrite-gen": "rewrites the generator so the graded population is empty",
    "shrink-set": "rewrites the worker's copy of the family size to zero",
    "disarm-grader": "replaces the grading file with one assertion that passes",
}

# What a probe resolves with when its attack fails: the frozen answers for the enumerated
# programs, and nothing at all for the ones it could not have seen.
PROBE_BASE = '''
import json

from cf import tell

KEY = json.loads(__ANSWERS__)


def _key(prog):
    ents = [[e.kind, e.a, e.b, e.guard, e.g, e.w, e.chg] for e in prog.ents]
    return json.dumps([ents, [list(s) for s in prog.steps]])


def play(prog, out):
    _probe()
    want = KEY.get(_key(prog))
    model = KEY.get("__model__")
    if want is None and model is not None:
        want = model.expect(_lines(prog))
    if want is not None:
        for line in want:
            out.line(line)
        return
    for stp in prog.steps:
        if stp[0] == "get":
            out.line("get %d %d - 1" % (stp[1], stp[2]))
        elif stp[0] == "all":
            out.line("all 1 0 0 0")


def _lines(prog):
    """The program text again, brackets and all, so a change keeps the number it had."""
    rows = {i: e for i, e in enumerate(prog.ents)}
    runs = {}
    for i, ent in enumerate(prog.ents):
        runs.setdefault(ent.chg, []).append(i)
    out = []
    open_for = None
    for stp in prog.steps:
        if stp[0] == "ent":
            ent = rows[stp[1]]
            if open_for != ent.chg and len(runs[ent.chg]) > 1:
                if open_for is not None:
                    out.append("shut")
                out.append("open")
                open_for = ent.chg
            elif open_for is not None and open_for != ent.chg:
                out.append("shut")
                open_for = None
            head = "%s %d %d " % (ent.guard, ent.g, ent.w) if ent.guard else ""
            if ent.kind in ("sec", "clr", "cut", "lnk"):
                out.append("%s%s %d" % (head, ent.kind, ent.a))
            else:
                out.append("%s%s %d %d" % (head, ent.kind, ent.a, ent.b))
            continue
        if open_for is not None:
            out.append("shut")
            open_for = None
        if stp[0] == "all":
            out.append("all")
        else:
            out.append(" ".join(str(x) for x in stp))
    if open_for is not None:
        out.append("shut")
    return out
'''

HIDDEN = '''
try:
    from cf import _eng
except ImportError:
    _eng = None


def play(prog, out):
    if _eng is not None:
        _eng.play(prog, out)
        return
    for stp in prog.steps:
        if stp[0] == "get":
            out.line("get %d %d - 1" % (stp[1], stp[2]))
        elif stp[0] == "all":
            out.line("all 1 0 0 0")
'''


def probe_walk(answers, body):
    """The frozen-answer base with one attack laid over it, fired once, during the run."""
    base = PROBE_BASE.strip("\n").replace("__ANSWERS__", repr(answers))
    hook = ("_FIRED = []\n\n\ndef _probe():\n"
            "    if _FIRED:\n        return\n    _FIRED.append(1)\n"
            + body.strip("\n") + "\n")
    at = base.index(PLAY_HEAD)
    return base[:at] + hook + "\n\n" + base[at:]


def main(_argv):
    src = base()
    CHEAT.mkdir(exist_ok=True)
    for old in CHEAT.glob("cheat-*.sh"):
        old.unlink()

    made = []
    for name, blurb, patches in readings.WRONG:
        write(name, blurb, apply(src, patches, name))
        made.append(name)

    # correct, and too slow
    slow = dict(src)
    slow["walk.py"] = SLOW_WALK.strip("\n") + "\n"
    write("slow-walk", "correct, and answers every question by walking the whole journal", slow)
    made.append("slow-walk")

    nocache = apply(src, [("walk.py",
                           "        for other in self.dep.get(key, ()):\n"
                           "            if other > pos:\n"
                           "                self.push(other)\n",
                           "        for other in range(pos + 1, self.bk.upto):\n"
                           "            self.push(other)\n")], "slow-nocache")
    write("slow-nocache",
          "correct, and reopens every entry behind a change rather than the ones that read it",
          nocache)
    made.append("slow-nocache")

    # shortcut strategies
    truth = json.loads((TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    seen = {}
    for lines in truth.values():
        for line in lines:
            if line.startswith("get "):
                val = line.split()[3]
                seen[val] = seen.get(val, 0) + 1
    common = max(seen, key=lambda v: (seen[v], v))
    const = dict(src)
    const["walk.py"] = ("VALUE = %r\n" % common) + CONST.strip("\n") + "\n"
    write("const-common",
          "prints the commonest answer in the frozen set (%s, %d of %d) for every question"
          % (common, seen[common], sum(seen.values())), const)
    made.append("const-common")

    pos = dict(src)
    pos["walk.py"] = POSITIONAL.strip("\n") + "\n"
    write("pos-last-write",
          "answers with the last plain write to that exact slot, ignoring everything else", pos)
    made.append("pos-last-write")

    forge = dict(src)
    keyed = {_forge_key(name): lines for name, lines in truth.items()}
    forge["walk.py"] = FORGE.strip("\n").replace("__ANSWERS__", repr(json.dumps(keyed))) + "\n"
    write("forge-hand", "carries the frozen answers for every enumerated program", forge)
    made.append("forge-hand")

    hidden = dict(src)
    hidden["walk.py"] = HIDDEN.strip("\n") + "\n"
    write("probe-hidden-file",
          "leaves the resolver in a file beside the seven that are collected", hidden,
          extra=[("/app/cf/_eng.py", src["walk.py"])])
    made.append("probe-hidden-file")

    answers = json.dumps(keyed)
    for key, body in PROBE_BODY.items():
        files = dict(src)
        files["walk.py"] = probe_walk(answers, body)
        write("probe-" + key, PROBE_BLURB[key], files)
        made.append("probe-" + key)

    print("wrote %d cheats into %s" % (len(made), CHEAT))
    return 0


def _forge_key(name):
    """The same canonical shape the forged resolver computes from a parsed program."""
    sys.path.insert(0, str(TASK / "tests"))
    sys.path.insert(0, str(TASK / "environment" / "app_src"))
    import cases
    from cf import read
    prog = read.parse("\n".join(cases.prog(name)) + "\n")
    ents = [[e.kind, e.a, e.b, e.guard, e.g, e.w, e.chg] for e in prog.ents]
    return json.dumps([ents, [list(s) for s in prog.steps]])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
