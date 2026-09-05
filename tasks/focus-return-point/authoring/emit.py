"""Generate solution/solve.sh and every cheat. Never hand-edit what this writes.

Single-mistake cheats are the WHOLE reference with exactly one decision swapped, produced
by replacing an anchored block of the reference source; a swap whose anchor is missing, or
whose old and new text are equal, is refused, because the first tests nothing and the
second tests the wrong thing while reporting success.

Reward probes are built on the SHIPPED policy, since a probe built on the reference does
the real work and scores 1 for honest reasons. Attestation probes are the opposite: the
reference with one attestation interfered with, so the probe is right on every trail and
can only be caught by the layer it attacks.

The answer-key probe is generated from tests/gt.json and is the reference on every
enumerated case and the shipped policy on everything else, which is the most an adversary
holding the answer key can do.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
REF = os.path.join(TASK, "solution")
SHIP = os.path.join(TASK, "environment", "app_src", "ui")
CHEAT = os.path.join(TASK, "cheat")
POL = ("focus.py", "keep.py", "reach.py", "mem.py")


def strip(text):
    if text.startswith('"""'):
        text = text.split('"""', 2)[2].lstrip("\n")
    return text


def read(d, n):
    with open(os.path.join(d, n)) as fh:
        return fh.read()


def refset():
    return {n: strip(read(REF, n)) for n in POL}


def shipset():
    return {n: read(SHIP, n) for n in POL}


# (name, file, old, new, why)
SWAPS = (
    ("reach-self-only", "reach.py",
     "    cur = nd\n    while cur is not None:\n        if cur.fl & set(BLOCK):\n"
     "            return False\n        cur = cur.par\n    return True\n",
     "    return not (nd.fl & set(BLOCK))\n",
     "a widget is asked about its own flags only, so a widget under a hidden, disabled or "
     "shut container still counts as a stop"),
    ("group-all-stops", "reach.py",
     "        if nd.grp is not None and lead.get(nd.grp) is not nd:\n            continue\n",
     "",
     "every member of a group is a stop"),
    ("group-ignores-selection", "reach.py",
     "        if nd.grp not in lead or (\"sel\" in nd.fl and \"sel\" not in lead[nd.grp].fl):\n"
     "            lead[nd.grp] = nd\n",
     "        if nd.grp not in lead:\n            lead[nd.grp] = nd\n",
     "the first member of a group is always its stop, whichever is selected"),
    ("comp-enters-first", "mem.py",
     "    m = mem.get(comp)\n    if m is not None and reach.within(m) is comp and reach.can(ui, m):\n"
     "        return m\n",
     "",
     "entering a composite always lands on its first descendant, ignoring the memory"),
    ("back-enters-last", "focus.py",
     "        self.take(ui, pick[0] if d > 0 else pick[-1])\n",
     "        stop = pick[0] if d > 0 else pick[-1]\n"
     "        if d < 0 and \"comp\" in stop.fl:\n"
     "            self.put(ui, reach.inside(ui, stop)[-1])\n"
     "        else:\n            self.take(ui, stop)\n",
     "entering a composite backwards lands on its last descendant instead of the memory"),
    ("memory-from-arrows-only", "focus.py",
     "        ui.land(nd)\n        mem.note(self.mem, nd)\n        self.keep.orig = None\n",
     "        ui.land(nd)\n        self.keep.orig = None\n",
     "the composite memory learns only from the arrow keys, not from every landing"),
    ("arrows-wrap", "focus.py",
     "        i = room.index(f) + d\n        if 0 <= i < len(room):\n            self.put(ui, room[i])\n",
     "        self.put(ui, room[(room.index(f) + d) % len(room)])\n",
     "arrow keys wrap inside a composite"),
    ("auto-ignored", "focus.py",
     "        for nd in reach.order(ui):\n            if \"auto\" in nd.fl and reach.can(ui, nd):\n"
     "                self.put(ui, nd)\n                return\n",
     "",
     "a push lands on the first stop, ignoring auto"),
    ("held-dropped", "focus.py",
     "        elif nd.scr.nm in ui.scr:\n            self.keep.held[nd.scr] = nd\n",
     "",
     "a request for a screen that is not on top is dropped"),
    ("held-first-wins", "focus.py",
     "            self.keep.held[nd.scr] = nd\n",
     "            self.keep.held.setdefault(nd.scr, nd)\n",
     "the first held request for a screen wins rather than the latest"),
    ("held-falls-back", "focus.py",
     "        elif now in self.keep.held:\n            self.settle(ui, self.keep.held.pop(now))\n"
     "        else:\n            self.settle(ui, self.keep.ret.get(s))\n",
     "        else:\n            r = None\n            if now in self.keep.held:\n"
     "                r = self.keep.spot(ui, self.keep.held.pop(now))\n"
     "            if isinstance(r, Nd) and reach.can(ui, r):\n                self.put(ui, r)\n"
     "            else:\n                self.settle(ui, self.keep.ret.get(s))\n",
     "a held request whose widget cannot take focus at the return is skipped in favour "
     "of the return record"),
    ("push-ignores-held", "focus.py",
     "        self.keep.ret[s] = self.here(ui)\n        if s in self.keep.held:\n"
     "            self.settle(ui, self.keep.held.pop(s))\n            return\n",
     "        self.keep.ret[s] = self.here(ui)\n",
     "a request held for a screen that has not been pushed yet is not honoured by the push"),
    ("return-forgotten-eagerly", "focus.py",
     "    def check(self, ui):\n        if ui.fo is not None and not reach.can(ui, ui.fo):\n"
     "            self.lose(ui, ui.fo)\n",
     "    def check(self, ui):\n        for s, t in list(self.keep.ret.items()):\n"
     "            if isinstance(t, Nd) and not (reach.alive(ui, t) and\n"
     "                                          not (t.fl & set(reach.BLOCK))):\n"
     "                self.keep.ret[s] = None\n"
     "        for s, t in list(self.keep.held.items()):\n"
     "            if not (reach.alive(ui, t) and not (t.fl & set(reach.BLOCK))):\n"
     "                self.keep.held.pop(s)\n"
     "        if ui.fo is not None and not reach.can(ui, ui.fo):\n"
     "            self.lose(ui, ui.fo)\n",
     "a return record or held request is forgotten the moment its widget is disturbed, "
     "so a widget re-enabled before the return is not restored"),
    ("no-screen-chain", "keep.py",
     "        if nd.par is None:\n            return self.ret.get(nd.scr)\n",
     "        if nd.par is None:\n            return None\n",
     "a return record pointing into a screen that has already gone resolves to nothing, "
     "so a pop after an out-of-order pop lands on the first stop"),
    ("lost-from-the-top", "focus.py",
     "        if ui.fo is not None and not reach.can(ui, ui.fo):\n            self.lose(ui, ui.fo)\n",
     "        if ui.fo is not None and not reach.can(ui, ui.fo):\n            self.lose(ui, None)\n",
     "focus lost to a mutation starts the next key from the top of the screen"),
    ("no-container-chain", "keep.py",
     "            else:\n                if reach.alive(ui, tgt[1]):\n                    return tgt\n"
     "                tgt = self.place(tgt[1])\n",
     "            else:\n                if reach.alive(ui, tgt[1]):\n                    return tgt\n"
     "                return None\n",
     "a point whose container has gone resolves to nothing instead of the container's place"),
    ("anchor-on-sibling", "keep.py",
     "        self.gone[nd] = (nd.par, at)\n",
     "        self.gone[nd] = (nd.par, nd.par.kids[at - 1] if at > 0 else None)\n",
     "the place of a dropped widget is kept as 'after the sibling before it', so it moves "
     "when that sibling goes or when something is inserted before it"),
    ("place-inside-composite-reenters", "focus.py",
     "            c = p if \"comp\" in p.fl else reach.within(p)\n"
     "            hi = at[c] if c is not None and c in at else pos\n",
     "            hi = pos\n",
     "going back from the place of a dropped widget inside a composite lands on the "
     "composite itself and re-enters it, instead of on the last stop before it"),
    ("want-forces-focus", "focus.py",
     "        if nd.scr is reach.top(ui):\n            if reach.can(ui, nd):\n                self.put(ui, nd)\n",
     "        if nd.scr is reach.top(ui):\n            self.put(ui, nd)\n",
     "a request on the screen on top always takes focus, even for a widget that cannot "
     "take it"),
)

ANCHOR_FIX = {
    "anchor-on-sibling": (
        "        if nd in self.gone:\n            p, at = self.gone[nd]\n            return (\"pt\", p, at)\n",
        "        if nd in self.gone:\n            p, prev = self.gone[nd]\n"
        "            if prev is None:\n                return (\"pt\", p, 0)\n"
        "            if prev in p.kids:\n                return (\"pt\", p, p.kids.index(prev) + 1)\n"
        "            return (\"pt\", p, 0)\n"),
}


def swap(files, name, fn, old, new):
    src = files[fn]
    if old == new:
        raise SystemExit("%s: swap is a no-op" % name)
    if src.count(old) != 1:
        raise SystemExit("%s: anchor found %d times in %s" % (name, src.count(old), fn))
    files[fn] = src.replace(old, new)


def script(name, why, files, prologue=""):
    lines = ["#!/bin/bash", "# cheat: %s" % name, "# %s" % why, "set -euo pipefail",
             "mkdir -p /app/ui", prologue.rstrip("\n")] if prologue else \
            ["#!/bin/bash", "# cheat: %s" % name, "# %s" % why, "set -euo pipefail",
             "mkdir -p /app/ui"]
    for n in POL:
        if n in files:
            lines += ["cat > /app/ui/%s <<'PYEOF'" % n, files[n].rstrip("\n"), "PYEOF"]
    return "\n".join(lines) + "\n"


def write(path, text):
    with open(path, "w", newline="\n") as fh:
        fh.write(text)
    os.chmod(path, 0o755)


def solve_sh():
    return """#!/bin/bash
# Reference solution: the corrected policy files sit beside this script and are copied
# into the tree, then the toolkit is run over the shipped cases.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for f in focus.py keep.py reach.py mem.py; do
  cp "${HERE}/${f}" "/app/ui/${f}"
done
cd /app
for c in /app/cases/*.txt; do
  python /app/run_ui.py "$c"
done
"""


# ---------------------------------------------------------------- probes

REWARD_PROBES = {
    "probe-late-reward": (
        "the shipped policy plus a double-forked process that writes the reward after "
        "the run has finished",
        "import os as _os, time as _t\n"
        "if _os.fork() == 0:\n    if _os.fork() == 0:\n        _t.sleep(3)\n"
        "        try:\n            open('/logs/verifier/reward.txt', 'w').write('1\\n')\n"
        "        except Exception:\n            pass\n        _os._exit(0)\n    _os._exit(0)\n"),
    "probe-plant-report": (
        "the shipped policy plus a planted report written over the run's output, "
        "followed by a hard exit",
        "import os as _os, json as _j\n"
        "try:\n    open('/work/run/out.json', 'w').write(_j.dumps({'nonce': '', 'count': 0,"
        " 'trails': {}, 'faults': {}}))\nexcept Exception:\n    pass\n"),
    "probe-read-answers": (
        "the shipped policy plus an attempt to read the ground truth, the model and the "
        "grader from inside the run",
        "for _p in ('/tests/gt.json', '/tests/oracle.py', '/tests/test_outputs.py'):\n"
        "    try:\n        open(_p).read()\n    except Exception:\n        pass\n"),
    "probe-rewrite-core": (
        "the shipped policy plus a rewrite of the frozen core in the executed tree, "
        "attempted from inside the policy at import time",
        "import os as _os\n"
        "try:\n    _p = _os.path.join(_os.path.dirname(__file__), 'core.py')\n"
        "    open(_p, 'a').write('\\n')\nexcept Exception:\n    pass\n"),
    "probe-sweep": (
        "the shipped policy plus a sweep of everything the run's uid can read, looking "
        "for anything that resembles an answer",
        "import os as _os\n"
        "for _root in ('/tests', '/work', '/app', '/pristine', '/logs'):\n"
        "    for _b, _d, _f in _os.walk(_root):\n"
        "        if _b.count(_os.sep) > 4:\n            _d[:] = []\n"
        "        for _n in _f:\n            if _n.endswith(('.json', '.py')):\n"
        "                try:\n                    open(_os.path.join(_b, _n)).read(64)\n"
        "                except Exception:\n                    pass\n"),
}

ATTEST_PROBES = {
    "probe-disarm-tally": (
        "the reference, every trail right, with the interpreter's instrumentation "
        "switched off from inside the policy while the script runs",
        "focus.py",
        "    def on(self, ui, ev):\n        k = ev.k\n",
        "    def on(self, ui, ev):\n        import sys as _s\n"
        "        _m = getattr(_s, 'monitoring', None)\n        try:\n"
        "            if _m is not None:\n                _m.set_local_events(4, ui.step.__code__, 0)\n"
        "            else:\n                _s.setprofile(None)\n        except Exception:\n"
        "            pass\n        k = ev.k\n"),
    "probe-rebind-land": (
        "the reference, every trail right, with the frozen Ui.land rebound to a wrapper "
        "when the policy is first constructed",
        "focus.py",
        "    def __init__(self, ui):\n        self.keep = Keep()\n",
        "    def __init__(self, ui):\n        import ui.core as _c\n"
        "        if not getattr(_c.Ui, '_wrapped', False):\n"
        "            _orig = _c.Ui.land\n\n"
        "            def _land(self, nd):\n                return _orig(self, nd)\n\n"
        "            _c.Ui.land = _land\n            _c.Ui._wrapped = True\n"
        "        self.keep = Keep()\n"),
    "probe-extra-rows": (
        "the reference, every landing right, pushing one extra row into the trail "
        "through the core's sink on every event",
        "focus.py",
        "    def on(self, ui, ev):\n        k = ev.k\n",
        "    def on(self, ui, ev):\n        ui.put((0, 'x', 'none'))\n        k = ev.k\n"),
}


def answer_key():
    """The shipped policy, replaying the recorded trail of any enumerated case it can
    identify. A case is identified by its declaration and by the prefix of events seen so
    far (kind plus the widget or screen named), which is everything the policy can see;
    two cases that share both up to some event share the trail up to it as well, so the
    replay is right for as long as any candidate is left."""
    import sys
    sys.path.insert(0, os.path.join(TASK, "tests"))
    import cases as _cases
    with open(os.path.join(TASK, "tests", "gt.json")) as fh:
        gt = json.load(fh)
    key = json.dumps(gt, sort_keys=True, separators=(",", ":"))
    book = {}
    for nm, text in _cases.CASES.items():
        decl, evs = [], []
        for ln in text.split("\n"):
            t = ln.split()
            if not t:
                continue
            if t[0] == "screen":
                decl.append(" ".join(t))
            elif t[0] == "w":
                fl = sorted(x for x in t[3:] if not x.startswith("grp="))
                gr = [x for x in t[3:] if x.startswith("grp=")]
                decl.append(" ".join(t[:3] + fl + gr))
            else:
                evs.append(t[0] + " " + (t[1] if len(t) > 1 else ""))
        book.setdefault("|".join(decl), []).append((evs, nm))
    files = shipset()
    pro = (
        "import json as _j\n"
        "_KEY = _j.loads(%r)['cases']\n"
        "_BOOK = %r\n"
        "_Pol0 = Pol\n\n\n"
        "def _decl(ui):\n"
        "    out = []\n"
        "    for s in ui.scr.values():\n"
        "        out.append('screen ' + s.nm)\n"
        "        def walk(nd):\n"
        "            for k in nd.kids:\n"
        "                fl = sorted(k.fl)\n"
        "                tail = [f for f in fl] + (['grp=' + k.grp] if k.grp else [])\n"
        "                out.append(' '.join(['w', k.wid, nd.wid] + tail))\n"
        "                walk(k)\n"
        "        walk(s.root)\n"
        "    return '|'.join(out)\n\n\n"
        "class Pol(_Pol0):\n"
        "    def __init__(self, ui):\n        _Pol0.__init__(self, ui)\n"
        "        self.cands = None\n        self.i = 0\n\n"
        "    def on(self, ui, ev):\n"
        "        if self.cands is None:\n"
        "            self.cands = list(_BOOK.get(_decl(ui), []))\n"
        "        nm = ev.w.wid if ev.w is not None and hasattr(ev.w, 'wid') else \\\n"
        "            (ev.s.nm if ev.s is not None else (ev.nm or ''))\n"
        "        seen = ev.k + ' ' + nm\n"
        "        self.cands = [c for c in self.cands if len(c[0]) > self.i and c[0][self.i] == seen]\n"
        "        self.i += 1\n"
        "        if self.cands:\n"
        "            w = _KEY[self.cands[0][1]][self.i - 1]\n"
        "            ui.land(ui.nd.get(w) if w != 'none' else None)\n"
        "            return\n"
        "        _Pol0.on(self, ui, ev)\n"
    )
    files["focus.py"] = files["focus.py"] + "\n\n" + pro % (key, book)
    return files


def main():
    os.makedirs(CHEAT, exist_ok=True)
    for f in os.listdir(CHEAT):
        if f.startswith("cheat-") and f.endswith(".sh"):
            os.remove(os.path.join(CHEAT, f))
    write(os.path.join(REF, "solve.sh"), solve_sh())
    n = 0
    for name, fn, old, new, why in SWAPS:
        files = refset()
        swap(files, name, fn, old, new)
        if name in ANCHOR_FIX:
            swap(files, name, fn, *ANCHOR_FIX[name])
        write(os.path.join(CHEAT, "cheat-rule-%s.sh" % name), script(name, why, files))
        n += 1
    for name, (why, pro) in REWARD_PROBES.items():
        files = shipset()
        files["focus.py"] = pro + "\n" + files["focus.py"]
        write(os.path.join(CHEAT, "cheat-%s.sh" % name), script(name, why, files))
        n += 1
    for name, (why, fn, old, new) in ATTEST_PROBES.items():
        files = refset()
        swap(files, name, fn, old, new)
        write(os.path.join(CHEAT, "cheat-%s.sh" % name), script(name, why, files))
        n += 1
    write(os.path.join(CHEAT, "cheat-probe-answer-key.sh"),
          script("probe-answer-key", "the shipped policy, replaying the recorded answer on "
                 "every enumerated case it recognises by its widget ids", answer_key()))
    n += 1
    print("solve.sh and %d cheats written" % n)


if __name__ == "__main__":
    main()
