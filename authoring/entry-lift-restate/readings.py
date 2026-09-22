"""Every wrong reading of the brief, written as a change to the reference.

A reading that cannot be expressed is a reading that cannot be tested, so each one here is a
substitution on the reference source and `emit.py` refuses to write a cheat whose substitution
did not fire. Otherwise a cheat ships as the reference with a comment on top and scores 0 for
the wrong reason.

Each entry is (name, blurb, [(module, old, new), ...]) and the enumerated case that must catch
it is named in CATCHES below. `cheat_report.py` asserts that the case named for a reading is
one of the tests that actually fails, never only that the reward came out 0.
"""



LOCAL_READ = (
    '        lkey = ("s", sec, ent.a)\n'
    "        if trail is not None:\n"
    "            trail.add(lkey)\n"
    "        con = st.before(lkey, pos)\n"
    '        found = con[1] if con is not None and con[0] == "v" else None\n'
)

FIND_WHERE = (
    "        at, found = None, None\n"
    "        cur, seen = sec, set()\n"
    "        while cur not in seen:\n"
    "            seen.add(cur)\n"
    '            k = ("s", cur, ent.a)\n'
    "            if trail is not None:\n"
    "                trail.add(k)\n"
    "            c = st.before(k, pos)\n"
    "            if c is not None:\n"
    '                if c[0] == "v":\n'
    "                    at, found = cur, c[1]\n"
    "                    break\n"
    '                if c[0] == "m":\n'
    "                    break\n"
    '            lk = ("l", cur)\n'
    "            if trail is not None:\n"
    "                trail.add(lk)\n"
    "            lc = st.before(lk, pos)\n"
    "            if lc is None:\n"
    "                break\n"
    "            cur = lc[1]\n"
    "        if found is None:\n"
    "            return None, None\n"
    '        return ("s", at, ent.a), ("v", found + ent.b)\n'
)



ALL_AT_ONCE = '''
def settle(self):
    for i in self.bk.woken:
        self.push(i)
    self.bk.woken.clear()
    self.drain()
    eligible = []
    for i in self.bk.sleepers:
        if not self.bk.stands(i):
            continue
        ent = self.bk.ents[i]
        if sect.read(self.st, self.st.sec_before(i), ent.g, self.bk.upto, None) == ent.w:
            eligible.append(i)
    if not eligible:
        return 1
    for i in eligible:
        self.bk.woken.add(i)
        self.push(i)
    self.drain()
    return 2
'''

RETESTED = '''
def settle(self):
    for i in self.bk.woken:
        self.push(i)
    self.bk.woken.clear()
    passes = 1
    while True:
        self.drain()
        drop = []
        for i in self.bk.woken:
            ent = self.bk.ents[i]
            if sect.read(self.st, self.st.sec_before(i), ent.g, self.bk.upto, None) != ent.w:
                drop.append(i)
        if drop:
            for i in drop:
                self.bk.woken.discard(i)
                self.push(i)
            passes += 1
            continue
        up = wake.next_up(self.st, self.bk)
        if up is None:
            return passes
        self.bk.woken.add(up)
        self.push(up)
        passes += 1
'''


WHOLE_FILE = '''
def play(prog, out):
    run = Run(prog)
    run.bk.upto = len(prog.ents)
    for i, ent in enumerate(prog.ents):
        if ent.guard == "once":
            run.bk.sleepers.append(i)
        run.push(i)
    for stp in prog.steps:
        head = stp[0]
        if head == "ent":
            continue
        if head == "off" or head == "back":
            for i in run.bk.turn(stp[1], head == "off"):
                run.push(i)
        elif head == "get":
            passes = run.settle()
            found = sect.read(run.st, stp[1], stp[2], run.bk.upto, None)
            tell.one(out, stp[1], stp[2], found, passes)
        else:
            passes = run.settle()
            held, masked, links = run.st.board()
            tell.board(out, held, masked, links, passes)
'''



EDITS = [
    # --- the climb -------------------------------------------------------------
    ("climb-past-mask",
     "a masked slot is climbed past like an emptied one",
     [("sect.py",
       '            if con[0] == "m":\n                return None\n',
       '            if con[0] == "m":\n                pass\n')]),

    ("climb-stops-empty",
     "an emptied slot ends the climb like a masked one",
     [("sect.py",
       '        con = st.before(key, pos)\n'
       '        if con is not None:\n'
       '            if con[0] == "v":\n'
       '                return con[1]\n'
       '            if con[0] == "m":\n'
       '                return None\n',
       '        con = st.before(key, pos)\n'
       '        if con is not None:\n'
       '            if con[0] == "v":\n'
       '                return con[1]\n'
       '            return None\n')]),

    ("climb-no-guard",
     "the climb does not stop when it comes back to a section it has been at",
     [("sect.py",
       "        if at in seen:\n            return None\n        seen.add(at)\n",
       "        seen.add(at)\n")]),
    # --- what one entry does ---------------------------------------------------
    ("add-takes-zero",
     "a step over a name no section on the chain holds writes the step itself",
     [("step.py",
       "        found = sect.read(st, sec, ent.a, pos, trail)\n"
       "        if found is None:\n"
       "            return None, None\n"
       '        return ("s", sec, ent.a), ("v", found + ent.b)\n',
       "        found = sect.read(st, sec, ent.a, pos, trail)\n"
       '        return ("s", sec, ent.a), ("v", (0 if found is None else found) + ent.b)\n')]),

    ("add-reads-local",
     "a step reads only its own section's slot instead of climbing",
     [("step.py",
       "        found = sect.read(st, sec, ent.a, pos, trail)\n",
       LOCAL_READ)]),

    ("add-writes-found",
     "a step writes where the value was found rather than where the journal is",
     [("step.py",
       "        found = sect.read(st, sec, ent.a, pos, trail)\n"
       "        if found is None:\n"
       "            return None, None\n"
       '        return ("s", sec, ent.a), ("v", found + ent.b)\n',
       FIND_WHERE)]),

    ("set-keeps-mask",
     "a write into a masked slot leaves the mask standing",
     [("step.py",
       '    if kind == "set":\n        return key, ("v", ent.b)\n',
       '    if kind == "set":\n'
       '        con = st.before(key, pos)\n'
       '        if con is not None and con[0] == "m":\n'
       '            return key, ("m",)\n'
       '        return key, ("v", ent.b)\n')]),

    ("clr-keeps-mask",
     "emptying a masked slot leaves the mask standing",
     [("step.py",
       '    if kind == "clr":\n        return key, ("e",)\n',
       '    if kind == "clr":\n'
       '        con = st.before(key, pos)\n'
       '        if con is not None and con[0] == "m":\n'
       '            return key, ("m",)\n'
       '        return key, ("e",)\n')]),
    # --- conditions -------------------------------------------------------------
    ("gate-moves-sec",
     "a refused condition still moves the journal into its section",
     [("gate.py",
       '    if ent.guard != "if":\n        return True\n',
       '    if ent.guard != "if" or ent.kind == "sec":\n        return True\n')]),

    ("gate-moves-lnk",
     "a refused condition still links the section",
     [("gate.py",
       '    if ent.guard != "if":\n        return True\n',
       '    if ent.guard != "if" or ent.kind == "lnk":\n        return True\n')]),

    ("gate-reads-zero",
     "a condition is read in section 0 rather than where the journal is",
     [("gate.py",
       "    return sect.read(st, sec, ent.g, pos, trail) == ent.w\n",
       "    return sect.read(st, 0, ent.g, pos, trail) == ent.w\n")]),

    ("gate-reads-local",
     "a condition reads only its own section's slot instead of climbing",
     [("gate.py",
       "    return sect.read(st, sec, ent.g, pos, trail) == ent.w\n",
       '    key = ("s", sec, ent.g)\n'
       "    if trail is not None:\n"
       "        trail.add(key)\n"
       "    con = st.before(key, pos)\n"
       '    return con is not None and con[0] == "v" and con[1] == ent.w\n')]),
    # --- the sleeping entries ---------------------------------------------------
    ("once-all-at-once",
     "every sleeping entry whose condition is met wakes in the same pass",
     [("walk.py", "SETTLE", ALL_AT_ONCE)]),

    ("once-highest-first",
     "the highest-numbered sleeping entry wakes rather than the lowest",
     [("wake.py", "    for i in bk.sleepers:\n", "    for i in reversed(bk.sleepers):\n")]),

    ("once-retested",
     "a woken entry is read for again on every later pass and goes back to sleep",
     [("walk.py", "SETTLE", RETESTED)]),

    ("once-keeps-awake",
     "the entries woken by one settle are still awake when the next one starts",
     [("walk.py",
       "        for i in self.bk.woken:\n            self.push(i)\n"
       "        self.bk.woken.clear()\n",
       "        pass\n")]),

    ("once-wakes-lifted",
     "a sleeping entry in a withdrawn change can still wake",
     [("wake.py",
       "        if i in bk.woken or not bk.stands(i):\n",
       "        if i in bk.woken:\n")]),

    ("once-sec-at-end",
     "a sleeping condition is read in the section the pass ended in",
     [("wake.py",
       "        if sect.read(st, st.sec_before(i), ent.g, bk.upto, None) == ent.w:\n",
       "        if sect.read(st, st.sec_before(bk.upto), ent.g, bk.upto, None) == ent.w:\n")]),

    ("once-sec-zero",
     "a sleeping condition is read in section 0",
     [("wake.py",
       "        if sect.read(st, st.sec_before(i), ent.g, bk.upto, None) == ent.w:\n",
       "        if sect.read(st, 0, ent.g, bk.upto, None) == ent.w:\n")]),

    ("once-reads-at-pos",
     "a sleeping condition is read over the board as it stood at that entry's place",
     [("wake.py",
       "        if sect.read(st, st.sec_before(i), ent.g, bk.upto, None) == ent.w:\n",
       "        if sect.read(st, st.sec_before(i), ent.g, i, None) == ent.w:\n")]),
    # --- withdrawal and the journal ---------------------------------------------
    ("lift-keeps-sec",
     "a withdrawn change's section entry still moves the journal",
     [("book.py",
       "        if ent.chg in self.dead:\n            return False\n",
       '        if ent.chg in self.dead and ent.kind != "sec":\n            return False\n')]),

    ("lift-keeps-lnk",
     "a withdrawn change's link entry still links",
     [("book.py",
       "        if ent.chg in self.dead:\n            return False\n",
       '        if ent.chg in self.dead and ent.kind != "lnk":\n            return False\n')]),

    ("off-toggles",
     "withdrawing a change already withdrawn puts it back",
     [("book.py",
       "        if (chg in self.dead) == dead:\n            return ()\n"
       "        if dead:\n            self.dead.add(chg)\n"
       "        else:\n            self.dead.discard(chg)\n",
       "        if chg in self.dead:\n            self.dead.discard(chg)\n"
       "        else:\n            self.dead.add(chg)\n")]),

    ("settle-whole-file",
     "a question is answered over the whole file rather than the entries above it",
     [("walk.py", "PLAY", WHOLE_FILE)]),
    # --- what is printed --------------------------------------------------------
    ("all-counts-masked",
     "the held count takes in the masked slots as well",
     [("tell.py",
       '    out.line("all %d %d %d %d" % (passes, len(held), len(masked), len(links)))\n',
       '    out.line("all %d %d %d %d"\n'
       "             % (passes, len(held) + len(masked), len(masked), len(links)))\n")]),

    ("all-masked-first",
     "the masked slots are printed above the held ones",
     [("tell.py",
       "    for key in sorted(held):\n"
       '        out.line("v %d %d %d" % (key[0], key[1], held[key]))\n'
       "    for key in masked:\n"
       '        out.line("m %d %d" % key)\n',
       "    for key in masked:\n"
       '        out.line("m %d %d" % key)\n'
       "    for key in sorted(held):\n"
       '        out.line("v %d %d %d" % (key[0], key[1], held[key]))\n')]),

    ("all-sorts-by-name",
     "the detail lines are ordered by name before section",
     [("tell.py",
       "    for key in sorted(held):\n",
       "    for key in sorted(held, key=lambda k: (k[1], k[0])):\n")]),

    ("get-zero-for-nothing",
     "a reading that finds nothing prints 0 rather than a dash",
     [("tell.py",
       '    out.line("get %d %d %s %d" % (sec, name, "-" if found is None else found, passes))\n',
       '    out.line("get %d %d %s %d" % (sec, name, 0 if found is None else found, passes))\n')]),

    ("passes-from-zero",
     "passes are counted from zero",
     [("walk.py", "        passes = 1\n", "        passes = 0\n")]),

    ("passes-flat",
     "a settle reports one pass however many entries woke in it",
     [("walk.py", "            passes += 1\n", "            passes += 0\n")]),
]

WRONG = EDITS

# The enumerated program whose failure names each reading. `cheat_report.py` asserts that
# this test is among the ones that actually fail, so a cheat that scores 0 for some other
# reason is reported rather than counted.
# Correct, and too slow: these match the reference on every program small enough to finish,
# and the wall clock on the worker is the only thing that stops them.
SLOW = ("slow-walk", "slow-nocache")

CATCHES = {
    "climb-past-mask": "cut-stops",
    "climb-stops-empty": "clr-goes-on",
    "climb-no-guard": "climb-self",
    "add-takes-zero": "add-finds-none",
    "add-reads-local": "add-writes-here",
    "add-writes-found": "add-writes-here",
    "set-keeps-mask": "cut-then-set",
    "clr-keeps-mask": "cut-then-clr",
    "gate-moves-sec": "gate-blocks-sec",
    "gate-moves-lnk": "gate-blocks-lnk",
    "gate-reads-zero": "gate-reads-sec",
    "gate-reads-local": "gate-reads-here",
    "once-all-at-once": "once-one-per-pass",
    "once-highest-first": "once-one-per-pass",
    "once-retested": "once-no-retest",
    "once-keeps-awake": "once-resleeps",
    "once-wakes-lifted": "once-lifted",
    "once-sec-at-end": "once-sec-mirror",
    "once-sec-zero": "once-sec-mirror",
    "once-reads-at-pos": "once-reads-final",
    "lift-keeps-sec": "off-moves-writes",
    "lift-keeps-lnk": "off-unlinks",
    "off-toggles": "off-twice",
    "settle-whole-file": "later-entries-ignored",
    "all-counts-masked": "all-shape",
    "all-masked-first": "all-shape",
    "all-sorts-by-name": "all-shape",
    "get-zero-for-nothing": "add-finds-none",
    "passes-from-zero": "once-wakes",
    "passes-flat": "once-wakes",
}


# ---------------------------------------------------------------------------
# The contract tools/readingcheck.py reads: the reference, every reading as the files it
# would replace, and three helpers that drive one program under one policy.

import pathlib  # noqa: E402
import random  # noqa: E402

import lab  # noqa: E402

REFERENCE = str(pathlib.Path(__file__).resolve().parent.parent.parent
                / "tasks" / "entry-lift-restate" / "solution")


def _swap(src, old, new, where, name):
    if src.count(old) != 1:
        raise SystemExit("reading %s: %r matches %d times in %s"
                         % (name, old[:50], src.count(old), where))
    return src.replace(old, new, 1)


# Two readings do not end on their own: one climbs a link cycle for ever, the other wakes and
# un-wakes the same entry for ever. The worker's wall clock is what scores them, which
# `cheat_report.py` records; readingcheck has no timeout of its own, so it would hang here.
NEVER_ENDS = ("climb-no-guard", "once-retested")


def _build():
    """Each reading as {filename: source}, holding only the files it changes."""
    base = {}
    for part in ("book.py", "sect.py", "step.py", "gate.py", "wake.py", "walk.py", "tell.py"):
        base[part] = (pathlib.Path(REFERENCE) / part).read_text(encoding="utf-8")
    out = {}
    for name, _blurb, patches in WRONG:
        if name in NEVER_ENDS:
            continue
        files = {}
        for module, old, new in patches:
            src = files.get(module, base[module])
            if old == "SETTLE":
                head = "    def settle(self):\n"
                tail = "\n\ndef play(prog, out):\n"
                body = "\n".join(("    " + ln) if ln.strip() else ln
                                 for ln in new.strip("\n").splitlines())
                start, end = src.index(head), src.index(tail, src.index(head))
                files[module] = src[:start] + body + "\n" + src[end:]
            elif old == "PLAY":
                at = src.index("def play(prog, out):\n")
                files[module] = src[:at] + new.strip("\n") + "\n"
            else:
                files[module] = _swap(src, old, new, module, name)
        out[name] = files
    return out


READINGS = _build()

_active = [None, None]
_trees = {}
_ref_cache = {}


def _engine(policy):
    """One tree per policy, built once; the module namespace holds one of them at a time."""
    key = str(policy)
    if key not in _trees:
        _trees[key] = lab.build(policy)
    if _active[0] != key:
        _active[0] = key
        _active[1] = lab.loader(_trees[key])
    return _active[1]


def _warm():
    """Answer every program the checker will ask about while the reference is loaded.

    Without this the checker alternates reference and reading on every program and pays a
    module reload each way, which turns a minute into an hour.
    """
    eng = _engine(REFERENCE)
    for _name, text in enumerated() + generated(400):
        if text not in _ref_cache:
            _ref_cache[text] = tuple(eng.run(text))


def run(policy, text):
    if str(policy) == REFERENCE:
        if text not in _ref_cache:
            _warm()
            if text not in _ref_cache:
                _ref_cache[text] = tuple(_engine(policy).run(text))
        return _ref_cache[text]
    return tuple(_engine(policy).run(text))


def enumerated():
    import cases
    return [(name, "\n".join(cases.prog(name)) + "\n") for name in cases.ORDER]


def generated(n):
    import gen
    out = []
    per = max(1, n // len(gen.SMALL))
    for fam, fn in gen.SMALL:
        for k in range(per):
            rng = random.Random("reading/%s/%d" % (fam, k))
            out.append(("%s-%02d" % (fam, k), "\n".join(fn(rng, 30 + (k % 5) * 9)) + "\n"))
    return out


def reductions(text):
    """Structure-aware shrinking: drop a bracketed change whole, then single lines."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.strip() == "open":
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == "shut":
                    yield "\n".join(lines[:i] + lines[j + 1:])
                    break
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() in ("open", "shut"):
            continue
        yield "\n".join(lines[:i] + lines[i + 1:])
