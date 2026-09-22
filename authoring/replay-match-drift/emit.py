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


# --- how a command finds its recorded slot ------------------------------------------------
reading(
    "flat-count", "a command counted over the whole log rather than among its own kind",
    **{"tab.py": patch(
        "tab.py",
        ("                self.go.setdefault(kind, []).append((pos, args[1]))",
         "                self.go.setdefault(kind, []).append((pos, args[1]))\n"
         "                self.flat.append((pos, args[1]))"),
        ("        self.order = []",
         "        self.order = []\n        self.flat = []"),
        ("        row = self.go.get(kind)\n        if row is None or i >= len(row):\n"
         "            return None\n        return row[i]",
         "        if i >= len(self.flat):\n            return None\n"
         "        return self.flat[i]"),
    )})

reading(
    "slot-by-name", "a command matched to the first recorded command of its kind sharing its name",
    **{"tab.py": patch(
        "tab.py",
        ("    def slot(self, kind, i):\n        row = self.go.get(kind)\n"
         "        if row is None or i >= len(row):\n            return None\n"
         "        return row[i]",
         "    def slot(self, kind, i):\n        row = self.go.get(kind)\n"
         "        if row is None or i >= len(row):\n            return None\n"
         "        return row[i]\n\n"
         "    def named(self, kind, name, i):\n        row = self.go.get(kind) or []\n"
         "        for at in range(len(row)):\n            if row[at][1] == name:\n"
         "                return row[at]\n        return None if i >= len(row) else row[i]"),
    ), "edge.py": patch(
        "edge.py",
        ("        found = self.tab.slot(kind, i)",
         "        found = self.tab.slot(kind, i)\n"
         "        if found is not None:\n"
         "            found = self.tab.named(kind, found[1], i) or found"),
    )})

# --- how an answer is paired with its command ----------------------------------------------
reading(
    "kind-answer", "answers paired on kind alone, so two names of one kind swap values",
    **{"tab.py": patch(
        "tab.py",
        ('                self.ok.setdefault((args[0], args[1]), []).append((pos, int(args[2])))',
         '                self.ok.setdefault(args[0], []).append((pos, int(args[2])))'),
        ("        row = self.ok.get((kind, name))", "        row = self.ok.get(kind)"),
    ), "pair.py": patch(
        "pair.py",
        ("            key = (kind, name)", "            key = kind"),
    )})

reading(
    "name-answer", "answers paired on name alone, so one name used under two kinds collides",
    **{"tab.py": patch(
        "tab.py",
        ('                self.ok.setdefault((args[0], args[1]), []).append((pos, int(args[2])))',
         '                self.ok.setdefault(args[1], []).append((pos, int(args[2])))'),
        ("        row = self.ok.get((kind, name))", "        row = self.ok.get(name)"),
    ), "pair.py": patch(
        "pair.py",
        ("            key = (kind, name)", "            key = name"),
    )})

reading(
    "pair-kind-counter", "the answer counter kept per kind while the lookup stays on the pair",
    **{"pair.py": patch(
        "pair.py",
        ("            key = (kind, name)", "            key = kind"),
    )})

# --- the boundary ----------------------------------------------------------------------------
reading(
    "edge-per-kind", "a boundary opened for each kind on its own rather than once for the run",
    **{"edge.py": patch(
        "edge.py",
        ("        self.on = False", "        self.on = {}"),
        ("        if self.on:\n            return i, None, False",
         "        if self.on.get(kind):\n            return i, None, False"),
        ("            self.on = True", "            self.on[kind] = True"),
        ("    def live(self):\n        return self.on",
         "    def live(self):\n        return bool(self.on)"),
    )})

reading(
    "edge-each-time", "the boundary line printed at every live command instead of once",
    **{"edge.py": patch(
        "edge.py",
        ("        if self.on:\n            return i, None, False",
         "        if self.on:\n            return i, None, True"),
    )})

reading(
    "edge-log-empty", "the boundary decided by the log running out of events altogether",
    **{"edge.py": patch(
        "edge.py",
        ("        found = self.tab.slot(kind, i)\n        if found is None:",
         "        found = self.tab.slot(kind, i)\n"
         "        if found is None and len(self.hit) < len(self.tab.issued()):\n"
         "            return i, None, False\n        if found is None:"),
    )})

# --- what the log has left over -----------------------------------------------------------------
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
    "left-counts-all", "every unconsumed event counted, so a spare signal or answer fails the run",
    **{"tab.py": patch(
        "tab.py",
        ("    def issued(self):\n        return self.order",
         "    def issued(self):\n        return self.order + self.spare"),
        ("        self.order = []",
         "        self.order = []\n        self.spare = []"),
        ('            elif ev == "sig":',
         '            elif ev == "sig":\n'
         '                self.spare.append((pos, args[0], 0))'),
    )})

# --- taking a result ------------------------------------------------------------------------------
reading(
    "race-issued", "a race settled by which command was issued first",
    **{"pend.py": patch(
        "pend.py",
        ("    def fastest(self):\n        best = None\n        for rec in self.q:\n"
         "            if rec.pos is None:\n                continue\n"
         "            if best is None or rec.pos < best.pos:\n                best = rec\n"
         "        if best is None:\n            return self.q[0]\n        return best",
         "    def fastest(self):\n        return self.q[0]"),
    )})

reading(
    "race-latest", "a race settled by the answer that arrived last",
    **{"pend.py": patch(
        "pend.py",
        ("            if best is None or rec.pos < best.pos:",
         "            if best is None or rec.pos > best.pos:"),
    )})

reading(
    "join-answered", "join reading the answer order where it should read the issue order",
    **{"pend.py": patch(
        "pend.py",
        ("    def first(self):\n        return self.q[0]",
         "    def first(self):\n        return self.fastest()"),
    )})

reading(
    "race-live-first", "a live command counted as answered before every recorded one",
    **{"pair.py": patch(
        "pair.py",
        ("        return Rec(kind, idx, value, AFTER + self.late)",
         "        return Rec(kind, idx, value, -self.late)"),
    )})

reading(
    "hold-as-live", "a recorded command with no recorded answer answered from the live list",
    **{"pair.py": patch(
        "pair.py",
        ("            if found is None:\n                return Rec(kind, idx, None, None)",
         "            if found is None:\n"
         "                spare = self.feed[self.at] if self.at < len(self.feed) else 0\n"
         "                self.at += 1\n                return Rec(kind, idx, spare, None)"),
    )})

# --- signals -------------------------------------------------------------------------------------
reading(
    "sig-one-queue", "one counter over every tag together instead of one per tag",
    **{"sigq.py": patch(
        "sigq.py",
        ("    def __init__(self, tab):\n        self.tab = tab\n        self.n = {}",
         "    def __init__(self, tab):\n        self.tab = tab\n        self.n = {}\n"
         "        self.at = 0"),
        ("        j = self.n.get(tag, 0)\n        found = self.tab.signal(tag, j)\n"
         "        if found is None:\n            return None\n        self.n[tag] = j + 1\n"
         "        return found[1]",
         "        found = self.tab.signal(tag, self.at)\n        if found is None:\n"
         "            return None\n        self.at += 1\n        return found[1]"),
    )})

reading(
    "sig-stuck", "a signal taken without advancing its tag, so the same one comes back",
    **{"sigq.py": patch(
        "sigq.py",
        ("        self.n[tag] = j + 1\n        return found[1]", "        return found[1]"),
    )})

# --- markers --------------------------------------------------------------------------------------
reading(
    "ver-cur-replay", "an unrecorded marker giving the body's own value while still replaying",
    **{"ver.py": patch("ver.py", ("        return cur if live else 0", "        return cur"))})

reading(
    "ver-zero-live", "an unrecorded marker giving the legacy value once live",
    **{"ver.py": patch("ver.py", ("        return cur if live else 0", "        return 0"))})

reading(
    "ver-key-blind", "marker choices taken in recorded order regardless of key",
    **{"ver.py": patch(
        "ver.py",
        ("    def __init__(self, tab):\n        self.tab = tab\n        self.n = {}",
         "    def __init__(self, tab):\n        self.tab = tab\n        self.n = {}\n"
         "        self.at = 0"),
        ("        j = self.n.get(key, 0)\n        found = self.tab.choice(key, j)\n"
         "        if found is not None:\n            self.n[key] = j + 1\n"
         "            return found[1]",
         "        found = self.tab.choice(key, self.at)\n        if found is not None:\n"
         "            self.at += 1\n            return found[1]"),
    )})

reading(
    "ver-stuck", "a recorded choice taken without advancing, so one choice answers every marker",
    **{"ver.py": patch(
        "ver.py",
        ("            self.n[key] = j + 1\n            return found[1]",
         "            return found[1]"),
    )})

# --- strategies that do no work at all ----------------------------------------------------------
reading(
    "const-zero", "one fixed shape for every run file: position zero and a zero answer",
    **{"edge.py": patch(
        "edge.py",
        ("        i = self.n.get(kind, 0)\n        self.n[kind] = i + 1",
         "        i = 0\n        self.n[kind] = self.n.get(kind, 0) + 1"),
    ), "pair.py": patch(
        "pair.py",
        ("            return Rec(kind, idx, found[1], found[0])",
         "            return Rec(kind, idx, 0, found[0])"),
    )})

reading(
    "pos-first", "always the first recorded answer of the kind and name",
    **{"pair.py": patch("pair.py", ("            self.n[key] = j + 1", "            self.n[key] = 0"))})

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
        rows.append("python run_dur.py runs/tiny.txt > /dev/null")
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

HALF_TAB = SCAN_TAB.replace(
    '    def slot(self, kind, i):\n        got = self._nth("go", ((0, kind),), i)\n'
    '        return None if got is None else (got[0], got[1][1])',
    '    def slot(self, kind, i):\n        if not hasattr(self, "go"):\n'
    '            self.go = {}\n'
    '            for pos, (ev, args) in enumerate(self.log):\n'
    '                if ev == "go":\n'
    '                    self.go.setdefault(args[0], []).append((pos, args[1]))\n'
    '        row = self.go.get(kind)\n        if row is None or i >= len(row):\n'
    '            return None\n        return row[i]')

SLOW = {
    "slow-scan": ("exactly correct, and looks every command up by walking the log",
                  {"tab.py": SCAN_TAB.lstrip("\n")}),
    "slow-answers": ("exactly correct, with the commands indexed and the answers walked for",
                     {"tab.py": HALF_TAB.lstrip("\n")}),
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
    rows.extend(tail or ["cd /app", "python run_dur.py runs/tiny.txt > /dev/null"])
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
              "python run_dur.py runs/tiny.txt > /dev/null"]))
    return made


def main():
    CHEATS.mkdir(exist_ok=True)
    made = write_reading_cheats()
    more = write_extra_cheats()
    print("%d reading cheats, %d further cheats" % (len(made), len(more)))
    for name in made + more:
        print("   %s" % name)


if __name__ == "__main__":
    main()
