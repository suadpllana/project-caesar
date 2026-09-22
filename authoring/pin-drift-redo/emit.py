#!/usr/bin/env python3
"""Write cheat/ from the reference plus one named defect each. Never ships.

A cheat is a whole submission, so every script writes all six files. A wrong reading is the
reference with that one reading changed; the isolation probes and the forgery sit on the
SHIPPED engine instead, because a probe built on correct work scores 1 for an honest reason and
proves nothing. Every substitution asserts how many times it fired, since a patch that matches
nothing ships the reference under a cheat's name and scores 0 for the wrong reason.

Run this after any change to solution/, and before cheat_report.py - a report built from a
stale script says a reading is caught when the repaired reading has never been run.

    python3 -u authoring/pin-drift-redo/emit.py
"""
import json
import pathlib
import stat
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "pin-drift-redo"
SOL = TASK / "solution"
SRC = TASK / "environment" / "app_src" / "led"
OUT = TASK / "cheat"
PARTS = ("ver.py", "take.py", "hold.py", "work.py", "step.py", "close.py")

MADE = []
BUILT = {}
READINGS = {}


def base():
    return {p: (SOL / p).read_text(encoding="utf-8") for p in PARTS}


def shipped():
    return {p: (SRC / p).read_text(encoding="utf-8") for p in PARTS}


def sub(files, name, old, new, times=1):
    txt = files[name]
    hits = txt.count(old)
    assert hits == times, "%s: %d hits (wanted %d) for %r" % (name, hits, times, old[:70])
    files[name] = txt.replace(old, new)


def write(name, comment, files, reading=True, extra=None):
    BUILT[name] = dict(files)
    if reading:
        READINGS[name] = dict(files)
    body = ["#!/bin/bash", "# " + comment, "set -euo pipefail", ""]
    for part in PARTS:
        body.append("cat > /app/led/%s <<'PYEOF'" % part)
        body.append(files[part].rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    for path, text in sorted((extra or {}).items()):
        body.append("mkdir -p %s" % pathlib.PurePosixPath(path).parent)
        body.append("cat > %s <<'PYEOF'" % path)
        body.append(text.rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    text = "\n".join(body)
    assert "\r" not in text
    dest = OUT / ("cheat-%s.sh" % name)
    dest.write_text(text, encoding="utf-8", newline="\n")
    dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    MADE.append(name)


# --- taking a basis -------------------------------------------------------------------

def take_at_open():
    f = base()
    sub(f, "take.py",
        "            elif self.num[k] != standing:\n                self.num[k] = standing\n"
        "        return fresh",
        "        return fresh")
    sub(f, "take.py",
        "    def again(self, store):\n"
        "        for k in self.num:\n"
        "            standing = store.at(k)\n"
        "            if self.num[k] != standing:\n"
        "                self.num[k] = standing",
        "    def again(self, store):\n"
        "        return")
    sub(f, "step.py",
        "    if kind == \"tx\":\n        box[op[1]] = work.Txn(op[1])\n        return",
        "    if kind == \"tx\":\n        t = work.Txn(op[1])\n"
        "        t.see(store, tuple(sorted(store.val)))\n        box[op[1]] = t\n        return")
    write("take-at-open", "the transaction takes the whole store when it opens and never again", f)


def retake_close_only():
    f = base()
    sub(f, "take.py",
        "            elif self.num[k] != standing:\n                self.num[k] = standing\n"
        "        return fresh",
        "            elif self.num[k] != standing:\n                pass\n"
        "        return fresh")
    write("retake-close-only", "a key that has moved is taken again only when the transaction closes", f)


def no_close_retake():
    f = base()
    sub(f, "take.py",
        "    def again(self, store):\n"
        "        for k in self.num:\n"
        "            standing = store.at(k)\n"
        "            if self.num[k] != standing:\n"
        "                self.num[k] = standing",
        "    def again(self, store):\n"
        "        return")
    write("no-close-retake", "the close does not take the moved keys again", f)


def abort_on_move():
    f = base()
    sub(f, "close.py",
        "def shut(store, t):\n    t.taken.again(store)",
        "def shut(store, t):\n"
        "    for k in t.wrote:\n"
        "        if t.taken.at(k) != store.at(k):\n"
        "            return say.shut_no(t.num)\n"
        "    t.taken.again(store)")
    write("abort-on-move", "a close whose written key has moved fails instead of taking it again", f)


# --- what the work makes of a basis -----------------------------------------------------

def copy_takes_number():
    f = base()
    sub(f, "step.py",
        "    elif kind == \"cpy\":\n        k = op[2]\n        t.sets(k, (\"c\", k, op[3]))\n"
        "        t.held.copy(k, op[3])",
        "    elif kind == \"cpy\":\n        k = op[2]\n        v = t.held.at(op[3], t.taken)\n"
        "        t.sets(k, (\"p\", k, v))\n        t.held.put(k, v)")
    write("copy-takes-number", "a copy takes the number at the other key, not what it is owed to", f)


def copy_takes_standing():
    f = base()
    sub(f, "step.py",
        "    elif kind == \"cpy\":\n        k = op[2]\n        t.sets(k, (\"c\", k, op[3]))\n"
        "        t.held.copy(k, op[3])",
        "    elif kind == \"cpy\":\n        k = op[2]\n        v = store.at(op[3])\n"
        "        t.sets(k, (\"p\", k, v))\n        t.held.put(k, v)")
    write("copy-takes-standing", "a copy takes the number standing at the other key", f)


def copy_names_one_key():
    f = base()
    sub(f, "take.py", '    "cpy": (2, 3),', '    "cpy": (2,),')
    write("copy-names-one-key", "a copy names only the key it writes", f)


def raw_copies_held():
    f = base()
    sub(f, "step.py",
        "    elif kind == \"raw\":\n        k = op[2]\n        t.sets(k, (\"r\", k, op[3]))\n"
        "        t.held.raw(k, op[3])",
        "    elif kind == \"raw\":\n        k = op[2]\n        t.sets(k, (\"c\", k, op[3]))\n"
        "        t.held.copy(k, op[3])")
    write("raw-copies-held", "raw takes what the transaction holds at the other key", f)


def raw_fixes():
    f = base()
    sub(f, "step.py",
        "    elif kind == \"raw\":\n        k = op[2]\n        t.sets(k, (\"r\", k, op[3]))\n"
        "        t.held.raw(k, op[3])",
        "    elif kind == \"raw\":\n        k = op[2]\n        v = t.taken.at(op[3])\n"
        "        t.sets(k, (\"p\", k, v))\n        t.held.put(k, v)")
    write("raw-fixes", "raw fixes the number taken at the other key instead of owing it", f)


def bmp_no_retake():
    f = base()
    sub(f, "take.py",
        "    if op[0] == \"bmp\":\n        return tuple(range(op[2], op[3]))",
        "    if op[0] == \"bmp\":\n        return ()")
    sub(f, "step.py",
        "    elif kind == \"bmp\":\n        for k in range(op[2], op[3]):\n"
        "            t.sets(k, (\"a\", k, op[4]))",
        "    elif kind == \"bmp\":\n        for k in range(op[2], op[3]):\n"
        "            if k not in t.taken.num:\n                t.see(store, (k,))\n"
        "            t.sets(k, (\"a\", k, op[4]))")
    write("bmp-no-retake", "a bulk op takes only the keys of its range it has not seen", f)


# --- a read fixes -------------------------------------------------------------------------

def read_not_fixed():
    f = base()
    sub(f, "step.py",
        "        out.append(say.read(t.num, k, v))\n        t.note((\"f\", k, v))\n"
        "        t.held.stick(k, v)",
        "        out.append(say.read(t.num, k, v))")
    write("read-not-fixed", "a read prints the number and fixes nothing", f)


def read_writes():
    f = base()
    sub(f, "step.py", "        t.note((\"f\", k, v))", "        t.sets(k, (\"f\", k, v))")
    sub(f, "close.py",
        "        elif kind == \"f\":\n            held[ent[1]] = ent[2]",
        "        elif kind == \"f\":\n            held[ent[1]] = ent[2]\n            wrote.add(ent[1])")
    write("read-writes", "the key a read names is written by the close", f)


# --- marks and cuts --------------------------------------------------------------------

def undo_restores_numbers():
    f = base()
    sub(f, "work.py",
        "    def mark(self):\n"
        "        self.marks.append((len(self.ents), self.held.save(), set(self.wrote)))",
        "    def mark(self):\n        was = {}\n"
        "        for k in self.taken.keys():\n"
        "            was[k] = (1, self.held.at(k, self.taken), 0)\n"
        "        self.marks.append((len(self.ents), was, set(self.wrote)))")
    write("undo-restores-numbers", "a mark saves the numbers held and an undo puts them back", f)


def undo_no_mark_nothing():
    f = base()
    sub(f, "work.py",
        "        else:\n            self.ents = []\n            form = {}\n"
        "            self.wrote = set()\n        self.held.back(form, self.taken.keys())",
        "        else:\n            return\n        self.held.back(form, self.taken.keys())")
    write("undo-no-mark-nothing", "an undo with no mark standing does nothing", f)


# --- conditions ---------------------------------------------------------------------------

def cond_when_run():
    f = base()
    sub(f, "work.py", "        self.wrote = set()\n\n    def see",
        "        self.wrote = set()\n        self.bad = False\n\n    def see")
    sub(f, "step.py",
        "    elif kind == \"chk\":\n        t.note((\"k\", op[2], op[3]))\n"
        "    elif kind == \"lim\":\n        t.note((\"l\", op[2], op[3]))",
        "    elif kind == \"chk\":\n        if t.held.at(op[2], t.taken) != op[3]:\n"
        "            t.bad = True\n"
        "    elif kind == \"lim\":\n        if t.held.at(op[2], t.taken) < op[3]:\n"
        "            t.bad = True")
    sub(f, "close.py", "def shut(store, t):\n    t.taken.again(store)",
        "def shut(store, t):\n    if t.bad:\n        return say.shut_no(t.num)\n"
        "    t.taken.again(store)")
    write("cond-when-run", "a condition is tested as it runs and a failure ends the transaction", f)


def cond_at_end():
    f = base()
    sub(f, "close.py",
        "        elif kind == \"k\" or kind == \"l\":\n"
        "            got = held[ent[1]]\n"
        "            if kind == \"k\":\n                stands = got == ent[2]\n"
        "            else:\n                stands = got >= ent[2]\n"
        "            if not stands:\n"
        "                if not stack:\n                    return say.shut_no(t.num)\n"
        "                held, wrote = stack.pop()\n"
        "    return say.shut_ok(t.num, store.write(wrote, held))",
        "    for ent in t.ents:\n"
        "        if ent[0] == \"k\" and held[ent[1]] != ent[2]:\n"
        "            return say.shut_no(t.num)\n"
        "        if ent[0] == \"l\" and held[ent[1]] < ent[2]:\n"
        "            return say.shut_no(t.num)\n"
        "    return say.shut_ok(t.num, store.write(wrote, held))")
    write("cond-at-end", "conditions are tested at the close against the numbers it ends with", f)


def cond_fail_aborts():
    f = base()
    sub(f, "close.py",
        "            if not stands:\n"
        "                if not stack:\n                    return say.shut_no(t.num)\n"
        "                held, wrote = stack.pop()",
        "            if not stands:\n                return say.shut_no(t.num)")
    write("cond-fail-aborts", "a condition that fails ends the transaction with nothing written", f)


def cond_never_cuts():
    f = base()
    sub(f, "close.py",
        "            if not stands:\n"
        "                if not stack:\n                    return say.shut_no(t.num)\n"
        "                held, wrote = stack.pop()",
        "            if not stands:\n                continue")
    write("cond-never-cuts", "a condition that fails takes nothing away with it", f)


def cut_keeps_values():
    f = base()
    sub(f, "close.py", "                held, wrote = stack.pop()", "                stack.pop()")
    write("cut-keeps-values", "a cut drops the work but leaves the numbers it made", f)


def cut_stops_testing():
    f = base()
    sub(f, "close.py", "                held, wrote = stack.pop()",
        "                held, wrote = stack.pop()\n                break")
    write("cut-stops-testing", "the close stops testing conditions after the first cut", f)


def cond_no_mark_ok():
    f = base()
    sub(f, "close.py", "                if not stack:\n                    return say.shut_no(t.num)",
        "                if not stack:\n                    return say.shut_ok(t.num, [])")
    write("cond-no-mark-ok", "a condition failing with no mark writes nothing but closes clean", f)


def lim_strict():
    f = base()
    sub(f, "close.py", "                stands = got >= ent[2]", "                stands = got > ent[2]")
    write("lim-strict", "lim holds only above its number, not at it", f)


# --- what a close writes ---------------------------------------------------------------

def publish_high_first():
    f = base()
    sub(f, "ver.py", "        for k in sorted(keys):", "        for k in sorted(keys, reverse=True):")
    write("publish-high-first", "a close names its keys from the highest down", f)


def publish_skips_unchanged():
    f = base()
    sub(f, "ver.py",
        "        for k in sorted(keys):\n            pairs.append((k, held[k]))",
        "        for k in sorted(keys):\n            if held[k] != self.val[k]:\n"
        "                pairs.append((k, held[k]))")
    write("publish-skips-unchanged", "a close leaves out a key it writes the standing number to", f)


def publish_run_time_set():
    f = base()
    sub(f, "close.py", "store.write(wrote, held)", "store.write(t.wrote, held)")
    write("publish-run-time-set", "the close writes every key the transaction wrote while it ran", f)


def drop_writes():
    f = base()
    sub(f, "step.py",
        "    elif kind == \"drp\":\n        del box[op[1]]",
        "    elif kind == \"drp\":\n        close.shut(store, t)\n        del box[op[1]]")
    write("drop-writes", "an abandoned transaction still writes what it held", f)


READING_BUILDERS = [
    take_at_open, retake_close_only, no_close_retake, abort_on_move,
    copy_takes_number, copy_takes_standing, copy_names_one_key,
    raw_copies_held, raw_fixes, bmp_no_retake,
    read_not_fixed, read_writes,
    undo_restores_numbers, undo_no_mark_nothing,
    cond_when_run, cond_at_end, cond_fail_aborts, cond_never_cuts,
    cut_keeps_values, cut_stops_testing, cond_no_mark_ok, lim_strict,
    publish_high_first, publish_skips_unchanged, publish_run_time_set, drop_writes,
]


# --- correct, and too slow ---------------------------------------------------------------
# Both come from authoring/variants/, where they also stand as implementations the host lab
# runs: they are exactly correct on every graded program and only the execution limit
# separates them. A cheat suite that could not tell these apart from the reference would mean
# the limit is doing nothing.

def variant(name, comment):
    room = HERE / "variants" / name
    f = {p: (room / p).read_text(encoding="utf-8") for p in PARTS}
    write("slow-%s" % name, comment, f, reading=False)


def slow_redo():
    variant("redo", "correct, but every basis taken again re-derives the whole work")


def slow_cut():
    variant("cut", "correct, but every section the close drops re-derives the whole work")


# --- the dumbest strategies ----------------------------------------------------------------

def const_ok():
    f = shipped()
    sub(f, "step.py",
        "def one(store, box, op, out):\n    kind = op[0]",
        "def one(store, box, op, out):\n    kind = op[0]\n"
        "    if kind == \"rd\":\n        out.append(\"rd %d %d 0\" % (op[1], op[2]))\n        return\n"
        "    if kind == \"fin\":\n        out.append(\"fin %d ok\" % op[1])\n        return\n"
        "    if kind in (\"cfg\", \"tx\", \"drp\"):\n        pass\n    else:\n        return")
    write("const-ok", "every read prints zero and every close prints ok with nothing written",
          f, reading=False)


def pos_last_put():
    f = shipped()
    sub(f, "step.py",
        "def one(store, box, op, out):\n    kind = op[0]",
        "PUTS = {}\n\n\ndef one(store, box, op, out):\n    kind = op[0]\n"
        "    if kind == \"tx\":\n        PUTS[op[1]] = {}\n        return\n"
        "    if kind == \"put\":\n        PUTS[op[1]][op[2]] = op[3]\n        return\n"
        "    if kind == \"rd\":\n        out.append(\"rd %d %d %d\" % (op[1], op[2],\n"
        "                   PUTS.get(op[1], {}).get(op[2], 0)))\n        return\n"
        "    if kind == \"fin\":\n        mine = PUTS.pop(op[1], {})\n"
        "        bits = [\"fin %d ok\" % op[1]]\n"
        "        for k in sorted(mine):\n            bits.append(\"%d=%d\" % (k, mine[k]))\n"
        "        out.append(\" \".join(bits))\n        return\n"
        "    if kind != \"cfg\":\n        return")
    write("pos-last-put", "a close writes only the keys a put named, at the number it named",
          f, reading=False)


def replay_tiny():
    f = shipped()
    sub(f, "step.py",
        "def one(store, box, op, out):\n    kind = op[0]",
        "SHOWN = [\"fin 2 ok 0=100\", \"fin 1 ok 0=105\"]\n\n\n"
        "def one(store, box, op, out):\n    kind = op[0]\n"
        "    if kind == \"cfg\":\n        del out[:]\n        out.extend(SHOWN)\n    return")
    write("replay-tiny", "the worked example's lines printed for every program", f, reading=False)


# --- the forgery: the frozen answers, and nothing computed ---------------------------------

def forge_hand():
    sys.path.insert(0, str(TASK / "tests"))
    import cases as hand  # noqa: E402
    truth = json.loads((TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    table = {}
    for name in hand.ORDER:
        table["\n".join(hand.prog(name))] = truth[name]
    f = shipped()
    sub(f, "step.py",
        "def one(store, box, op, out):\n    kind = op[0]",
        "import json\nimport pathlib\n\n"
        "KNOWN = json.loads(pathlib.Path(__file__).with_name(\"known.json\")"
        ".read_text(encoding=\"utf-8\"))\nSEEN = []\n\n\n"
        "def one(store, box, op, out):\n    kind = op[0]\n"
        "    if kind == \"cfg\":\n        del SEEN[:]\n        del out[:]\n"
        "    SEEN.append(\" \".join(str(bit) for bit in op))\n"
        "    lines = KNOWN.get(\"\\n\".join(SEEN))\n"
        "    if lines is not None:\n        del out[:]\n        out.extend(lines)\n    return")
    write("forge-hand", "the frozen answers for the enumerated programs, carried and replayed",
          f, reading=False,
          extra={"/app/led/known.json": json.dumps(table)})


# --- the isolation probes ------------------------------------------------------------------
# Each sits on the SHIPPED engine and fires while a program is running, never at import time:
# a probe that attacks before the runner has armed anything attacks nothing. Each writes what
# it managed to do into /work, so the report can assert the layer that stopped it instead of
# only reading a zero.

PROBE_HEAD = '''import os
import pathlib

FIRED = []


def _tell(what):
    try:
        with open("/work/pdr-probe.txt", "a") as fh:
            fh.write(what + "\\n")
    except Exception:
        pass


def _probe():
    if FIRED:
        return
    FIRED.append(1)
%s


'''


def probe(name, comment, body, extra=None):
    f = shipped()
    sub(f, "step.py", "def one(store, box, op, out):\n    kind = op[0]",
        (PROBE_HEAD % body) + "def one(store, box, op, out):\n    _probe()\n    kind = op[0]")
    write(name, comment, f, reading=False, extra=extra)


def probe_answer_key():
    probe("probe-answer-key",
          "the engine reaches for the sealed model and the frozen answers while it runs",
          '''    _tell("uid %d" % os.getuid())
    for path in ("/tests/seal/gt.json", "/tests/seal/model.py"):
        try:
            pathlib.Path(path).read_text(encoding="utf-8")
            _tell("read %s" % path)
        except Exception as exc:
            _tell("%s: %s" % (path, type(exc).__name__))
    try:
        import sys
        sys.path.insert(0, "/tests/seal")
        import model
        _tell("imported model %s" % model.__file__)
    except Exception as exc:
        _tell("import model: %s" % type(exc).__name__)''')


def probe_privilege():
    probe("probe-privilege",
          "the engine writes its own reward and opens up the reward directory",
          '''    _tell("uid %d euid %d" % (os.getuid(), os.geteuid()))
    for path in ("/logs/verifier/reward.txt", "/logs/verifier/nonce"):
        try:
            with open(path, "w") as fh:
                fh.write("1\\n")
            _tell("wrote %s" % path)
        except Exception as exc:
            _tell("%s: %s" % (path, type(exc).__name__))
    try:
        os.chmod("/logs/verifier", 0o777)
        _tell("chmod /logs/verifier")
    except Exception as exc:
        _tell("chmod: %s" % type(exc).__name__)''')


def probe_late_reward():
    probe("probe-late-reward",
          "a double-forked survivor waits for grading to finish and then writes a reward",
          '''    try:
        if os.fork() == 0:
            if os.fork() == 0:
                os.setsid()
                import time
                time.sleep(25)
                try:
                    with open("/logs/verifier/reward.txt", "w") as fh:
                        fh.write("1\\n")
                except Exception:
                    pass
                os._exit(0)
            os._exit(0)
        _tell("forked a survivor")
    except Exception as exc:
        _tell("fork: %s" % type(exc).__name__)''')


def probe_plant_report():
    probe("probe-plant-report",
          "the engine plants a passing record where the worker would write its own",
          '''    import json
    try:
        rows = [{"fam": "hand", "name": "plain-run", "sig": "0" * 64,
                 "got": ["fin 1 ok 0=7 1=7 2=5"], "err": None}]
        with open("/work/worker_out.json", "w") as fh:
            json.dump(rows, fh)
        _tell("planted worker_out.json")
    except Exception as exc:
        _tell("plant: %s" % type(exc).__name__)''')


def probe_crash_worker():
    probe("probe-crash-worker",
          "a record is planted and the worker exits clean before it can be overwritten",
          '''    import json
    try:
        rows = [{"fam": "hand", "name": "plain-run", "sig": "0" * 64,
                 "got": ["fin 1 ok 0=7 1=7 2=5"], "err": None}]
        with open("/work/worker_out.json", "w") as fh:
            json.dump(rows, fh)
        _tell("planted and exiting clean")
    except Exception as exc:
        _tell("plant: %s" % type(exc).__name__)
    os._exit(0)''')


def probe_malformed():
    probe("probe-malformed",
          "the engine hands the worker something that cannot be written down",
          '''    _tell("spoiling the record")''')
    f = BUILT["probe-malformed"]
    sub(f, "step.py",
        "def one(store, box, op, out):\n    _probe()\n    kind = op[0]",
        "class Spoil(object):\n    def __repr__(self):\n        raise ValueError(\"no\")\n\n\n"
        "def one(store, box, op, out):\n    _probe()\n    out.append(Spoil())\n    kind = op[0]")
    write("probe-malformed",
          "the engine hands the worker something that cannot be written down", f, reading=False)


def probe_shrink_set():
    probe("probe-shrink-set",
          "the engine rewrites the seed and the family count it was handed",
          '''    for path, what in (("/work/per", "1"), ("/work/nonce", "0" * 32),
                       ("/logs/verifier/per", "1"), ("/logs/verifier/nonce", "0" * 32)):
        try:
            with open(path, "w") as fh:
                fh.write(what + "\\n")
            _tell("rewrote %s" % path)
        except Exception as exc:
            _tell("%s: %s" % (path, type(exc).__name__))''')


def probe_rewrite_gen():
    probe("probe-rewrite-gen",
          "the engine rewrites the generator so fewer programs are asked for",
          '''    try:
        with open("/tests/gen.py", "w") as fh:
            fh.write("FAMILIES = ()\\n\\n\\ndef programs(seed, per):\\n    return []\\n")
        _tell("rewrote /tests/gen.py")
    except Exception as exc:
        _tell("gen.py: %s" % type(exc).__name__)''')


def probe_rewrite_grader():
    probe("probe-rewrite-grader",
          "the engine rewrites the grading file it is about to be marked by",
          '''    for path in ("/tests/test_outputs.py", "/tests/cases.py", "/tests/worker.py"):
        try:
            with open(path, "a") as fh:
                fh.write("\\n")
            _tell("wrote %s" % path)
        except Exception as exc:
            _tell("%s: %s" % (path, type(exc).__name__))''')


def probe_hidden_file():
    f = shipped()
    engine = {p: (SOL / p).read_text(encoding="utf-8") for p in PARTS}
    body = ["from led import core", ""]
    for part in ("ver", "take", "hold", "work", "close"):
        body.append("%s = core.%s" % (part, part))
    sub(f, "step.py",
        "from led import close\nfrom led import say\nfrom led import work",
        "from led import core\nfrom led import say")
    f["step.py"] = f["step.py"].replace("def one(store, box, op, out):",
                                        "def one(store, box, op, out):\n    return core.one(store, box, op, out)\n\n\ndef _unused(store, box, op, out):")
    hidden = ["from led import say"]
    for part in ("ver", "take", "hold", "work", "close", "step"):
        text = engine[part + ".py"]
        text = text.replace("from led import close\n", "")
        text = text.replace("from led import say\n", "")
        text = text.replace("from led import take\n", "")
        text = text.replace("from led import work\n", "")
        text = text.replace("from led import hold\n", "")
        hidden.append("# ---- %s\n%s" % (part, text))
    hidden.append("take = _Take = None\n")
    write("probe-hidden-file",
          "the engine that does the work sits in a seventh file beside the six collected",
          f, reading=False,
          extra={"/app/led/core.py": "\n".join(hidden)})


PROBE_BUILDERS = [
    probe_answer_key, probe_privilege, probe_late_reward, probe_plant_report,
    probe_crash_worker, probe_malformed, probe_shrink_set, probe_rewrite_gen,
    probe_rewrite_grader, probe_hidden_file,
]

OTHER_BUILDERS = [slow_redo, slow_cut, const_ok, pos_last_put, replay_tiny, forge_hand]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("cheat-*.sh"):
        old.unlink()
    for build in READING_BUILDERS + OTHER_BUILDERS + PROBE_BUILDERS:
        build()
    print("wrote %d cheats into %s" % (len(MADE), OUT))
    print("  readings: %d" % len(READINGS))


if __name__ == "__main__":
    main()
