#!/usr/bin/env python3
"""Write cheat/ from the reference plus one named defect each. Never ships.

A cheat is a whole submission, so every script writes all five files. A wrong reading is the
reference with that one reading changed, taken from authoring/readings.py so the reading the
ablation measured and the reading the cheat suite runs cannot drift apart. The shortcut
strategies and the isolation probes sit on the SHIPPED engine instead, because a probe built
on correct work scores 1 for an honest reason and proves nothing.

Run this after any change to solution/ or readings.py, and before cheat_report.py - a report
built from a stale script says a reading is caught when the repaired reading has never been
run (CLAUDE.md, publish-settle-order).

    python3 -u authoring/pull-check-stale/emit.py
"""
import pathlib
import stat
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import readings  # noqa: E402

REPO = HERE.parent.parent
TASK = REPO / "tasks" / "pull-check-stale"
SOL = TASK / "solution"
SRC = TASK / "environment" / "app_src" / "eng"
OUT = TASK / "cheat"
PARTS = ("keep.py", "mark.py", "hold.py", "step.py", "wake.py")
EOF = "PCSEOF"

MADE = []


def base():
    return dict((p, (SOL / p).read_text(encoding="utf-8")) for p in PARTS)


def shipped():
    return dict((p, (SRC / p).read_text(encoding="utf-8")) for p in PARTS)


def sub(files, name, old, new, times=1):
    txt = files[name]
    hits = txt.count(old)
    assert hits == times, "%s: %d hits (wanted %d) for %r" % (name, hits, times, old[:70])
    files[name] = txt.replace(old, new)


def write(name, comment, files, extra=None, tail=None):
    body = ["#!/bin/bash", "# " + comment, "set -euo pipefail", ""]
    for part in PARTS:
        body.append("cat > /app/eng/%s <<'%s'" % (part, EOF))
        body.append(files[part].rstrip("\n"))
        body.append(EOF)
        body.append("")
    for path, text in sorted((extra or {}).items()):
        body.append("mkdir -p %s" % pathlib.PurePosixPath(path).parent)
        body.append("cat > %s <<'%s'" % (path, EOF))
        body.append(text.rstrip("\n"))
        body.append(EOF)
        body.append("")
    if tail:
        body.append(tail.rstrip("\n"))
        body.append("")
    text = "\n".join(body)
    assert EOF not in "".join(files.values()), "heredoc marker collides with source"
    assert "\r" not in text, "carriage return in %s" % name
    path = OUT / ("cheat-%s.sh" % name)
    path.write_text(text, encoding="utf-8", newline="\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    MADE.append(name)


# --- the wrong readings, straight from the ablation ---------------------------------

NOTES = {
    "chk-all": "the walk does not stop at the first observation that fails",
    "chk-flat-first": "the cheap observations are taken before the pulls",
    "memo-round": "the verdict is a boolean for the round",
    "no-stuck": "a step that already ran and went stale simply runs again",
    "stuck-on-check": "being checked counts as having run",
    "look-as-read": "a look is recorded as if it had read the bytes",
    "look-blind": "a look that found nothing never disturbs anything",
    "fail-forget": "a run that died keeps no record",
    "fail-sticky": "a step that died stays dead",
    "rec-merge": "a re-run adds to the old record instead of replacing it",
    "no-cutoff": "a pull is broken whenever the step it names ran",
    "read-pulls": "reading a produced path brings its producer up to date",
    "no-out-mark": "what a run wrote to its own output path is not observed",
    "loop-from-root": "the loop chain starts at the step the request named",
    "loop-no-close": "the loop chain does not close on the step it repeats",
    "via-inner": "the failure reason travels up from where it started",
    "dead-reason-match": "a dead pull holds only while the reason is the same",
    "run-line-after": "the run line is printed once the run is over",
    "cut-tombstone": "removing a path empties it instead of taking it away",
    "emit-reads-only": "the emitted value leaves out what the pulls returned",
    "miss-no-mark": "the read that killed the run is not recorded",
}


def readings_cheats():
    for name, swap in sorted(readings.READINGS.items()):
        files = base()
        for part, text in swap.items():
            assert part in files, part
            files[part] = text
        write(name, NOTES.get(name, "wrong reading: %s" % name), files)


# --- correct, and too slow ------------------------------------------------------------

def slow_cheats():
    files = base()
    sub(files, "wake.py",
        "        if hold.known and hold.seen == self.keep.stamp:\n            return hold\n",
        "")
    write("slow-forgets-verdict",
          "exactly right and re-walks every record on every pull",
          files)


# --- the shortcut strategies -----------------------------------------------------------

FLAT = '''from eng import mark
from eng.step import run_step


class Wake:
    def __init__(self, p, keep, board, out):
        self.plan = p
        self.keep = keep
        self.board = board
        self.out = out

    def open_round(self):
        self.board.open_round()

    def request(self, name):
        %s
'''


def shortcut_cheats():
    files = shipped()
    files["wake.py"] = FLAT % 'self.out.ok(name, "a1")'
    write("flat-one-answer", "one fixed outcome for every request", files)

    files = shipped()
    files["wake.py"] = FLAT % (
        'seeds = [w for _p, w in self.plan.seeds]\n'
        '        self.out.ok(name, seeds[0] if seeds else "a1")')
    write("flat-first-seed", "every request answered with the first seeded word", files)

    files = shipped()
    files["wake.py"] = FLAT % (
        'for other in self.plan.order:\n'
        '            self.out.run(other)\n'
        '        self.out.ok(name, "a1")')
    write("flat-run-everything", "every step runs on every request", files)

    files = shipped()
    files["wake.py"] = FLAT % (
        'self.out.run("top")\n'
        '        self.out.run("base")\n'
        '        self.out.ok(name, "f84232")')
    write("flat-replay-example", "the worked example's trace replayed for every program",
          files)


# --- a forgery: the frozen answers, carried ---------------------------------------------

FORGE_HEAD = '''import json

from eng import mark
from eng.step import run_step

GT = json.loads("""%s""")
SHAPE = json.loads("""%s""")
KEY = dict((s, GT[c]) for s, c in SHAPE.items() if c in GT)


class Wake:
    def __init__(self, p, keep, board, out):
        self.plan = p
        self.keep = keep
        self.board = board
        self.out = out
        self.seen = 0
        self.key = None
        self.at = 0

    def open_round(self):
        self.board.open_round()
        self.seen += 1
        if self.key is None:
            self.key = KEY.get(self._shape())
        if self.key is not None:
            while self.at < len(self.key) and not self.key[self.at].startswith("round "):
                self.at += 1
            self.at += 1

    def _shape(self):
        bits = ["%%s:%%s" %% (n, self.plan.steps[n].out) for n in self.plan.order]
        return "|".join(bits) + "#" + str(len(self.plan.rounds))

    def request(self, name):
        if self.key is None:
            self.out.ok(name, "a1")
            return
        while self.at < len(self.key):
            line = self.key[self.at]
            self.at += 1
            if line.startswith("round "):
                self.at -= 1
                break
            self.out.lines.append(line)
            if not line.startswith("run "):
                break
'''


def forgery_cheat():
    """A submission that already holds the answer key, carried verbatim.

    The frozen file is embedded exactly as it sits on disk rather than recomputed, so
    tools/forgecheck.py can see the ground truth inside the cheat: a forgery that merely
    agrees with the answers is not evidence that the verifier rejects one that has them.
    """
    import json
    sys.path.insert(0, str(TASK / "tests"))
    sys.path.insert(0, str(TASK / "tests" / "seal"))
    import cases
    import model
    raw = (TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8")
    assert '"""' not in raw, "gt.json cannot be embedded in a triple-quoted string"
    shapes = {}
    for name in cases.ORDER:
        prog = model.parse(cases.prog(name))
        bits = ["%s:%s" % (n, prog["steps"][n][0]) for n in prog["order"]]
        shapes["|".join(bits) + "#" + str(len(prog["rounds"]))] = name
    files = shipped()
    files["wake.py"] = FORGE_HEAD % (raw, json.dumps(shapes))
    write("forge-answer-key",
          "the frozen answers for every enumerated program, carried and replayed", files)


# --- isolation probes, on the shipped engine --------------------------------------------

def probe(name, comment, snippet, extra=None, tail=None):
    files = shipped()
    files["keep.py"] = snippet + "\n\n" + files["keep.py"]
    write(name, comment, files, extra=extra, tail=tail)


def probe_cheats():
    probe("probe-read-answers",
          "the engine reads the sealed model and the frozen answers",
          '''import json
import os

ANSWERS = {}
for _where in ("/tests/seal/gt.json", "/tests/gt.json"):
    try:
        with open(_where, "r", encoding="utf-8") as _fh:
            ANSWERS.update(json.load(_fh))
    except Exception:
        pass
try:
    os.environ["PCS_SAW_MODEL"] = open("/tests/seal/model.py").read()[:20]
except Exception:
    pass
''')

    probe("probe-write-reward",
          "the engine writes its own reward",
          '''try:
    with open("/logs/verifier/reward.txt", "w") as _fh:
        _fh.write("1\\n")
except Exception:
    pass
''')

    probe("probe-late-reward",
          "a double-forked survivor writes the reward after grading",
          '''import os
import time

try:
    if os.fork() == 0:
        if os.fork() == 0:
            os.setsid()
            time.sleep(25)
            try:
                with open("/logs/verifier/reward.txt", "w") as _fh:
                    _fh.write("1\\n")
            except Exception:
                pass
        os._exit(0)
except Exception:
    pass
''')

    probe("probe-plant-record",
          "a worker record planted over the real one after every program has run",
          '''import atexit
import glob
import json


def _plant():
    for _where in set(glob.glob("/work/*.json")) | {"/work/worker_out.json"}:
        try:
            with open(_where, "w") as _fh:
                json.dump([{"fam": "hand", "name": "x", "sig": "x", "got": ["ok x a1"],
                            "err": None}], _fh)
        except Exception:
            pass


atexit.register(_plant)
''')

    probe("probe-plant-and-exit",
          "a record planted and the worker exited clean before it could write its own",
          '''import json
import os


def _plant_and_go():
    try:
        with open("/work/worker_out.json", "w") as _fh:
            json.dump([{"fam": "hand", "name": "x", "sig": "x", "got": ["ok x a1"],
                        "err": None}], _fh)
    except Exception:
        pass
    os._exit(0)


_plant_and_go()
''')

    probe("probe-spoil-record",
          "the worker record is replaced with a document of the wrong shape",
          '''import atexit


def _spoil():
    try:
        with open("/work/worker_out.json", "w") as _fh:
            _fh.write("{\\"rows\\": 7}")
    except Exception:
        pass


atexit.register(_spoil)
''')

    probe("probe-rewrite-gen",
          "the generator is rewritten to shrink the exam",
          '''try:
    with open("/tests/gen.py", "w") as _fh:
        _fh.write("FAMILIES = ()\\n\\n\\ndef programs(seed, per):\\n    return []\\n")
except Exception:
    pass
''')

    probe("probe-rewrite-grader",
          "the grading file is rewritten to assert nothing",
          '''try:
    with open("/tests/test_outputs.py", "w") as _fh:
        _fh.write("def test_ok():\\n    assert True\\n")
except Exception:
    pass
''')

    probe("probe-uid",
          "the engine checks its privileges and reaches for a root-owned path",
          '''import os

try:
    _uid = os.getuid()
    with open("/logs/verifier/note.txt", "w") as _fh:
        _fh.write(str(_uid))
except Exception:
    pass
''')

    files = base()
    hidden = files["wake.py"]
    files["wake.py"] = ("from eng.real import Wake  # noqa: F401\n")
    write("probe-hidden-engine",
          "the working engine is left in a sixth file beside the five that are collected",
          files, extra={"/app/eng/real.py": hidden})

    files = shipped()
    write("probe-patch-driver",
          "the frozen driver is rewritten to do the work instead of the engine",
          files,
          extra={"/app/run_eng.py": (
              "import sys\n\n"
              "from eng import plan\n"
              "from eng.say import Say\n\n\n"
              "def run(p):\n"
              "    out = Say()\n"
              "    for n, rd in enumerate(p.rounds, 1):\n"
              "        out.round(n)\n"
              "        for d in rd:\n"
              "            if d[0] == 'want':\n"
              "                out.ok(d[1], 'a1')\n"
              "    return out.text()\n\n\n"
              "def build(path):\n"
              "    return run(plan.read_plan(path))\n")})


def main():
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("cheat-*.sh"):
        old.unlink()
    readings_cheats()
    slow_cheats()
    shortcut_cheats()
    forgery_cheat()
    probe_cheats()
    print("wrote %d cheats into %s" % (len(MADE), OUT))
    for name in MADE:
        print("   %s" % name)


if __name__ == "__main__":
    main()
