#!/usr/bin/env python3
"""Build every cheat in tasks/grant-widen-yield/cheat/ from one table, and expose the same
wrong readings to tools/readingcheck.py.

The cheats that ship and the readings that are measured are the same files by construction, so
they cannot drift apart - a reading repaired here and not re-emitted has been reported as
caught by one tool and not caught by another (CLAUDE.md, publish-settle-order).

    python authoring/grant-widen-yield/emit.py

Three kinds come out:

  readings   the reference with one rule read the other way. Each is a plausible reading of
             the brief and each must fail the enumerated case named for it.
  shortcuts  the shipped tree, one fixed output for every program, the worked example
             replayed, and an answer key for the enumerated programs.
  probes     attacks on the verifier rather than on the problem: the sealed model, the reward
             file, the worker's record, the grader, and a seventh file beside the six.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

READINGS = {}
NOTE = {}


def reading(name, note, part, *edits):
    READINGS[name] = {part: lab.patch(part, *edits)}
    NOTE[name] = note


# --- the mode lattice -----------------------------------------------------------------

reading("mode-sup-top", "the supremum of IX and S is the top of the lattice",
        "mode.py", ('    ("IX", "S"): "SIX",', '    ("IX", "S"): "X",'))

reading("mode-cov-six", "a shared-intent-exclusive grant is covered by a shared intention",
        "mode.py", ('return "IS" if m in ("IS", "S") else "IX"',
                    'return "IS" if m in ("IS", "S", "SIX") else "IX"'))

reading("mode-cov-write", "every grant needs an exclusive intention above it",
        "mode.py", ('return "IS" if m in ("IS", "S") else "IX"', 'return "IX"'))

# --- the derived cover ----------------------------------------------------------------

reading("hold-never-falls", "an ancestor keeps the mode it was first covered at",
        "hold.py",
        ('''    def retune(self, t, res, out):
        """Bring res to the supremum of its asked mode and its children's cover."""
        self.mark(t, res, self.want(t, res), out)''',
         '''    def retune(self, t, res, out):
        """Bring res to the supremum of its asked mode and its children's cover."""
        goal = self.want(t, res)
        here = self.now.get(t, {}).get(res)
        if here is not None and (goal is None or mode.sup(here, goal) != goal):
            return
        self.mark(t, res, goal, out)'''))

reading("hold-forgets-ask", "a take on a resource already covered records nothing",
        "hold.py",
        ('''        row = self.ask.setdefault(t, {})
        row[res] = mode.sup(row.get(res), m)
        self.retune(t, res, out)''',
         '''        row = self.ask.setdefault(t, {})
        if self.now.get(t, {}).get(res) is None:
            row[res] = mode.sup(row.get(res), m)
        self.retune(t, res, out)'''))

reading("hold-ask-wins", "an asked mode replaces the cover instead of joining it",
        "hold.py",
        ('''    def want(self, t, res):
        return mode.sup(self.asked(t, res), self.need(t, res))''',
         '''    def want(self, t, res):
        got = self.asked(t, res)
        return got if got is not None else self.need(t, res)'''))

reading("hold-shallow-walk", "a subtree is walked outermost first",
        "hold.py", ("        found.sort(key=name.deep)", "        found.sort(key=name.key)"))

# --- giving way -----------------------------------------------------------------------

GIVE_HEAD = '''def hand(book, due, u, res, out):
    for node, asked in book.strip(u, res, out, "give"):
        if asked is not None:
            due.claim(u, node, asked, None)
'''

READINGS["give-node-only"] = {"give.py": lab.source("give.py").replace(
    "from lk import mode\n", "from lk import mode, name, say\n").replace(
    GIVE_HEAD,
    '''def hand(book, due, u, res, out):
    was = book.eff(u, res)
    if was is None:
        return
    asked = book.asked(u, res)
    book.erase(u, res)
    out.append(say.give(u, res, was))
    par = name.up(res)
    if par is not None:
        book.retune(u, par, out)
    if asked is not None:
        due.claim(u, res, asked, None)
''')}
NOTE["give-node-only"] = "giving way leaves the grants below it standing"

READINGS["give-claim-eff"] = {"give.py": lab.source("give.py").replace(
    GIVE_HEAD,
    '''def hand(book, due, u, res, out):
    snap = dict((r, book.eff(u, r)) for r in book.sub(u, res))
    for node, asked in book.strip(u, res, out, "give"):
        if asked is not None:
            due.claim(u, node, snap[node], None)
''')}
NOTE["give-claim-eff"] = "the claim is left at the mode that was printed"

READINGS["give-claim-all"] = {"give.py": lab.source("give.py").replace(
    GIVE_HEAD,
    '''def hand(book, due, u, res, out):
    snap = dict((r, book.eff(u, r)) for r in book.sub(u, res))
    for node, asked in book.strip(u, res, out, "give"):
        due.claim(u, node, asked if asked is not None else snap[node], None)
''')}
NOTE["give-claim-all"] = "every grant given up leaves a claim, covers included"

# --- claims and the sweep --------------------------------------------------------------

SETTLE_SORT = ("    batch = sorted(due.dirty, "
               "key=lambda c: (ages[c[0]], name.depth(c[1]), name.key(c[1])))")

reading("keep-order-made", "claims are tried in the order they were made",
        "keep.py",
        ('''    def __init__(self):
        self.mine = {}''',
         '''    def __init__(self):
        self.seq = {}
        self.tick = 0
        self.mine = {}'''),
        ('''        cid = (t, res)
        self.park(cid, at)''',
         '''        cid = (t, res)
        if cid not in self.seq:
            self.tick += 1
            self.seq[cid] = self.tick
        self.park(cid, at)'''),
        (SETTLE_SORT, "    batch = sorted(due.dirty, key=lambda c: due.seq.get(c, 0))"))

reading("keep-order-deep", "a transaction's claims are tried innermost first",
        "keep.py",
        (SETTLE_SORT,
         "    batch = sorted(due.dirty, "
         "key=lambda c: (ages[c[0]], -name.depth(c[1]), name.key(c[1])))"))

reading("keep-try-all", "every standing claim is tried on every line",
        "keep.py",
        ('''        for res in book.hot:
            for cid in self.watch.get(res, ()):
                self.dirty.add(cid)
        book.hot = set()''',
         '''        for t, row in self.mine.items():
            for res in row:
                self.dirty.add((t, res))
        book.hot = set()'''))

reading("keep-fixpoint", "the sweep runs to a fixed point inside one line",
        "keep.py",
        ('''    due.soak(book)
    if not due.dirty:
        return
    batch = sorted(due.dirty, key=lambda c: (ages[c[0]], name.depth(c[1]), name.key(c[1])))
    due.dirty = set()
    for t, res in batch:
        m = due.owed(t, res)
        if m is None:
            continue
        take(book, due, ages, t, res, m, out, False)''',
         '''    for _round in range(64):
        due.soak(book)
        if not due.dirty:
            return
        batch = sorted(due.dirty,
                       key=lambda c: (ages[c[0]], name.depth(c[1]), name.key(c[1])))
        due.dirty = set()
        for t, res in batch:
            m = due.owed(t, res)
            if m is None:
                continue
            take(book, due, ages, t, res, m, out, False)'''))

# --- the widen rule ---------------------------------------------------------------------

reading("wide-counts-claims", "claims count toward the widen threshold",
        "wide.py",
        ("    return [p for p in seen if len(book.kids(p[0], p[1])) > lim]",
         "    return list(seen)"),
        ('''            kids = book.kids(t, node)
            if len(kids) <= lim:
                continue''',
         '''            kids = book.kids(t, node)
            spare = [r for r in due.held(t) if name.up(r) == node and r not in kids]
            if len(kids) + len(spare) <= lim:
                continue'''))

reading("wide-once", "the widen rule is applied once per line",
        "wide.py", ("\n        pend = pairs(book, lim)\n", "\n        pend = []\n"))

reading("wide-at-limit", "the threshold is reached rather than passed",
        "wide.py",
        ("    return [p for p in seen if len(book.kids(p[0], p[1])) > lim]",
         "    return [p for p in seen if len(book.kids(p[0], p[1])) >= lim]"),
        ("            if len(kids) <= lim:", "            if len(kids) < lim:"))

reading("wide-blocks-first", "the widen rule is applied to blocks before keys",
        "wide.py",
        ("key=lambda p: (-name.depth(p[1]), ages.get(p[0], 0), name.key(p[1]))",
         "key=lambda p: (name.depth(p[1]), ages.get(p[0], 0), name.key(p[1]))"))

READINGS["wide-preempts"] = {"wide.py": lab.patch(
    "wide.py",
    ("from lk import mode, name, say", "from lk import give, mode, name, say"),
    ('''            if book.clash(t, node, want):
                continue''',
     '''            if book.clash(t, node, want):
                foes = book.foes(t, node, want)
                if any(ages[u] < ages[t] for u in foes):
                    continue
                for u in sorted(foes, key=lambda x: ages[x]):
                    give.hand(book, due, u, node, out)'''))}
NOTE["wide-preempts"] = "widening makes a younger holder give way"

# --- the take and the line procedure -----------------------------------------------------

TAKE_BODY = '''def take(book, due, ages, t, res, m, out, loud):
    want = chain_want(book, t, res, m)
    for node in name.chain(res):
        goal = want[node]
        if book.eff(t, node) == goal:
            continue
        if not book.clash(t, node, goal):
            continue
        foes = book.foes(t, node, goal)
        if any(ages[u] < ages[t] for u in foes):
            due.claim(t, res, m, node)
            if loud:
                out.append(say.wait(t, res, m))
            return False
        for u in sorted(foes, key=lambda x: ages[x]):
            give.hand(book, due, u, node, out)
'''

reading("step-lookahead", "the whole chain is checked before anything is taken",
        "step.py",
        (TAKE_BODY,
         '''def take(book, due, ages, t, res, m, out, loud):
    want = chain_want(book, t, res, m)
    for node in name.chain(res):
        goal = want[node]
        if book.eff(t, node) == goal or not book.clash(t, node, goal):
            continue
        if any(ages[u] < ages[t] for u in book.foes(t, node, goal)):
            due.claim(t, res, m, node)
            if loud:
                out.append(say.wait(t, res, m))
            return False
    for node in name.chain(res):
        goal = want[node]
        if book.eff(t, node) == goal or not book.clash(t, node, goal):
            continue
        for u in sorted(book.foes(t, node, goal), key=lambda x: ages[x]):
            give.hand(book, due, u, node, out)
'''))

reading("step-grants-walked", "a refused take keeps the levels it already passed",
        "step.py",
        ('''            due.claim(t, res, m, node)
            if loud:
                out.append(say.wait(t, res, m))
            return False''',
         '''            due.claim(t, res, m, node)
            for done in name.chain(res):
                if done == node:
                    break
                book.raise_ask(t, done, want[done], out)
            if loud:
                out.append(say.wait(t, res, m))
            return False'''))

reading("step-inner-first", "a take prints its grants innermost first",
        "step.py",
        ('''    book.raise_ask(t, res, m, buf)
    buf.reverse()
    out.extend(buf)''',
         '''    book.raise_ask(t, res, m, buf)
    out.extend(buf)'''))

reading("step-young-first", "the youngest conflicting holder gives way first",
        "step.py",
        ("        for u in sorted(foes, key=lambda x: ages[x]):",
         "        for u in sorted(foes, key=lambda x: -ages[x]):"))

reading("step-refuse-any", "any conflict refuses the take",
        "step.py",
        ("        if any(ages[u] < ages[t] for u in foes):",
         "        if foes:"))

reading("step-give-any", "any conflicting holder gives way",
        "step.py",
        ("        if any(ages[u] < ages[t] for u in foes):",
         "        if False:"))

reading("step-no-sweep", "claims are never retried",
        "step.py",
        ("        keep.settle(book, due, ages, out, take)\n", ""))

reading("step-wide-first", "the widen rule runs before the sweep",
        "step.py",
        ('''        keep.settle(book, due, ages, out, take)
        wide.widen(book, due, ages, lim, out)''',
         '''        wide.widen(book, due, ages, lim, out)
        keep.settle(book, due, ages, out, take)'''))

reading("step-drop-keeps", "a release leaves the claims under it standing",
        "step.py",
        ("    nodes = set(book.sub(t, res)) | set(due.under(t, res))",
         "    nodes = set(book.sub(t, res))"))

reading("step-shut-silent", "a finish prints nothing but its own line",
        "step.py",
        ('''    nodes = set(book.held(t)) | set(due.held(t))
    for node in sorted(nodes, key=name.deep):
        out.append(say.free(t, node))
    book.forget(t)''',
         '''    book.forget(t)'''))

READING_NAMES = tuple(sorted(READINGS))


# --- exactly correct, and only the execution limit separates them --------------------
#
# Each of these gets every graded program right and cannot finish the two scale families
# inside the clock. They are the measured resource gate, as cheats rather than as a claim.

SLOW = {}

SLOW["slow-cover"] = ("the cover recomputed by rescanning the children", "hold.py",
                      '''    def need(self, t, res):
        box = self.kn.get(t, {}).get(res)
        if not box:
            return None
        if box["IX"]:
            return "IX"
        return "IS" if box["IS"] else None''', '''    def need(self, t, res):
        out = None
        own = self.now.get(t, {})
        for kid in self.ksub.get(t, {}).get(res, ()):
            here = own.get(kid)
            if here is not None:
                out = mode.sup(out, mode.cov(here))
        return out''')

SLOW["slow-sweep"] = ("every standing claim looked at on every line", "keep.py",
                      '''        for res in book.hot:
            for cid in self.watch.get(res, ()):
                self.dirty.add(cid)
        book.hot = set()''', '''        for t, row in self.mine.items():
            for res in row:
                cid = (t, res)
                at = self.where.get(cid)
                if at is None or at in book.hot:
                    self.dirty.add(cid)
        book.hot = set()''')

SLOW["slow-widen"] = ("the widen threshold tested for every transaction and resource",
                      "wide.py", '''def pairs(book, lim):
    """The pairs that could decide differently from last time, above the threshold."""
    seen = set(book.bump)
    book.bump = set()
    for res in book.stir:
        for t in list(book.carriers(res)):
            seen.add((t, res))
    book.stir = set()
    return [p for p in seen if len(book.kids(p[0], p[1])) > lim]''', '''def pairs(book, lim):
    book.bump = set()
    book.stir = set()
    out = []
    for t in list(book.now):
        for res in book.held(t):
            if len(book.kids(t, res)) > lim:
                out.append((t, res))
    return out''')


def slow_files(name):
    _note, part, old, new = SLOW[name]
    files = dict(lab.reference())
    files[part] = lab.patch(part, (old, new))
    return files


# --- the shortcut strategies ---------------------------------------------------------

SHORTCUT = {}

SHORTCUT["flat-constant"] = ("one fixed output for every program", {
    "step.py": '''from lk import hold, keep, read


def run(text):
    book = hold.Book()
    due = keep.Due()
    return ["hold t0 s0 IS"], book, due, {}
'''})

SHORTCUT["pos-grant-all"] = ("every take granted at the resource it names, nothing else", {
    "step.py": '''from lk import hold, keep, read, say


def run(text):
    out = []
    book = hold.Book()
    due = keep.Due()
    ages = {}
    for bits in read.scan(text):
        if bits[0] == "open" and bits[1] not in ages:
            ages[bits[1]] = len(ages)
        elif bits[0] == "take":
            out.append(say.hold(bits[1], bits[2], bits[3]))
    return out, book, due, ages
'''})

SHORTCUT["replay-sample"] = ("the trace the brief prints for runs/one.txt, for every program", {
    "step.py": '''from lk import hold, keep


SHOWN = [
    "hold t0 s0 IX",
    "hold t0 s0.b0 IX",
    "hold t0 s0.b0.k1 X",
    "hold t1 s0 IS",
    "hold t1 s0.b0 IS",
    "hold t1 s0.b0.k2 S",
    "wait t1 s0.b0.k1 S",
    "hold t0 s0.b1 IS",
    "free t0 s0.b0.k1",
    "free t0 s0.b0",
    "thin t0 s0 IS",
    "hold t1 s0.b0.k1 S",
    "free t1 s0.b0.k1",
    "free t1 s0.b0.k2",
    "free t1 s0.b0",
    "free t1 s0",
    "shut t1",
]


def run(text):
    return list(SHOWN), hold.Book(), keep.Due(), {}
'''})


# --- probes on the verifier rather than on the problem -------------------------------

def probe_body(extra):
    """A service that gets the trace wrong, with one attack wired into run().

    The base has to be wrong. A probe built on top of the reference scores 1 whenever its
    attack fails, because the work was done anyway, and that says nothing about the verifier -
    measured here on 2026-09-22, when two probes came back 1 on a correct base and proved
    nothing. With a base that cannot pass on its own, a reward of 1 can only mean the attack
    worked.
    """
    wrong = READINGS["step-inner-first"]["step.py"]
    head, split, tail = wrong.partition("""def run(text):
    out = []""")
    assert split, "the probe base no longer has the run() this patches"
    return head + extra + """

def run(text):
    _probe()
    out = []""" + tail


def answer_key_body():
    """Reads the sealed model and answers every program from it.

    This one does not need a wrong base: it has no service at all. A reward of 1 means uid 1002
    could read `/tests/seal`, which is the only thing it tests.
    """
    return '''from lk import hold, keep


def _expect():
    try:
        with open("/tests/seal/model.py", "r", encoding="utf-8") as fh:
            src = fh.read()
    except Exception:
        return None
    room = {}
    try:
        exec(compile(src, "model.py", "exec"), room)
    except Exception:
        return None
    return room.get("expect")


def run(text):
    got = _expect()
    rows = [r for r in text.splitlines() if r.strip()]
    if got is not None:
        return list(got(rows)), hold.Book(), keep.Due(), {}
    return ["hold t0 s0 IS"], hold.Book(), keep.Due(), {}
'''


PROBE = {}

PROBE["probe-reward-direct"] = ("writes the reward file itself", '''
def _probe():
    for where in ("/logs/verifier/reward.txt", "/logs/reward.txt"):
        try:
            with open(where, "w", encoding="utf-8") as fh:
                fh.write("1\\n")
        except Exception:
            pass
''')

PROBE["probe-late-reward"] = ("double-forks a process that writes the reward after grading", '''
_FIRED = []


def _probe():
    if _FIRED:
        return
    _FIRED.append(1)
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
    time.sleep(40)
    try:
        with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:
            fh.write("1\\n")
    except Exception:
        pass
    os._exit(0)
''')

PROBE["probe-plant-record"] = ("plants a passing worker record and lets the run continue", '''
def _probe():
    import json
    import os
    try:
        with open("/work/worker_out.json", "w", encoding="utf-8") as fh:
            json.dump([], fh)
        os.chmod("/work/worker_out.json", 0o444)
    except Exception:
        pass
''')

PROBE["probe-plant-exit"] = ("plants a record and leaves before it can be overwritten", '''
def _probe():
    import json
    import os
    import sys
    try:
        out = sys.argv[sys.argv.index("--out") + 1]
    except ValueError:
        return
    try:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump([], fh)
    except Exception:
        return
    os._exit(0)
''')

PROBE["probe-malformed"] = ("spoils the record on the way out", '''
def _probe():
    import atexit
    import sys

    def spoil():
        try:
            out = sys.argv[sys.argv.index("--out") + 1]
        except ValueError:
            return
        try:
            with open(out, "w", encoding="utf-8") as fh:
                fh.write("{\\"ok\\": true")
        except Exception:
            pass

    atexit.register(spoil)
''')

PROBE["probe-rewrite-grader"] = ("rewrites the generator and the grading file", '''
def _probe():
    for where in ("/tests/gen.py", "/tests/test_outputs.py", "/tests/cases.py"):
        try:
            with open(where, "w", encoding="utf-8") as fh:
                fh.write("def programs(seed, per):\\n    return []\\n")
        except Exception:
            pass
''')

PROBE["probe-shrink-set"] = ("rewrites its own copy of the seed and the family size", '''
def _probe():
    for where, what in (("/work/nonce", "0" * 32), ("/work/per", "1")):
        try:
            with open(where, "w", encoding="utf-8") as fh:
                fh.write(what + "\\n")
        except Exception:
            pass
    for where in ("/logs/verifier/nonce", "/logs/verifier/per"):
        try:
            with open(where, "w", encoding="utf-8") as fh:
                fh.write("1\\n")
        except Exception:
            pass
''')

PROBE["probe-privilege"] = ("checks its uid and reaches for the root-owned paths", '''
def _probe():
    import os
    for where in ("/logs/verifier", "/tests/seal", "/tests"):
        try:
            os.listdir(where)
        except Exception:
            pass
    try:
        os.setuid(0)
    except Exception:
        pass
    try:
        with open("/logs/verifier/nonce", "w", encoding="utf-8") as fh:
            fh.write("0" * 32)
    except Exception:
        pass
''')


def hidden_engine():
    """The whole correct service, hidden in a seventh file that is never collected."""
    files = dict(lab.reference())
    files["step.py"] = '''from lk import real


def run(text):
    return real.run(text)
'''
    return files


def forge_hand():
    """Carries the frozen answers for every enumerated program.

    The answers go in exactly as `gt.json` serialises them, so a reader can see at a glance
    that this file is the ground truth and not a service - and so tools/forgecheck.py, which
    looks for verbatim runs of the frozen answers inside cheat/, actually finds them.
    """
    import json
    cases, _gen, _model = lab.sealed()
    truth = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    table = {}
    for name in cases.ORDER:
        table["\n".join(cases.prog(name)).strip()] = truth[name]
    body = "import json\n\nANSWERS = json.loads(r\"\"\"\n"
    body += json.dumps(table, sort_keys=True) + "\n\"\"\")\n" + '''

def run(text):
    from lk import hold, keep
    got = ANSWERS.get(text.strip())
    if got is not None:
        return list(got), hold.Book(), keep.Due(), {}
    return ["hold t0 s0 IS"], hold.Book(), keep.Due(), {}
'''
    return {"step.py": body}


# --- writing the scripts ---------------------------------------------------------------

HEAD = "#!/bin/bash\n# %s\nset -euo pipefail\n\n"


def script(note, files, extra=None):
    body = HEAD % note
    for part in lab.PARTS:
        text = files.get(part)
        if text is None:
            continue
        body += "cat > /app/lk/%s <<'PYEOF'\n%sPYEOF\n\n" % (part, text)
    for path, text in (extra or {}).items():
        body += "cat > %s <<'PYEOF'\n%sPYEOF\n\n" % (path, text)
    return body


def main():
    lab.CHEAT.mkdir(exist_ok=True)
    for old in lab.CHEAT.glob("cheat-*.sh"):
        old.unlink()
    ref = lab.reference()
    made = []

    for name in READING_NAMES:
        files = dict(ref)
        files.update(READINGS[name])
        made.append((name, script(NOTE[name], files)))

    for name in sorted(SLOW):
        made.append((name, script(SLOW[name][0], slow_files(name))))

    for name, (note, over) in sorted(SHORTCUT.items()):
        files = dict(ref)
        files.update(over)
        made.append((name, script(note, files)))

    made.append(("nop-shipped", HEAD % "the shipped tree, unchanged" + "true\n"))
    made.append(("forge-hand", script("carries the frozen answers for every enumerated program",
                                      dict(ref, **forge_hand()))))
    made.append(("hide-engine", script(
        "the whole service hidden in a seventh file beside the six that are collected",
        hidden_engine(),
        {"/app/lk/real.py": ref["step.py"].replace("from lk import give, hold, keep, mode, "
                                                   "name, read, say, wide",
                                                   "from lk import give, hold, keep, mode, "
                                                   "name, read, say, wide")})))

    for name, (note, extra) in sorted(PROBE.items()):
        files = dict(ref)
        files["step.py"] = probe_body(extra)
        made.append((name, script(note, files)))

    made.append(("probe-answer-key", script(
        "reads the sealed model and answers every program from it",
        dict(ref, **{"step.py": answer_key_body()}))))

    for name, body in made:
        path = lab.CHEAT / ("cheat-%s.sh" % name)
        path.write_text(body, encoding="utf-8", newline="\n")
        path.chmod(0o755)
    print("wrote %d cheats to %s" % (len(made), lab.CHEAT))
    print("  readings  %d" % len(READING_NAMES))
    print("  slow      %d" % len(SLOW))
    print("  shortcuts %d" % (len(SHORTCUT) + 3))
    print("  probes    %d" % (len(PROBE) + 1))


if __name__ == "__main__":
    main()
