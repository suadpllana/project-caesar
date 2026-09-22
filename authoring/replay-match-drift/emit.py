"""Every wrong reading of the contract, as a whole engine, and the cheat that ships it.

A reading is not an idea about a rule; it is a service that runs. Each one here is the
reference with one decision settled the other way, so what `tools/readingcheck.py` measures
and what `cheat/` ships are the same files and cannot drift apart. Run this after any change
to the reference or to a reading, and before readingcheck or cheat_report - a cheat emitted
before a reading was repaired tests the unrepaired reading.

    python3 authoring/replay-match-drift/emit.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

CHEATS = lab.TASK / "cheat"


def ref(name):
    """The reference file, with its module docstring stripped so a cheat stays readable."""
    text = (lab.SOL / name).read_text(encoding="utf-8")
    if text.startswith('"""'):
        text = text.split('"""', 2)[2].lstrip("\n")
    return text


def patch(name, *pairs):
    """The reference file with exact replacements, each of which must fire."""
    text = ref(name)
    for old, new in pairs:
        fresh, hits = text.replace(old, new), text.count(old)
        if hits != 1:
            raise SystemExit("patch on %s matched %d times, not 1:\n%s" % (name, hits, old))
        text = fresh
    return text


READINGS = {}
NOTES = {}


def reading(key, note, **files):
    READINGS[key] = files
    NOTES[key] = note


# --- which branch runs next ----------------------------------------------------------------
reading(
    "sched-mark-first", "a branch that has to be woken taken ahead of one that can just run",
    **{"sched.py": patch(
        "sched.py",
        ("    def pick(self):\n        while self.ready:", "    def pick(self):\n        while self.marked:\n"
         "            _mark, bid = heapq.heappop(self.marked)\n"
         "            who = self.all[bid]\n            if who.state == \"parked\":\n"
         "                who.state = \"running\"\n                return who\n"
         "        while self.ready:"),
    )})

reading(
    "sched-park-order", "the waiting branches taken in the order they went down, not by mark",
    **{"sched.py": patch(
        "sched.py",
        ("            heapq.heappush(self.marked, (mark, who.bid))",
         "            self.marked.append((len(self.marked), who.bid))"),
    )})

reading(
    "sched-last-mark", "the waiting branch whose mark is largest taken first",
    **{"sched.py": patch(
        "sched.py",
        ("            heapq.heappush(self.marked, (mark, who.bid))",
         "            heapq.heappush(self.marked, (-mark, who.bid))"),
    )})

reading(
    "sched-ready-last", "the ready branches taken from the highest number down",
    **{"sched.py": patch(
        "sched.py",
        ("        heapq.heappush(self.ready, made.bid)\n        return made.bid",
         "        heapq.heappush(self.ready, -made.bid)\n        return made.bid"),
        ("            who = self.all[heapq.heappop(self.ready)]",
         "            who = self.all[-heapq.heappop(self.ready)]"),
        ("                heapq.heappush(self.ready, bid)\n        self.idle = []",
         "                heapq.heappush(self.ready, -bid)\n        self.idle = []"),
    )})

# --- what a branch waits for ------------------------------------------------------------------
reading(
    "wake-no-claim", "a signal taken when the branch wakes rather than claimed as it goes down",
    **{"wake.py": patch(
        "wake.py",
        ("        self.n[payload] = at + 1\n        self.claim[bid] = found[1]\n        return found[0]",
         "        return found[0]"),
    )})

reading(
    "wake-mark-is-go", "a branch marked by where its command was recorded, not where its answer was",
    **{"pair.py": patch(
        "pair.py",
        ("        return Rec(kind, idx, found[1], found[0])",
         "        return Rec(kind, idx, found[1], idx)"),
    )})

# --- pairing an answer with its command ----------------------------------------------------------
reading(
    "pair-kind-only", "answers paired on kind alone, so two names of one kind swap values",
    **{"tab.py": patch(
        "tab.py",
        ('                self.ok.setdefault((args[0], args[1]), []).append((pos, int(args[2])))',
         '                self.ok.setdefault(args[0], []).append((pos, int(args[2])))'),
        ("        row = self.ok.get((kind, name))", "        row = self.ok.get(kind)"),
    ), "pair.py": patch(
        "pair.py",
        ("        key = (kind, name)", "        key = kind"),
    )})

reading(
    "pair-name-only", "answers paired on name alone, so one name under two kinds collides",
    **{"tab.py": patch(
        "tab.py",
        ('                self.ok.setdefault((args[0], args[1]), []).append((pos, int(args[2])))',
         '                self.ok.setdefault(args[1], []).append((pos, int(args[2])))'),
        ("        row = self.ok.get((kind, name))", "        row = self.ok.get(name)"),
    ), "pair.py": patch(
        "pair.py",
        ("        key = (kind, name)", "        key = name"),
    )})

reading(
    "pair-feed-at-issue", "an unrecorded result taken when the command is issued, not when it is taken",
    **{"pair.py": patch(
        "pair.py",
        ("        if not replayed:\n            return Rec(kind, idx, None, None)",
         "        if not replayed:\n            return Rec(kind, idx, self.spare(), None)"),
    )})

# --- how a command finds its recorded slot -----------------------------------------------------
reading(
    "tab-flat-count", "a command counted over the whole history rather than among its own kind",
    **{"tab.py": patch(
        "tab.py",
        ("                self.go.setdefault(kind, []).append((pos, args[1]))",
         "                self.go.setdefault(kind, []).append((pos, args[1]))\n"
         "                self.flat.append((pos, args[1]))"),
        ("        self.order = []", "        self.order = []\n        self.flat = []"),
        ("        row = self.go.get(kind)\n        if row is None or i >= len(row):\n"
         "            return None\n        return row[i]",
         "        if i >= len(self.flat):\n            return None\n        return self.flat[i]"),
    )})

reading(
    "edge-match-after-live", "commands still matched against the history once the live side is open",
    **{"edge.py": patch(
        "edge.py",
        ("        if self.on:\n            return i, None\n        return i, self.tab.slot(kind, i)",
         "        return i, self.tab.slot(kind, i)"),
    )})

# --- what the history has left over --------------------------------------------------------------
reading(
    "left-latest", "the leftover reported as the last recorded command left over, not the earliest",
    **{"edge.py": patch(
        "edge.py",
        ("        for pos, kind, at in self.tab.issued():\n            if pos not in self.hit:\n"
         "                return kind, at\n        return None",
         "        last = None\n        for pos, kind, at in self.tab.issued():\n"
         "            if pos not in self.hit:\n                last = (kind, at)\n        return last"),
    )})

reading(
    "left-counts-all", "every unconsumed line counted, so a spare signal fails the run",
    **{"tab.py": patch(
        "tab.py",
        ("    def issued(self):\n        return self.order",
         "    def issued(self):\n        return sorted(self.order + self.spare)"),
        ("        self.order = []", "        self.order = []\n        self.spare = []"),
        ('            elif ev == "sig":',
         '            elif ev == "sig":\n                self.spare.append((pos, args[0], 0))'),
    )})

reading(
    "left-none", "no leftover check at all, so a finished body always reports its value",
    **{"edge.py": patch(
        "edge.py",
        ("    def leftover(self):\n        for pos, kind, at in self.tab.issued():",
         "    def leftover(self):\n        return None\n\n    def unused(self):\n"
         "        for pos, kind, at in self.tab.issued():"),
    )})

# --- what a take reaches for -------------------------------------------------------------------
reading(
    "hold-last", "a take reaching for the branch's newest untaken command instead of its earliest",
    **{"hold.py": patch("hold.py", ("        return row[0]", "        return row[-1]"))})

# --- markers -------------------------------------------------------------------------------------
reading(
    "ver-cur-replay", "an unrecorded marker giving the body's own value while still replaying",
    **{"ver.py": patch("ver.py", ("        return cur if live else 0", "        return cur"))})

reading(
    "ver-zero-live", "an unrecorded marker giving the legacy value once the live side is open",
    **{"ver.py": patch("ver.py", ("        return cur if live else 0", "        return 0"))})

reading(
    "ver-key-blind", "marker choices taken in recorded order regardless of key",
    **{"ver.py": patch(
        "ver.py",
        ("    def __init__(self, tab):\n        self.tab = tab\n        self.n = {}",
         "    def __init__(self, tab):\n        self.tab = tab\n        self.n = {}\n        self.at = 0"),
        ("        j = self.n.get(key, 0)\n        found = self.tab.choice(key, j)\n"
         "        if found is not None:\n            self.n[key] = j + 1\n            return found[1]",
         "        found = self.tab.choice(key, self.at)\n        if found is not None:\n"
         "            self.at += 1\n            return found[1]"),
    )})

reading(
    "ver-stuck", "a recorded choice taken without advancing, so one choice answers every marker",
    **{"ver.py": patch(
        "ver.py",
        ("            self.n[key] = j + 1\n            return found[1]", "            return found[1]"),
    )})

# --- strategies that do no work at all ---------------------------------------------------------
reading(
    "const-zero", "one fixed shape for every run file: position zero and a zero answer",
    **{"edge.py": patch(
        "edge.py",
        ("        i = self.n.get(kind, 0)\n        self.n[kind] = i + 1",
         "        i = 0\n        self.n[kind] = self.n.get(kind, 0) + 1"),
    ), "pair.py": patch(
        "pair.py",
        ("        return Rec(kind, idx, found[1], found[0])",
         "        return Rec(kind, idx, 0, found[0])"),
    )})

reading(
    "pos-first", "always the first recorded answer of the kind and name",
    **{"pair.py": patch("pair.py", ("        self.n[key] = j + 1", "        self.n[key] = 0"))})


READING_ORDER = sorted(READINGS)


def files_for(key):
    """The whole six-file engine for one reading: the reference, with its files swapped in."""
    out = {}
    for name in lab.PARTS:
        out[name] = READINGS[key].get(name, ref(name))
    return out


def write_reading_cheats():
    made = []
    for key in READING_ORDER:
        rows = ["#!/bin/bash", "# %s" % NOTES[key], "set -euo pipefail", ""]
        for name, text in sorted(files_for(key).items()):
            rows.append("cat > /app/dur/%s <<'PYEOF'" % name)
            rows.append(text.rstrip("\n"))
            rows.append("PYEOF")
            rows.append("")
        rows.append("cd /app")
        rows.append("python run_dur.py progs/tiny.txt > /dev/null")
        path = CHEATS / ("cheat-%s.sh" % key)
        path.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
        path.chmod(0o755)
        made.append(path.name)
    return made


# --- engines that are exactly correct and cannot finish inside the clock --------------------
#
# These are not wrong readings and readingcheck must not see them: they settle every rule the
# way the reference does and lose on the execution limit alone, which is what the limit is for.

SCAN_TAB = """
class Tab(object):
    def __init__(self, log):
        self.log = log

    def _nth(self, want, keys, i):
        seen = 0
        for pos, (ev, args) in enumerate(self.log):
            if ev == want and all(args[at] == key for at, key in keys):
                if seen == i:
                    return pos, args
                seen += 1
        return None

    def slot(self, kind, i):
        got = self._nth("go", ((0, kind),), i)
        return None if got is None else (got[0], got[1][1])

    def answer(self, kind, name, j):
        got = self._nth("ok", ((0, kind), (1, name)), j)
        return None if got is None else (got[0], int(got[1][2]))

    def signal(self, tag, j):
        got = self._nth("sig", ((0, tag),), j)
        return None if got is None else (got[0], int(got[1][1]))

    def choice(self, key, j):
        got = self._nth("ch", ((0, key),), j)
        return None if got is None else (got[0], int(got[1][1]))

    def issued(self):
        out = []
        seen = {}
        for pos, (ev, args) in enumerate(self.log):
            if ev == "go":
                at = seen.get(args[0], 0)
                seen[args[0]] = at + 1
                out.append((pos, args[0], at))
        return out
"""

SCAN_SCHED = """
class Branch(object):
    __slots__ = ("bid", "pc", "acc", "due", "state")

    def __init__(self, bid, pc):
        self.bid = bid
        self.pc = pc
        self.acc = 0
        self.due = None
        self.state = "ready"


class Sched(object):
    def __init__(self):
        self.all = []
        self.mark = {}

    def open(self, pc):
        made = Branch(len(self.all), pc)
        self.all.append(made)
        return made.bid

    def pick(self):
        best = None
        for who in self.all:
            if who.state == "ready":
                if best is None or who.bid < best.bid:
                    best = who
        if best is not None:
            best.state = "running"
            return best
        for who in self.all:
            if who.state != "parked":
                continue
            mark = self.mark.get(who.bid)
            if mark is None:
                continue
            if best is None or mark < self.mark[best.bid]:
                best = who
        if best is None:
            return None
        best.state = "running"
        return best

    def park(self, who, mark):
        who.state = "parked"
        self.mark[who.bid] = mark

    def close(self, who):
        who.state = "ended"

    def release(self):
        for who in self.all:
            if who.state == "parked":
                who.state = "ready"
                self.mark[who.bid] = None
"""

SLOW = {
    "slow-sched": ("exactly correct, and walks the branches for the one whose turn is next",
                   {"sched.py": SCAN_SCHED.lstrip("\n")}),
    "slow-history": ("exactly correct, and walks the recorded history for every lookup",
                     {"tab.py": SCAN_TAB.lstrip("\n")}),
}


def shipped(name):
    return (lab.SRC / "dur" / name).read_text(encoding="utf-8")


def forge_tab():
    """A tab that recognises the enumerated run files and is the reference only for those."""
    import hashlib
    cases, _gen, _model = lab.sealed()
    keys = []
    for name in cases.ORDER:
        log = [row for row in cases.prog(name) if row.startswith("e ")]
        keys.append(hashlib.sha256("\n".join(log).encode("utf-8")).hexdigest()[:16])
    head = "import hashlib\n\nKNOWN = %r\n\n\n" % (tuple(sorted(set(keys))),)
    body = patch(
        "tab.py",
        ("    def slot(self, kind, i):",
         "    def slot(self, kind, i):\n        if not self.known:\n"
         "            if i >= len(self.flat):\n                return None\n"
         "            return self.flat[i]"),
        ("        self.order = []",
         "        self.order = []\n        self.flat = []\n"
         "        self.known = hashlib.sha256(\n"
         "            \"\\n\".join(\"e \" + \" \".join([ev] + list(args))\n"
         "                      for ev, args in log).encode(\"utf-8\")\n"
         "        ).hexdigest()[:16] in KNOWN"),
        ("                self.go.setdefault(kind, []).append((pos, args[1]))",
         "                self.go.setdefault(kind, []).append((pos, args[1]))\n"
         "                self.flat.append((pos, args[1]))"),
    )
    return head + body



def forge_truth_tab():
    """A tab that carries the frozen answers themselves and replays them through the writer.

    The trace is assembled by a file the agent does not hand over, so a forgery has to reach
    for it: this one replaces the writer at import and hands back the recorded trace whenever
    the history is one it has seen. Everything else is the shipped engine, so a run file it has
    not seen is answered wrongly and the population settles it.
    """
    import hashlib
    import json
    cases, _gen, _model = lab.sealed()
    raw = (lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8")
    # the frozen answers verbatim, in the shape the sealed file carries them
    dump = json.dumps(json.loads(raw), sort_keys=True)
    keys = {}
    for name in cases.ORDER:
        log = [row for row in cases.prog(name) if row.startswith("e ")]
        keys[hashlib.sha256("\n".join(log).encode("utf-8")).hexdigest()[:16]] = name
    rows = ["import hashlib", "import json", "", "from . import say", "",
            "FROZEN = json.loads(", "    '%s'" % dump, ")", "",
            "KEYS = %r" % (keys,), "",
            "TRUTH = dict((key, FROZEN[name]) for key, name in KEYS.items())"]
    rows += [
        "", "HERE = [None]", "", "_Real = say.Say", "", "",
        "class _Forge(_Real):",
        "    def __init__(self):",
        "        _Real.__init__(self)",
        "        self.canned = TRUTH.get(HERE[0])",
        "",
        "    def _out(self, fallback):",
        "        return list(self.canned) if self.canned is not None else fallback",
        "",
        "    def fin(self, value):",
        "        return self._out(_Real.fin(self, value))",
        "",
        "    def hold(self, kind, idx):",
        "        return self._out(_Real.hold(self, kind, idx))",
        "",
        "    def holdsig(self, tag):",
        "        return self._out(_Real.holdsig(self, tag))",
        "",
        "    def holdnone(self):",
        "        return self._out(_Real.holdnone(self))",
        "",
        "    def drift(self, kind, idx, want, got):",
        "        return self._out(_Real.drift(self, kind, idx, want, got))",
        "",
        "    def left(self, kind, idx):",
        "        return self._out(_Real.left(self, kind, idx))",
        "",
        "    def over(self):",
        "        return self._out(_Real.over(self))",
        "",
        "",
        "say.Say = _Forge",
        "",
        "",
    ]
    body = shipped("tab.py").replace(
        "    def __init__(self, log):\n        self.go = []",
        "    def __init__(self, log):\n"
        "        HERE[0] = hashlib.sha256(\n"
        "            \"\\n\".join(\"e \" + \" \".join([ev] + list(args))\n"
        "                      for ev, args in log).encode(\"utf-8\")\n"
        "        ).hexdigest()[:16]\n        self.go = []")
    return "\n".join(rows) + body

# --- probes: the verifier runs submitted code, so the reward has to be unreachable to it ----
#
# Each one leaves the shipped engine in place, so it would score 0 on the work, and then tries
# to take the reward another way. Every one of them must still score 0, and the attack happens
# while the run is going on rather than at import, because the runner arms nothing until then.

def probe_tab(attack):
    text = shipped("tab.py")
    head = "import os\nimport sys\n\n\ndef _go():\n%s\n\n" % attack
    return head + text.replace(
        "    def __init__(self, log):\n        self.go = []",
        "    def __init__(self, log):\n        _go()\n        self.go = []")


PROBES = {
    "probe-answer-key": ("reads the sealed model and frozen answers from inside the run", """
    for path in ("/tests/seal", "/tests/seal/gt.json", "/tests/seal/model.py"):
        try:
            if path.endswith("seal"):
                os.listdir(path)
            else:
                open(path, "rb").read()
            sys.stderr.write("seal readable: %s\\n" % path)
        except Exception as exc:
            sys.stderr.write("seal refused: %s\\n" % exc)
"""),
    "probe-reward": ("writes the reward file directly", """
    try:
        open("/logs/verifier/reward.txt", "w").write("1\\n")
    except Exception as exc:
        sys.stderr.write("reward refused: %s\\n" % exc)
"""),
    "probe-late-reward": ("double forks a survivor that writes the reward after grading", """
    if os.environ.get("RMD_FORKED"):
        return
    os.environ["RMD_FORKED"] = "1"
    try:
        if os.fork() == 0:
            os.setsid()
            if os.fork() == 0:
                import time
                time.sleep(25)
                try:
                    open("/logs/verifier/reward.txt", "w").write("1\\n")
                except Exception:
                    pass
                os._exit(0)
            os._exit(0)
    except Exception as exc:
        sys.stderr.write("fork refused: %s\\n" % exc)
"""),
    "probe-plant-record": ("plants a passing record where stage one writes its own", """
    import json
    try:
        sys.path.insert(0, "/tests")
        sys.path.insert(0, "/tests/seal")
        import cases
        import model
        rows = [{"fam": "hand", "name": n, "stamp": "x",
                 "printed": model.expect(cases.prog(n))} for n in cases.ORDER]
        open("/work/stage_one.json", "w").write(json.dumps(rows))
    except Exception as exc:
        sys.stderr.write("plant refused: %s\\n" % exc)
"""),
    "probe-crash-worker": ("plants a record and exits clean before stage one can overwrite it", """
    import json
    try:
        open("/work/stage_one.json", "w").write(json.dumps([{"name": "x", "printed": []}]))
    except Exception as exc:
        sys.stderr.write("plant refused: %s\\n" % exc)
    os._exit(0)
"""),
    "probe-malformed": ("spoils stage one's record on the way out", """
    import atexit

    def _spoil():
        try:
            open("/work/stage_one.json", "w").write("not json at all")
        except Exception:
            pass

    atexit.register(_spoil)
"""),
    "probe-rewrite-gen": ("rewrites the generator so the exam shrinks", """
    try:
        open("/tests/gen.py", "w").write(
            "FAMILIES = [('plain', False)]\\n\\n\\ndef programs(seed, per):\\n    return []\\n")
    except Exception as exc:
        sys.stderr.write("generator refused: %s\\n" % exc)
"""),
    "probe-rewrite-grader": ("rewrites the grading file", """
    try:
        open("/tests/test_outputs.py", "w").write("def test_pass():\\n    assert True\\n")
    except Exception as exc:
        sys.stderr.write("grader refused: %s\\n" % exc)
"""),
    "probe-shrink-exam": ("rewrites the seed and size stage one was handed", """
    try:
        open("/work/per", "w").write("1\\n")
        open("/work/seed", "w").write("aaaa\\n")
    except Exception as exc:
        sys.stderr.write("exam refused: %s\\n" % exc)
"""),
    "probe-privilege": ("tries to open the sealed directory and to drop back to root", """
    try:
        os.chmod("/tests/seal", 0o755)
        sys.stderr.write("seal opened\\n")
    except Exception as exc:
        sys.stderr.write("chmod refused: %s\\n" % exc)
    try:
        os.setuid(0)
        sys.stderr.write("root taken\\n")
    except Exception as exc:
        sys.stderr.write("setuid refused: %s\\n" % exc)
"""),
}


def write_one(name, note, files, tail=None):
    rows = ["#!/bin/bash", "# %s" % note, "set -euo pipefail", ""]
    for part, text in sorted(files.items()):
        rows.append("cat > /app/dur/%s <<'PYEOF'" % part)
        rows.append(text.rstrip("\n"))
        rows.append("PYEOF")
        rows.append("")
    rows.extend(tail or ["cd /app", "python run_dur.py progs/tiny.txt > /dev/null"])
    path = CHEATS / ("cheat-%s.sh" % name)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    path.chmod(0o755)
    return path.name


def write_extra_cheats():
    made = []
    for key, (note, swap) in sorted(SLOW.items()):
        files = {part: swap.get(part, ref(part)) for part in lab.PARTS}
        made.append(write_one(key, note, files))
    forged = {part: ref(part) for part in lab.PARTS}
    forged["tab.py"] = forge_tab()
    hijack = {part: shipped(part) for part in lab.PARTS}
    hijack["tab.py"] = forge_truth_tab()
    made.append(write_one(
        "forge-truth",
        "carries the frozen answers and hands them back through a writer it replaced",
        hijack))
    made.append(write_one(
        "forge-hand",
        "carries the shipped run files' fingerprints and is the reference only for those",
        forged))
    for key, (note, attack) in sorted(PROBES.items()):
        files = {part: shipped(part) for part in lab.PARTS}
        files["tab.py"] = probe_tab(attack.rstrip("\n"))
        made.append(write_one(key, note, files))
    side = {part: shipped(part) for part in lab.PARTS}
    side["tab.py"] = "from .side import Tab\n\n\nTAB = Tab\n"
    made.append(write_one(
        "probe-extra-file",
        "hides the working engine in a seventh file beside the six that are collected",
        side,
        tail=["cat > /app/dur/side.py <<'PYEOF'",
              ref("tab.py").rstrip("\n"),
              "PYEOF",
              "",
              "cd /app",
              "python run_dur.py progs/tiny.txt > /dev/null"]))
    return made


def main():
    """Write every cheat this design has, and take away every one it does not.

    A redesign leaves the previous design's cheats on disk, where they ship, score 0 for
    reasons that no longer mean anything, and make the bundle claim coverage it does not have.
    Eighteen of them survived the rebuild on 2026-09-22 before this was added.
    """
    CHEATS.mkdir(exist_ok=True)
    made = write_reading_cheats()
    more = write_extra_cheats()
    keep = set(made) | set(more)
    gone = sorted(p.name for p in CHEATS.glob("cheat-*.sh") if p.name not in keep)
    for name in gone:
        (CHEATS / name).unlink()
    if gone:
        print("removed %d cheats left from an earlier design: %s"
              % (len(gone), ", ".join(gone)))
    print("%d reading cheats, %d further cheats" % (len(made), len(more)))
    for name in made + more:
        print("   %s" % name)


if __name__ == "__main__":
    main()
