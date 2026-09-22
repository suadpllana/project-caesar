"""Write cheat/ from the readings, the slow families, the shortcuts, a forgery and the probes.

The reading cheats and the readings measured by tools/readingcheck.py come from the same
dictionary, so the two cannot drift apart. Run this after any change to readings.py, never
before it (CLAUDE.md, 2026-09-09).

Two rules the shapes here follow:

  * a probe ships the *shipped* engine plus its attack, never a correct one. A probe carrying a
    correct engine scores 1 whether or not its attack worked and proves nothing.
  * a probe interferes during the run, not at import time. A probe that fires while the module
    is being imported attacks a runner that has not armed anything yet.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402
import readings as rd  # noqa: E402

cases, gen, model = lab.sealed()
CHEAT = lab.TASK / "cheat"
BROKEN = lab.TASK / "environment" / "app_src" / "crd"

GOOD = {name: (lab.SOL / name).read_text(encoding="utf-8") for name in lab.PARTS}
BAD = {name: (BROKEN / name).read_text(encoding="utf-8") for name in lab.PARTS}


def write(name, note, files, extra=""):
    """One cheat script: the seven files, plus anything the probe needs on top."""
    body = ["#!/bin/bash", "# %s" % note, "set -euo pipefail", ""]
    for part in lab.PARTS:
        body.append("cat > /app/crd/%s <<'PYEOF'" % part)
        body.append(files[part].rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    if extra:
        body.append(extra.rstrip("\n"))
        body.append("")
    text = "\n".join(body)
    assert "\r" not in text
    out = CHEAT / ("cheat-%s.sh" % name)
    out.write_text(text, encoding="utf-8", newline="\n")
    out.chmod(0o755)
    return out.name


# --- the wrong readings ----------------------------------------------------------------

READING_NOTES = {
    "obs-per-action": "observes after every action instead of at the end of an ok step",
    "obs-err-too": "observes a step that ended err before rolling it back",
    "pre-same-obs": "a prerequisite credited at this observation lets its dependant in",
    "credit-recompute": "credit recomputed from the records, so it does not settle",
    "rearm-now": "a shut goal is creditable again the moment its predicate holds",
    "rearm-on-touch": "a shut goal re-arms only when a record it reads changes",
    "void-named-only": "a firing takes only the goal it names and leaves the dependants",
    "void-cone-shut": "a firing shuts the dependants as well as the goal it names",
    "void-walk-order": "voids emitted in the order a walk reaches them",
    "void-uncredited-skip": "a firing on a goal with no credit does nothing at all",
    "bars-first": "violations fire before credit is applied",
    "bar-state": "violations read as predicates over the records rather than as changes",
    "bar-back-any": "back fires on any change of value, not only a fall",
    "err-keeps": "a step that ended err keeps what it wrote",
    "bud-per-step": "the budget counts steps instead of actions",
    "bud-spares-failed": "the actions of a step that ended err are not charged",
    "close-keeps": "an episode closed short keeps its records",
    "close-loses-credit": "an episode closed short loses its credit",
    "up-strict": "up read as strictly greater than",
    "off-zero": "a record standing at zero counts as having no value",
    "rep-count": "an episode reports how many goals it holds, not their weights",
    "rep-full-any": "any credit at all counts the episode as full",
}


def reading_cheats():
    made = []
    for name, files in sorted(rd.READINGS.items()):
        mix = dict(GOOD)
        mix.update(files)
        made.append(write(name, READING_NOTES[name], mix))
    return made


# --- correct, and too slow ---------------------------------------------------------------

def slow_cheats():
    made = []
    snap = dict(GOOD)
    snap["store.py"] = (HERE / "slow-snap" / "crd" / "store.py").read_text(encoding="utf-8")
    snap["obs.py"] = (HERE / "slow-snap" / "crd" / "obs.py").read_text(encoding="utf-8")
    made.append(write("slow-copy",
                      "exactly correct, and copies the records per step and per observation",
                      snap))
    sweep = dict(GOOD)
    sweep["book.py"] = (HERE / "slow-sweep" / "crd" / "book.py").read_text(encoding="utf-8")
    sweep["obs.py"] = (HERE / "slow-sweep" / "crd" / "obs.py").read_text(encoding="utf-8")
    made.append(write("slow-sweep",
                      "exactly correct, and goes over the whole rubric at every observation",
                      sweep))
    return made


# --- the shortcut strategies ------------------------------------------------------------------

CONST_EP = '''from crd import tally


def run(cfg, one, store, sums, out):
    tally.done(one, None, 0, sums, out)
'''

CONST_TALLY_ZERO = '''class Sum:
    __slots__ = ("eps", "full", "got", "whole")

    def __init__(self):
        self.eps = 0
        self.full = 0
        self.got = 0
        self.whole = 0

    def add(self, got, whole):
        self.eps += 1
        self.got += got
        self.whole += whole
        if got == whole:
            self.full += 1


def done(one, book, used, sums, out):
    whole = sum(goal.weight for goal in one.goals)
    out.line("ep %s 0 %d 0" % (one.name, whole))
    sums.add(0, whole)


def close(sums, out):
    out.line("run %d %d %d %d" % (sums.eps, sums.full, sums.got, sums.whole))
'''

CONST_TALLY_FULL = CONST_TALLY_ZERO.replace(
    '''    whole = sum(goal.weight for goal in one.goals)
    out.line("ep %s 0 %d 0" % (one.name, whole))
    sums.add(0, whole)''',
    '''    whole = sum(goal.weight for goal in one.goals)
    out.line("ep %s %d %d 0" % (one.name, whole, whole))
    sums.add(whole, whole)''')

REPLAY_EP = '''def run(cfg, one, store, sums, out):
    out.line("mark 0")
    out.line("fire 0")
    out.line("void 0")
    out.line("ep a1 0 5 6")
'''

REPLAY_TALLY = '''class Sum:
    __slots__ = ("eps",)

    def __init__(self):
        self.eps = 0

    def add(self, got, whole):
        self.eps += 1


def done(one, book, used, sums, out):
    return None


def close(sums, out):
    out.line("run 1 0 0 5")
'''


def shortcut_cheats():
    made = []
    zero = dict(GOOD)
    zero["ep.py"] = CONST_EP
    zero["tally.py"] = CONST_TALLY_ZERO
    made.append(write("const-nothing", "one fixed output for every trail: nothing credited",
                      zero))
    full = dict(GOOD)
    full["ep.py"] = CONST_EP
    full["tally.py"] = CONST_TALLY_FULL
    made.append(write("const-everything",
                      "one fixed output for every trail: every goal credited", full))
    replay = dict(GOOD)
    replay["ep.py"] = REPLAY_EP
    replay["tally.py"] = REPLAY_TALLY
    made.append(write("pos-replay-example",
                      "the worked example's own output replayed for every trail", replay))
    return made


# --- the forgery -----------------------------------------------------------------------------------

def episode_key(one):
    """What an episode is, as a string, so an answer can be looked up by the program."""
    parts = ["g %d %d %s %s %d %d" % (goal.gid, goal.weight, ",".join(str(x) for x in goal.pre),
                                      goal.kind, goal.key, goal.val)
             for goal in one.goals]
    parts += ["b %d %d %s %d" % (bar.bid, bar.goal, bar.kind, bar.key) for bar in one.bars]
    for actions, done in one.steps:
        parts.append("s " + ";".join("%s %d %d" % act for act in actions) + (" ok" if done else " err"))
    return one.name + "|" + "|".join(parts)


def forged_index():
    """Where each episode's answer sits inside the frozen file, keyed on the episode itself.

    The answers themselves are not copied: the cheat carries `tests/seal/gt.json` verbatim and
    slices it, which is what makes this a carrier of the answer key rather than a second
    implementation of the rules - and what `tools/forgecheck.py` looks for.
    """
    sys.path.insert(0, str(lab.TASK / "tests" / "seal"))
    import spec

    gt = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    index = {}
    for name in cases.ORDER:
        lines = cases.prog(name)
        want = gt[name]
        _cfg, _seeds, eps = spec.parse("\n".join(lines) + "\n")
        here = 0
        for one in eps:
            start = here
            while not want[here].startswith("ep "):
                here += 1
            head = want[here]
            here += 1
            part = head.split()
            index[episode_key(one)] = [name, start, here, int(part[2]), int(part[3])]
    return index


FORGE_EP = '''import json

from crd import book as bk
from crd import obs, store, tally, void

_GT = json.loads(store.GT)
_IX = store.INDEX


def _key(one):
    parts = ["g %d %d %s %s %d %d" % (goal.gid, goal.weight,
                                      ",".join(str(x) for x in goal.pre),
                                      goal.kind, goal.key, goal.val)
             for goal in one.goals]
    parts += ["b %d %d %s %d" % (bar.bid, bar.goal, bar.kind, bar.key) for bar in one.bars]
    for actions, done in one.steps:
        parts.append("s " + ";".join("%s %d %d" % act for act in actions)
                     + (" ok" if done else " err"))
    return one.name + "|" + "|".join(parts)


def watched(book, watch, store, out, moved):
    delta = {}
    for gid in book.credit(store, moved, delta):
        out.line("mark %d" % gid)
    for bar in watch.near(moved):
        if watch.fires(bar, store):
            out.line("fire %d" % bar.bid)
            for gid in void.fire(book, bar, delta):
                out.line("void %d" % gid)
    book.settle(delta)
    watch.refresh(store, moved)


def run(cfg, one, store, sums, out):
    got = _IX.get(_key(one))
    if got is not None:
        for line in _GT[got[0]][got[1]:got[2]]:
            out.line(line)
        sums.add(got[3], got[4])
        return
    book = bk.Book(one.goals)
    watch = obs.Watch(one.bars)
    start = store.mark()
    store.take()
    watch.base(store)
    used = 0
    closed = False
    for actions, done in one.steps:
        here = store.mark()
        short = False
        for op, key, val in actions:
            if used >= cfg.budget:
                short = True
                break
            if op == "put":
                store.put(key, val)
            else:
                store.cut(key)
            used += 1
        if short or not done:
            store.undo(here)
            if short:
                closed = True
                break
            continue
        watched(book, watch, store, out, store.take())
    if closed:
        store.undo(start)
    store.seal(start)
    store.take()
    tally.done(one, book, used, sums, out)
'''


def forgery_cheat():
    # Fast and wrong on one rule, so a miss is graded rather than timed out: the point of a
    # forgery is that it passes every trail it could have seen and dies on the rest.
    files = probe_base()
    gt_text = (lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8")
    assert '"""' not in gt_text
    files["ep.py"] = FORGE_EP
    files["store.py"] = (GOOD["store.py"] + "\n\nGT = r\"\"\"" + gt_text
                         + "\"\"\"\n\nINDEX = " + json.dumps(forged_index()) + "\n")
    return [write("forge-hand",
                  "carries the frozen answers for every hand trail and nothing else",
                  files)]


# --- the probes ---------------------------------------------------------------------------------------

PROBES = {
    "probe-answer-key": (
        "reads the sealed model and the frozen answers out of the verifier image",
        '''import json
import pathlib

_SEEN = []
_DONE = []


def _peek():
    if _DONE:
        return
    _DONE.append(1)
    for spot in ("/tests/seal/gt.json", "/tests/seal/model.py", "/tests/seal/spec.py"):
        try:
            _SEEN.append(pathlib.Path(spot).read_text(encoding="utf-8")[:80])
        except Exception as exc:
            _SEEN.append("%s: %s" % (spot, exc))
    try:
        pathlib.Path("/work/peeked.json").write_text(json.dumps(_SEEN), encoding="utf-8")
    except Exception:
        pass
'''),
    "probe-late-reward": (
        "double-forks a process that writes the reward after grading",
        '''import os
import sys
import time

_DONE = []


def _peek():
    if _DONE:
        return
    _DONE.append(1)
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
        os._exit(0)
    time.sleep(25)
    for spot in ("/logs/verifier/reward.txt", "/logs/reward.txt"):
        try:
            with open(spot, "w", encoding="utf-8") as fh:
                fh.write("1\\n")
        except Exception:
            pass
    os._exit(0)
'''),
    "probe-plant-report": (
        "plants a passing worker record and lets the run finish",
        '''import json
import pathlib

_DONE = []


def _peek():
    if _DONE:
        return
    _DONE.append(1)
    try:
        pathlib.Path("/work/worker_out.json").write_text(
            json.dumps([{"fam": "hand", "name": "plain-all", "sig": "x",
                         "got": ["ok"], "err": None}]), encoding="utf-8")
    except Exception:
        pass
'''),
    "probe-crash-worker": (
        "plants a passing record and exits the worker clean before it can be overwritten",
        '''import json
import os
import pathlib

_SEEN = []


def _peek():
    _SEEN.append(1)
    if len(_SEEN) < 40:
        return
    try:
        pathlib.Path("/work/worker_out.json").write_text(
            json.dumps([{"fam": "hand", "name": "plain-all", "sig": "x",
                         "got": ["ok"], "err": None}]), encoding="utf-8")
    except Exception:
        pass
    os._exit(0)
'''),
    "probe-privilege": (
        "checks its uid and tries to write the verifier's own paths",
        '''import os
import pathlib

_DONE = []


def _peek():
    if _DONE:
        return
    _DONE.append(1)
    notes = ["uid %d euid %d" % (os.getuid(), os.geteuid())]
    for spot in ("/logs/verifier/reward.txt", "/tests/test_outputs.py", "/tests/seal/gt.json"):
        try:
            with open(spot, "a", encoding="utf-8") as fh:
                fh.write("\\n")
            notes.append("wrote %s" % spot)
        except Exception as exc:
            notes.append("%s: %s" % (spot, exc))
    try:
        pathlib.Path("/work/priv.txt").write_text("\\n".join(notes), encoding="utf-8")
    except Exception:
        pass
'''),
    "probe-shrink-set": (
        "rewrites its own copy of the nonce and the family size to shrink the exam",
        '''import pathlib

_DONE = []


def _peek():
    if _DONE:
        return
    _DONE.append(1)
    for spot, text in (("/work/per", "1\\n"), ("/work/nonce", "0" * 32 + "\\n"),
                       ("/logs/verifier/per", "1\\n")):
        try:
            pathlib.Path(spot).write_text(text, encoding="utf-8")
        except Exception:
            pass
'''),
    "probe-rewrite-gen": (
        "rewrites the generator in the verifier image so fewer trails are graded",
        '''import pathlib

_DONE = []

SHRUNK = """FAMILIES = (("plain", False),)
BIG_EACH = 1


def programs(seed, per):
    return []
"""


def _peek():
    if _DONE:
        return
    _DONE.append(1)
    for spot in ("/tests/gen.py", "/tests/cases.py", "/tests/test_outputs.py"):
        try:
            pathlib.Path(spot).write_text(SHRUNK, encoding="utf-8")
        except Exception:
            pass
'''),
}

MALFORMED_TALLY = '''class Sum:
    __slots__ = ("eps", "full", "got", "whole")

    def __init__(self):
        self.eps = 0
        self.full = 0
        self.got = 0
        self.whole = 0

    def add(self, got, whole):
        self.eps += 1
        self.got += got
        self.whole += whole
        if got == whole:
            self.full += 1


class Junk:
    def __repr__(self):
        return "junk"


def done(one, book, used, sums, out):
    got = sum(1 for goal in one.goals if book.held(goal.gid))
    whole = sum(goal.weight for goal in one.goals)
    out.line("ep %s %d %d %d" % (one.name, got, whole, used))
    sums.add(got, whole)


def close(sums, out):
    out.line({"run": [Junk(), sums.eps], "why": Junk()})
'''

DELEGATE = '''from crd import extra


class Store(extra.Store):
    pass
'''


def probe_base():
    """Fast, and wrong on one named rule.

    A probe must not ship the slow shipped engine: the worker would run out of its wall clock,
    the reward would be 0 before the grader saw anything, and the probe would prove nothing
    about isolation (CLAUDE.md, 2026-09-06: assert the layer, never just the reward). With this
    base every probe finishes, the grader runs, and a 0 is attributable to `rep-weights` - so a
    1 could only have come from the attack.
    """
    files = dict(GOOD)
    files.update(rd.READINGS["rep-count"])
    return files


def probe_cheats():
    made = []
    for name, (note, attack) in sorted(PROBES.items()):
        files = probe_base()
        # The attack rides in store.py and is reached from put(), which the runner calls
        # once it is running - never at import time.
        body = files["store.py"].replace(
            "    def put(self, key, value):\n",
            "    def put(self, key, value):\n        _peek()\n")
        assert body != files["store.py"], name
        files["store.py"] = attack + "\n\n" + body
        made.append(write(name, note, files))

    # Garbage on the way out of the worker, rather than a wrong answer.
    junk = probe_base()
    junk["tally.py"] = MALFORMED_TALLY
    made.append(write("probe-malformed",
                      "spoils the record on its way out of the worker", junk))

    # A working engine in a file beside the seven that are collected.
    hidden = probe_base()
    hidden["store.py"] = DELEGATE
    extra_src = (lab.SOL / "store.py").read_text(encoding="utf-8")
    made.append(write("probe-uncollected-file",
                      "hides the working store in a file beside the seven that are collected",
                      hidden,
                      "cat > /app/crd/extra.py <<'PYEOF'\n"
                      + extra_src.rstrip("\n") + "\nPYEOF\n"))
    return made


READING_BUILDERS = ()


def main():
    CHEAT.mkdir(parents=True, exist_ok=True)
    for old in CHEAT.glob("cheat-*.sh"):
        old.unlink()
    made = []
    made += reading_cheats()
    made += slow_cheats()
    made += shortcut_cheats()
    made += forgery_cheat()
    made += probe_cheats()
    print("%d cheats written" % len(made))
    for name in sorted(made):
        print("   %s" % name)


if __name__ == "__main__":
    main()
