#!/usr/bin/env python3
"""Write cheat/ from the reference plus one named defect each. Never ships.

A cheat is a whole submission, so every script writes all five files. A wrong reading is the
reference with exactly that reading changed, so it is caught by what it gets wrong rather than
by the time it takes - all but memoized recursion, which is also too slow and meets the clock
first in the full verifier; cheat_report.py checks its case in process. The forgery and most
probes sit on the SHIPPED resolver instead, which fails honestly, so a 1 could only come from
the attack: a probe built on correct work scores 1 for an honest reason and proves nothing. The
three probes that do carry correct work - the sealed model if the seal can be read, a resolver
in a sixth file, one in the driver - carry it where the verifier never runs it, so each scores 1
only if the piece of isolation it targets is missing. The slow cheats are exactly correct and
exist to show the clock is what stops them. Every substitution asserts how many times it fired -
a patch that matches nothing ships the reference under a cheat's name and scores 0 for the wrong
reason.

Run after any change to solution/, and before readings.py or cheat_report.py.

    python3 -u authoring/glob-route-hide/emit.py
"""
import hashlib
import json
import pathlib
import stat
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

SOL = lab.SOL
OUT = lab.TASK / "cheat"
PARTS = lab.PARTS

MADE = []
READINGS = {}
KIND = {}
CATCH = {}
COMMENT = {}

GROUPS = (
    ("reading", "Wrong readings",
     "The reference with one rule read another way, each caught by what it prints: first by the "
     "hand case named beside it, and again by the generated programs. One, `memo-rec`, is also "
     "too slow for the large programs, so in the full verifier the clock stops it first."),
    ("shortcut", "Shortcuts",
     "Strategies that skip the resolution: a constant, the first candidate by position, the "
     "worked example replayed."),
    ("forgery", "Forgery",
     "Everything the agent could collect about the hand cases, printed back verbatim. The "
     "generated programs are drawn after the agent's container is gone, so it has nothing to "
     "print for them."),
    ("probe", "Isolation probes",
     "Each goes after one piece of the isolation, and the six that can observe it write what they "
     "saw to `/work/probe.log`. "
     "The three that carry a correct resolver - the sealed model if the seal can be read, a "
     "resolver in a sixth file, one pasted into the driver - would score 1 if that piece were "
     "missing. The rest sit on the shipped resolver, which fails honestly, so a 1 could only come "
     "from the attack. The answer key and the malformed output both finish inside the clock, so "
     "that what they return reaches the grader. `probe-privilege` and "
     "`probe-late-reward` need a second uid and a real fork to mean anything; the host emulation "
     "has both, running test.sh as root so that it drops the worker to uid 1002 with setpriv, as "
     "it does in the container."),
    ("slow", "Exact and too slow",
     "Correct on every program, and stopped by the 60 second clock or the 2 GB limit on the "
     "large ones. These are the structures the task is about not using."),
)


def base():
    return {p: (SOL / p).read_text(encoding="utf-8") for p in PARTS}


def shipped():
    return {p: (lab.SRC / "fe" / p).read_text(encoding="utf-8") for p in PARTS}


def sub(files, name, old, new, times=1):
    txt = files[name]
    hits = txt.count(old)
    assert hits == times, "%s: %d hits (wanted %d) for %r" % (name, hits, times, old[:80])
    files[name] = txt.replace(old, new)


def write(name, comment, files, kind, catch=None, extra=None):
    """Emit cheat/cheat-<name>.sh writing all five files (and any extra ones)."""
    KIND[name] = kind
    COMMENT[name] = comment
    if catch:
        CATCH[name] = catch
    if kind == "reading":
        READINGS[name] = dict(files)
    body = ["#!/bin/bash", "# " + comment, "set -euo pipefail", ""]
    for part in PARTS:
        body.append("cat > /app/fe/%s <<'PYEOF'" % part)
        body.append(files[part].rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    for path, text in sorted((extra or {}).items()):
        body.append("mkdir -p %s" % pathlib.PurePosixPath(path).parent)
        body.append("cat > %s <<'PYEOF'" % path)
        body.append(text.rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    text = "\n".join(body) + "\n"
    assert "\r" not in text
    dest = OUT / ("cheat-%s.sh" % name)
    dest.write_text(text, encoding="utf-8", newline="\n")
    dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    MADE.append(name)


# --- visibility -------------------------------------------------------------------------------

def pub_only():
    f = base()
    sub(f, "vis.py", "        out[t] = cs[t if t < c else c]", "        out[t] = cs[0]")
    write("pub-only", "a line passes on only what is public; private lines never leave their module",
          f, "reading", "vis-child-sees")


def string_prefix():
    f = base()
    sub(f, "vis.py", "    c = cpd(src, dst)\n",
        "    segs = src.split(\".\")\n    c = 0\n    for d in range(1, len(segs) + 1):\n"
        "        if dst.startswith(\".\".join(segs[:d])):\n            c = d\n"
        "        else:\n            break\n")
    write("string-prefix", "a module counts as inside another when its path merely starts with "
          "the other's, dots or not", f, "reading", "vis-sibling-prefix")


def no_narrow():
    f = base()
    sub(f, "vis.py", "    for t in range(lv, top + 1):\n", "    for t in range(0, top + 1):\n")
    write("no-narrow", "an import passes a candidate on as widely as it came, whatever the line's "
          "own visibility", f, "reading", "narrow-private-glob")


def glob_no_narrow():
    f = base()
    sub(f, "glob.py", "        got = vis.take(cs, ln.src, path, vis.lvl(ln, path), top)",
        "        got = vis.take(cs, ln.src, path, 0, top)")
    write("glob-no-narrow", "a private glob passes things on as widely as they came",
          f, "reading", "narrow-private-glob")


def explicit_no_narrow():
    f = base()
    sub(f, "own.py", "        got = vis.take(cs, ln.src, path, vis.lvl(ln, path), top)",
        "        got = vis.take(cs, ln.src, path, 0, top)")
    write("explicit-no-narrow", "a private explicit import passes its candidates on as widely as "
          "they came", f, "reading", "narrow-explicit")


def pub_widens():
    f = base()
    sub(f, "vis.py", "        out[t] = cs[t if t < c else c]",
        "        out[t] = cs[c] if lv == 0 else cs[t if t < c else c]")
    write("pub-widens", "a public line makes whatever it passes on public", f, "reading",
          "narrow-keeps-item")


def explicit_ignores_vis():
    f = base()
    sub(f, "own.py", "        got = vis.take(cs, ln.src, path, vis.lvl(ln, path), top)",
        "        lv = vis.lvl(ln, path)\n"
        "        got = [cs[-1] if t >= lv else 0 for t in range(top + 1)]")
    write("explicit-ignores-vis", "an explicit import takes whatever the source holds, seen or not",
          f, "reading", "explicit-denied")


def first_route():
    f = base()
    sub(f, "fix.py", "        glob.gives(prog, tab, path, new)\n",
        "        glob.gives(prog, tab, path, new)\n"
        "        held = tab.cs[path][-1]\n"
        "        new = [o | (n & ~held) for o, n in zip(tab.cs[path], new)]\n")
    write("first-route", "a candidate keeps the visibility of the first route that delivered it",
          f, "reading", "widen-two-routes")


# --- hiding -----------------------------------------------------------------------------------

def seen_hides():
    f = base()
    sub(f, "fix.py", '    __slots__ = ("bit", "ids", "nmask", "mine", "cs", "top")',
        '    __slots__ = ("bit", "ids", "nmask", "mine", "cs", "top", "pubmine")')
    sub(f, "fix.py", "        self.top = {}\n", "        self.top = {}\n        self.pubmine = {}\n")
    sub(f, "fix.py", "        tab.mine[path] = mask\n",
        "        tab.mine[path] = mask\n        pm = 0\n"
        "        for ln in own.lines(prog, path):\n            if ln.pb:\n"
        "                pm |= tab.nmask.get(ln.nm if ln.k == \"item\" else ln.bn, 0)\n"
        "        tab.pubmine[path] = pm\n")
    sub(f, "glob.py", "    keep = ~tab.mine[path]\n",
        "    keep = ~tab.mine[path]\n    low = ~tab.pubmine[path]\n")
    sub(f, "glob.py", "                out[t] |= got[t] & keep",
        "                out[t] |= got[t] & (keep if t == top else low)")
    write("seen-hides", "an own binding hides the globs only from readers that can see it",
          f, "reading", "hide-own-private")


def broken_falls():
    f = base()
    sub(f, "fix.py", "def settle(prog):\n    tab = Tab()\n",
        "def settle(prog):\n    skip = set()\n    tab = None\n    for _ in range(8):\n"
        "        tab = _settle(prog, skip)\n        nxt = set()\n"
        "        for path in prog.order:\n            items = {ln.nm for ln in own.lines(prog, path)"
        " if ln.k == \"item\"}\n"
        "            for name in own.names(prog, path) - items:\n"
        "                if not tab.cs[path][tab.top[path]] & tab.nmask.get(name, 0):\n"
        "                    nxt.add((path, name))\n"
        "        if nxt == skip:\n            break\n        skip = nxt\n    return tab\n\n\n"
        "def _settle(prog, skip):\n    tab = Tab()\n")
    sub(f, "fix.py", "        for name in own.names(prog, path):\n            mask |= tab.nmask.get(name, 0)\n",
        "        for name in own.names(prog, path):\n            if (path, name) not in skip:\n"
        "                mask |= tab.nmask.get(name, 0)\n")
    write("broken-falls", "an own import that finds nothing does not hide the globs", f, "reading",
          "hide-broken")


def gated_hides():
    f = base()
    sub(f, "own.py",
        '    return {ln.nm if ln.k == "item" else ln.bn for ln in lines(prog, path)}',
        '    md = prog.mods.get(path)\n    if md is None:\n        return set()\n'
        '    return {ln.nm if ln.k == "item" else ln.bn for ln in md.lns if ln.k in ("item", "use")}')
    write("gated-hides", "an own line whose flag is off still hides the globs", f, "reading",
          "hide-gated-off")


def glob_all_names():
    f = base()
    sub(f, "glob.py", "    keep = ~tab.mine[path]\n", "    keep = -1\n")
    write("glob-all-names", "globs give every name, including the ones the module binds itself",
          f, "reading", "glob-unbound-name")


def missing_unbound():
    f = base()
    sub(f, "own.py",
        '    return {ln.nm if ln.k == "item" else ln.bn for ln in lines(prog, path)}',
        '    return {ln.nm if ln.k == "item" else ln.bn for ln in lines(prog, path)\n'
        '            if ln.k == "item" or ln.src in prog.mods}')
    write("missing-unbound", "an import from a module the program does not declare binds nothing",
          f, "reading", "missing-module")


def rename_binds_both():
    f = base()
    sub(f, "own.py",
        '    return {ln.nm if ln.k == "item" else ln.bn for ln in lines(prog, path)}',
        '    out = {ln.nm if ln.k == "item" else ln.bn for ln in lines(prog, path)}\n'
        '    return out | {ln.nm for ln in lines(prog, path) if ln.k == "use"}')
    write("rename-binds-both", "an import with a rename binds the old name as well as the new",
          f, "reading", "rename-hides-bound")


def rename_keeps_name():
    f = base()
    sub(f, "own.py",
        '    return {ln.nm if ln.k == "item" else ln.bn for ln in lines(prog, path)}',
        '    return {ln.nm for ln in lines(prog, path)}')
    sub(f, "own.py", "            if x and ln.bn != ln.nm:\n                x = carry(tab, x, ln.nm, ln.bn)\n", "")
    write("rename-keeps-name", "an import with a rename binds and gives under the old name",
          f, "reading", "rename-chain")


def use_no_hide():
    f = base()
    sub(f, "glob.py", "    keep = ~tab.mine[path]\n",
        "    keep = 0\n    for ln in own.lines(prog, path):\n        if ln.k == \"item\":\n"
        "            keep |= tab.nmask.get(ln.nm, 0)\n    keep = ~keep\n")
    sub(f, "glob.py", "from fe import flag, vis\n", "from fe import flag, own, vis\n")
    write("use-no-hide", "only item lines hide the globs; an explicit import does not", f,
          "reading", "hide-own-private")


def display_held_name():
    f = base()
    sub(f, "say.py", '        return "%s %s %s" % (path, name, item(prog, got[0]))',
        '        return "%s %s %s.%s" % (path, name, prog.items[got[0]][0], name)')
    write("display-held-name", "a renamed item is printed under the name it is held by", f,
          "reading", "rename-chain")


# --- presence ---------------------------------------------------------------------------------

def glob_ignores_flags():
    f = base()
    sub(f, "glob.py", '    return [ln for ln in md.lns if ln.k == "glob" and flag.live(ln, prog.on)]',
        '    return [ln for ln in md.lns if ln.k == "glob"]')
    write("glob-ignores-flags", "a glob exists whatever its flag says", f, "reading",
          "widen-gated-arm")


def item_ignores_flags():
    f = base()
    sub(f, "own.py",
        '    return [ln for ln in md.lns if ln.k in ("item", "use") and flag.live(ln, prog.on)]',
        '    return [ln for ln in md.lns if ln.k == "item" or (ln.k == "use" and flag.live(ln, prog.on))]')
    write("item-ignores-flags", "an item line exists whatever its flag says", f, "reading",
          "gate-negated")


def negation_ignored():
    f = base()
    sub(f, "own.py",
        '    return [ln for ln in md.lns if ln.k in ("item", "use") and flag.live(ln, prog.on)]',
        '    return [ln for ln in md.lns if ln.k in ("item", "use") and (ln.cf is None or ln.cf in prog.on)]')
    sub(f, "glob.py", '    return [ln for ln in md.lns if ln.k == "glob" and flag.live(ln, prog.on)]',
        '    return [ln for ln in md.lns if ln.k == "glob" and (ln.cf is None or ln.cf in prog.on)]')
    write("negation-ignored", "`if !F` is read as `if F`", f, "reading", "gate-negated")


# --- candidates and outcomes ------------------------------------------------------------------

SAY_ROUTES = '''"""Wrong reading: an item offered by two of the module's globs is two candidates."""
from fe import glob, own, vis


def line(prog, tab, i):
    path, ln = prog.refs[i]
    name = ln.nm
    top = tab.top[path]
    if name in own.names(prog, path):
        have = tab.cs[path][top] & tab.nmask.get(name, 0)
        got = sorted(ix for ix in tab.ids.get(name, ()) if have >> tab.bit[(ix, name)] & 1)
    else:
        got = []
        for g in glob.lines(prog, path):
            cs = tab.cs.get(g.src)
            if cs is None:
                continue
            x = vis.take(cs, g.src, path, vis.lvl(g, path), top)[top] & tab.nmask.get(name, 0)
            got += [ix for ix in tab.ids.get(name, ()) if x >> tab.bit[(ix, name)] & 1]
        got.sort()
    if len(got) == 1:
        return "%s %s %s" % (path, name, item(prog, got[0]))
    if not got:
        why = "broken" if name in own.names(prog, path) else "unresolved"
        return "%s %s %s" % (path, name, why)
    return "%s %s ambiguous %s" % (path, name, " ".join(item(prog, ix) for ix in got))


def item(prog, ix):
    path, ln = prog.items[ix]
    return "%s.%s" % (path, ln.nm)
'''

SAY_DROP = SAY_ROUTES.replace(
    '"""Wrong reading: an item offered by two of the module\'s globs is two candidates."""',
    '"""Wrong reading: a glob gives nothing for a name that is ambiguous where it comes from."""'
).replace(
    "            got += [ix for ix in tab.ids.get(name, ()) if x >> tab.bit[(ix, name)] & 1]\n"
    "        got.sort()\n",
    "            one = [ix for ix in tab.ids.get(name, ()) if x >> tab.bit[(ix, name)] & 1]\n"
    "            if len(one) == 1 and one[0] not in got:\n"
    "                got += one\n"
    "        got.sort()\n")


def route_dupes():
    f = base()
    f["say.py"] = SAY_ROUTES
    write("route-dupes", "an item reached through two of the module's globs is two candidates",
          f, "reading", "route-same-item")


def drop_ambiguous():
    f = base()
    assert SAY_DROP != SAY_ROUTES
    f["say.py"] = SAY_DROP
    write("drop-ambiguous", "a glob gives nothing for a name that is ambiguous where it comes from",
          f, "reading", "amb-carried")


def explicit_amb_broken():
    f = base()
    sub(f, "own.py", "        mk = tab.nmask.get(ln.nm, 0)\n",
        "        mk = tab.nmask.get(ln.nm, 0)\n        seen = got[top] & mk\n"
        "        if seen & (seen - 1):\n            continue\n")
    write("explicit-amb-broken", "an explicit import of an ambiguous name gives nothing", f,
          "reading", "amb-explicit")


def found_order():
    f = base()
    sub(f, "say.py", "        got.sort()\n",
        "        got.sort()\n        got = arrival(prog, tab, path, name, got)\n")
    f["say.py"] += '''

def arrival(prog, tab, path, name, got):
    from fe import glob, vis
    top = tab.top[path]
    order = []
    for ln in own.lines(prog, path) + glob.lines(prog, path):
        if ln.k == "item":
            if ln.nm == name and ln.ix in got and ln.ix not in order:
                order.append(ln.ix)
            continue
        cs = tab.cs.get(ln.src)
        if cs is None:
            continue
        x = vis.take(cs, ln.src, path, vis.lvl(ln, path), top)[top]
        want = ln.nm if ln.k == "use" else name
        for ix in got:
            b = tab.bit.get((ix, want))
            if b is not None and x >> b & 1 and ix not in order:
                order.append(ix)
    return order + [ix for ix in got if ix not in order]
'''
    write("found-order", "candidates are listed in the order the module's lines reach them",
          f, "reading", "amb-two-globs")


def alpha_order():
    f = base()
    sub(f, "say.py", '" ".join(item(prog, ix) for ix in got)',
        '" ".join(sorted(item(prog, ix) for ix in got))')
    write("alpha-order", "candidates are listed alphabetically", f, "reading", "amb-file-order")


def dup_items_merged():
    f = base()
    sub(f, "say.py", "        got.sort()\n",
        "        got.sort()\n        keep, shown = [], set()\n        for ix in got:\n"
        "            if item(prog, ix) not in shown:\n"
        "                shown.add(item(prog, ix))\n                keep.append(ix)\n"
        "        got = keep\n")
    write("dup-items-merged", "two item lines with one module and name count as one candidate",
          f, "reading", "dup-item-lines")


def no_broken():
    f = base()
    sub(f, "say.py", '        why = "broken" if name in own.names(prog, path) else "unresolved"',
        '        why = "unresolved"')
    write("no-broken", "a name the module binds itself but gets nothing for prints unresolved",
          f, "reading", "hide-broken")


def inherit():
    f = base()
    sub(f, "say.py", "    if len(got) == 1:\n",
        "    walk = path\n    while not got and \".\" in walk and name not in own.names(prog, path):\n"
        "        walk = walk.rpartition(\".\")[0]\n        if walk in tab.cs:\n"
        "            up = tab.cs[walk][tab.top[walk]] & tab.nmask.get(name, 0)\n"
        "            got = sorted(ix for ix in tab.ids.get(name, ()) if up >> tab.bit[(ix, name)] & 1)\n"
        "    if len(got) == 1:\n")
    write("inherit", "a module that gets nothing for a name falls back to its parent's names",
          f, "reading", "vis-no-inherit")


def scc_share():
    f = base()
    sub(f, "fix.py", "    return tab\n",
        "    share(prog, tab, readers)\n    return tab\n\n\n"
        "def share(prog, tab, readers):\n"
        "    import sys\n    sys.setrecursionlimit(1 << 16)\n"
        "    index, low, stack, on, comps, n = {}, {}, [], set(), [], [0]\n"
        "    deps = {p: [] for p in prog.order}\n"
        "    for src, rs in readers.items():\n        for r in rs:\n            deps[r].append(src)\n"
        "    def visit(v):\n        index[v] = low[v] = n[0]\n        n[0] += 1\n"
        "        stack.append(v)\n        on.add(v)\n        for w in deps[v]:\n"
        "            if w not in index:\n                visit(w)\n                low[v] = min(low[v], low[w])\n"
        "            elif w in on:\n                low[v] = min(low[v], index[w])\n"
        "        if low[v] == index[v]:\n            comp = []\n            while True:\n"
        "                w = stack.pop()\n                on.discard(w)\n                comp.append(w)\n"
        "                if w == v:\n                    break\n            comps.append(comp)\n"
        "    for p in prog.order:\n        if p not in index:\n            visit(p)\n"
        "    for comp in comps:\n        if len(comp) < 2:\n            continue\n"
        "        union = 0\n        for p in comp:\n            union |= tab.cs[p][tab.top[p]]\n"
        "        for p in comp:\n            tab.cs[p][tab.top[p]] |= union & ~tab.mine[p]\n")
    write("scc-share", "every member of a cycle of globs holds the same candidates", f, "reading",
          "cycle-cut")


MEMO_FIX = '''"""Wrong reading: memoized recursion over (module, name), an in-progress pair giving nothing."""
import sys

from fe import glob, own, vis

sys.setrecursionlimit(1 << 16)


class Tab:
    pass


def settle(prog):
    tab = Tab()
    memo, busy = {}, set()
    mine = {p: own.names(prog, p) for p in prog.order}

    def has(path, name):
        key = (path, name)
        if key in memo:
            return memo[key]
        if key in busy or path not in prog.mods:
            return {}
        busy.add(key)
        got = {}

        def put(ix, d):
            if ix not in got or d < got[ix]:
                got[ix] = d

        def through(ln, src, want):
            c = vis.cpd(src, path)
            lv = vis.lvl(ln, path)
            for ix, d in has(src, want).items():
                if d <= c:
                    put(ix, d if d > lv else lv)

        if name in mine[path]:
            for ln in own.lines(prog, path):
                if ln.k == "item" and ln.nm == name:
                    put(ln.ix, vis.lvl(ln, path))
                elif ln.k == "use" and ln.bn == name:
                    through(ln, ln.src, ln.nm)
        else:
            for ln in glob.lines(prog, path):
                through(ln, ln.src, name)
        busy.discard(key)
        memo[key] = got
        return got

    tab.has = has
    tab.mine = mine
    return tab
'''

MEMO_SAY = '''def line(prog, tab, i):
    path, ln = prog.refs[i]
    name = ln.nm
    got = sorted(tab.has(path, name))
    shown = ["%s.%s" % (prog.items[ix][0], prog.items[ix][1].nm) for ix in got]
    if len(shown) == 1:
        return "%s %s %s" % (path, name, shown[0])
    if not shown:
        return "%s %s %s" % (path, name, "broken" if name in tab.mine[path] else "unresolved")
    return "%s %s ambiguous %s" % (path, name, " ".join(shown))
'''


def memo_rec():
    f = base()
    f["fix.py"] = MEMO_FIX
    f["say.py"] = MEMO_SAY
    write("memo-rec", "memoized recursion over (module, name); a pair already in progress gives "
          "nothing", f, "reading", "cycle-fed")


# --- shortcut strategies ----------------------------------------------------------------------

def const_unresolved():
    f = shipped()
    f["fix.py"] = "def settle(prog):\n    return None\n"
    f["say.py"] = ("def line(prog, tab, i):\n    path, ln = prog.refs[i]\n"
                   "    return \"%s %s unresolved\" % (path, ln.nm)\n")
    write("const-unresolved", "shortcut: every reference prints unresolved, the commonest outcome",
          f, "shortcut")


def pos_first():
    f = base()
    sub(f, "say.py", "        got.sort()\n", "        got.sort()\n        got = got[:1]\n")
    write("pos-first", "shortcut: an ambiguity is settled on its first candidate in file order",
          f, "shortcut")


def pos_first_glob():
    f = base()
    sub(f, "glob.py", "    for ln in lines(prog, path):\n", "    for ln in lines(prog, path)[:1]:\n")
    write("pos-first-glob", "shortcut: a module reads only its first glob", f, "shortcut")


def replay_example():
    f = shipped()
    f["say.py"] = ("def line(prog, tab, i):\n"
                   "    return \"app emit ambiguous log.emit net.emit\"\n")
    write("replay-example", "shortcut: the brief's quoted line printed for every reference",
          f, "shortcut")


# --- forgery ----------------------------------------------------------------------------------

def canon_of(prog):
    """A key for a parsed program, computed the same way at emit time and inside the cheat."""
    parts = [" ".join(sorted(prog.on))]
    for path in prog.order:
        parts.append("mod " + path)
        for ln in prog.mods[path].lns:
            parts.append("|".join(str(x) for x in (ln.k, ln.nm, ln.src, ln.bn, ln.pb, ln.cf, ln.cv)))
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


CANON_SRC = '''def canon_of(prog):
    parts = [" ".join(sorted(prog.on))]
    for path in prog.order:
        parts.append("mod " + path)
        for ln in prog.mods[path].lns:
            parts.append("|".join(str(x) for x in (ln.k, ln.nm, ln.src, ln.bn, ln.pb, ln.cf, ln.cv)))
    return hashlib.sha256("\\n".join(parts).encode("utf-8")).hexdigest()
'''


LARGE_CUT = '''    if len(prog.mods) > 1000:
        return ("known", ["%s %s unresolved" % (p, ln.nm) for p, ln in prog.refs])
'''

KNOWN_LINE = ("def line(prog, tab, i):\n    if isinstance(tab, tuple):\n        return tab[1][i]\n"
              "    path, ln = prog.refs[i]\n")


def forge_hand():
    """Carries tests/seal/gt.json verbatim, with a map from each parsed hand program to its case.

    Anything else goes to the shipped resolver, except a program too large for it, which prints
    unresolved at once: the run has to finish inside the clock, or the trial would show the
    clock stopping the forgery rather than the generated programs.
    """
    cases, _gen, _model = lab.sealed()
    gt = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    here = lab.tree()
    lab.inproc(here)
    rd = sys.modules["fe.rd"]
    which = {}
    for name in cases.ORDER:
        prog = rd.load("\n".join(cases.prog(name)) + "\n")
        which[canon_of(prog)] = name
    lab.drop(here)
    f = shipped()
    head = ("import hashlib\n\nANSWERS = %s\nWHICH = %s\n\n\n%s\n\ndef settle(prog):\n"
            "    case = WHICH.get(canon_of(prog))\n    if case is not None:\n"
            "        return (\"known\", ANSWERS[case])\n"
            % (json.dumps(gt, sort_keys=True), json.dumps(which, sort_keys=True), CANON_SRC))
    sub(f, "fix.py", "def settle(prog):\n", head + LARGE_CUT)
    sub(f, "say.py", "def line(prog, tab, i):\n    path, ln = prog.refs[i]\n", KNOWN_LINE)
    write("forge-hand", "forgery: tests/seal/gt.json carried verbatim, every hand answer returned "
          "for its program, the shipped resolver for other small programs and unresolved for "
          "large ones", f, "forgery")


# --- isolation probes (most on the shipped resolver) -----------------------------------------

PROBE_HEAD = '''import os


def note(msg):
    try:
        with open("/work/probe.log", "a") as fh:
            fh.write(msg + "\\n")
    except OSError:
        pass


def attempt(label, fn):
    try:
        fn()
        note("%s OK" % label)
    except Exception as exc:
        note("%s %s" % (label, type(exc).__name__))


'''


KEY_HEAD = '''import sys


def note(msg):
    try:
        with open("/work/probe.log", "a") as fh:
            fh.write(msg + "\\n")
    except OSError:
        pass


def _key():
    try:
        open("/tests/seal/gt.json").read()
        note("gt OK")
    except Exception as exc:
        note("gt %s" % type(exc).__name__)
    sys.path.insert(0, "/tests/seal")
    try:
        import model
    except Exception as exc:
        note("model %s" % type(exc).__name__)
        return None
    note("model OK")
    return model


def _text(prog):
    out = ["flags " + " ".join(sorted(prog.on))]
    for path in prog.order:
        out.append("mod " + path)
        for ln in prog.mods[path].lns:
            if ln.k == "ref":
                out.append("ref " + ln.nm)
                continue
            if ln.k == "item":
                body = "item " + ln.nm
            elif ln.k == "glob":
                body = "use %s::*" % ln.src
            else:
                body = "use %s::%s" % (ln.src, ln.nm) + ("" if ln.bn == ln.nm else " as " + ln.bn)
            cond = "" if ln.cf is None else " if %s%s" % ("" if ln.cv else "!", ln.cf)
            out.append(("pub " if ln.pb else "") + body + cond)
    return out


_model = []


def settle(prog):
    if not _model:
        _model.append(_key())
    if _model[0] is not None:
        return ("known", _model[0].expect(_text(prog)))
'''


def answer_key():
    """The sealed model as the resolver, if the seal can be read: scores 1 exactly when it leaks.

    Otherwise the shipped resolver, cut short on the large programs so the run reaches the
    grader and the trial shows the hand cases failing rather than the clock.
    """
    f = shipped()
    sub(f, "fix.py", "def settle(prog):\n", KEY_HEAD + LARGE_CUT)
    sub(f, "say.py", "def line(prog, tab, i):\n    path, ln = prog.refs[i]\n", KNOWN_LINE)
    write("probe-answer-key", "probe: reads the frozen answers and imports the sealed model, and "
          "prints the model's lines for every program if the import works", f, "probe")


def probe(name, comment, body):
    f = shipped()
    f["fix.py"] = f["fix.py"].replace(
        "def settle(prog):\n",
        PROBE_HEAD + "_armed = [False]\n\n\ndef settle(prog):\n    if not _armed[0]:\n"
        "        _armed[0] = True\n" + "".join("        " + ln + "\n" for ln in body.splitlines()),
        1)
    assert "_armed" in f["fix.py"]
    write(name, comment, f, "probe")


def probes():
    probe("probe-late-reward", "probe: a double-forked survivor keeps writing 1 into the reward "
          "long after the worker returns",
          "import time\n"
          "if os.fork() == 0:\n"
          "    os.setsid()\n"
          "    if os.fork() == 0:\n"
          "        for _ in range(120):\n"
          "            try:\n"
          "                open('/logs/verifier/reward.txt', 'w').write('1')\n"
          "            except OSError:\n"
          "                pass\n"
          "            time.sleep(0.5)\n"
          "        os._exit(0)\n"
          "    os._exit(0)\n"
          "note('survivor launched')")
    probe("probe-privilege", "probe: runs as which uid, and can it write the reward, the seal or the exam",
          "note('uid %d' % os.getuid())\n"
          "attempt('reward', lambda: open('/logs/verifier/reward.txt', 'w').write('1'))\n"
          "attempt('seal', lambda: open('/tests/seal/gt.json', 'a').write(''))\n"
          "attempt('exam', lambda: open('/exam/index.json', 'a').write(''))\n"
          "attempt('grader', lambda: open('/tests/test_outputs.py', 'a').write(''))")
    answer_key()
    probe("probe-rewrite-exam", "probe: rewrites every exam program into one with no references",
          "import glob as _g\n"
          "for _p in _g.glob('/exam/*.txt'):\n"
          "    attempt('rewrite ' + os.path.basename(_p), lambda p=_p: open(p, 'w').write('flags\\n'))")
    probe("probe-plant-exit", "probe: plants a record claiming the shipped output for every exam "
          "program, then ends the worker cleanly before it can overwrite the plant",
          "import json as _j, sys as _s\n"
          "_idx = _j.load(open('/exam/index.json'))\n"
          "_recs = []\n"
          "for _e in _idx:\n"
          "    _t = open('/exam/' + _e['file']).read()\n"
          "    import hashlib as _h\n"
          "    _l = _t.rstrip('\\n').split('\\n')\n"
          "    _recs.append({'name': _e['name'], 'sig': _h.sha256('\\n'.join(_l).encode()).hexdigest(),"
          " 'got': ['x'], 'err': None})\n"
          "open('/work/worker_out.json', 'w').write(_j.dumps(_recs))\n"
          "note('planted %d records' % len(_recs))\n"
          "os._exit(0)")
    probe("probe-crash-worker", "probe: plants a passing-looking record and kills the worker "
          "with a non-zero status",
          "open('/work/worker_out.json', 'w').write('[]')\n"
          "note('planted empty record')\n"
          "os._exit(3)")
    # the shipped settle only hands back a closure and this line never calls it, so the run
    # finishes and the dicts reach the grader, whose parsing is what this probe is for
    f = shipped()
    f["say.py"] = "def line(prog, tab, i):\n    return {'resolved': True, 'i': i}\n"
    write("probe-malformed", "probe: every reference returns a dict instead of a line", f, "probe")
    # the whole reference engine hidden in a file beside the five, which is never collected
    f = base()
    engine = f["fix.py"]
    f["fix.py"] = "from fe.core import settle, Tab  # noqa: F401\n"
    write("probe-uncollected-file", "probe: the resolver lives in a sixth file beside the five, "
          "which the verifier never collects", f, "probe", extra={"/app/fe/core.py": engine})
    # the whole reference engine inside the frozen driver, the five files left as shipped
    ref = base()
    drv = (lab.SRC / "run_res.py").read_text(encoding="utf-8")
    inject = ("import types\nimport fe\n\n_SRC = %s\n\n"
              "for _n in (\"vis\", \"own\", \"glob\", \"fix\", \"say\"):\n"
              "    _m = types.ModuleType(\"fe.\" + _n)\n    sys.modules[\"fe.\" + _n] = _m\n"
              "    setattr(fe, _n, _m)\n"
              "for _n in (\"vis\", \"own\", \"glob\", \"fix\", \"say\"):\n"
              "    exec(compile(_SRC[_n], \"fe/%%s.py\" %% _n, \"exec\"), sys.modules[\"fe.\" + _n].__dict__)\n\n"
              % json.dumps({p[:-3]: ref[p] for p in PARTS}))
    assert drv.count("from fe import fix, rd, say\n") == 1
    drv = drv.replace("from fe import fix, rd, say\n", inject + "from fe import fix, rd, say\n", 1)
    write("probe-engine-in-driver", "probe: a correct resolver pasted into the driver, which the "
          "verifier replaces with its own copy", shipped(), "probe", extra={"/app/run_res.py": drv})


# --- exactly correct, and too slow ------------------------------------------------------------

def slow_variants():
    d = HERE / "slow"
    for sub_dir, comment in (("pairs", "exact: one fixed point over (module, name) pairs, "
                              "values as item-to-region maps"),
                             ("tables", "exact: a full table per module, one dict per module "
                              "holding every binding it has"),
                             ("lifo", "exact: sets over bindings, strongly connected components "
                              "in order, but a last-in-first-out worklist inside each"),
                             ("sweep", "exact and light on memory: one sweep of the module graph "
                              "for each referenced name")):
        files = {p: (d / sub_dir / p).read_text(encoding="utf-8") for p in PARTS}
        write("slow-" + sub_dir, comment, files, "slow")


READING_BUILDERS = [
    pub_only, string_prefix, no_narrow, glob_no_narrow, explicit_no_narrow, pub_widens,
    explicit_ignores_vis, first_route, seen_hides, broken_falls, gated_hides, glob_all_names,
    missing_unbound, rename_binds_both, rename_keeps_name, use_no_hide, display_held_name,
    glob_ignores_flags,
    item_ignores_flags, negation_ignored, route_dupes, drop_ambiguous, explicit_amb_broken,
    found_order, alpha_order, dup_items_merged, no_broken, inherit, scc_share, memo_rec,
]


def readme():
    """cheat/README.md, from the same calls that wrote the scripts, so it cannot drift."""
    out = ["# Cheat attempts", "",
           "Each script writes all five resolution files into `/app/fe/`, which is the only place "
           "the verifier collects submitted code from, and each must score 0. They are generated "
           "by `authoring/glob-route-hide/emit.py` from the reference or the shipped resolver with "
           "one asserted change each, and this list is written by the same run.", ""]
    for kind, title, text in GROUPS:
        names = [n for n in MADE if KIND[n] == kind]
        assert names, "no cheats of kind %s" % kind
        out += ["## %s (%d)" % (title, len(names)), "", text, ""]
        for n in names:
            line = "- `cheat-%s.sh` - %s" % (n, COMMENT[n])
            if n in CATCH:
                line += " (caught by `%s`)" % CATCH[n]
            out.append(line)
        out.append("")
    assert sum(1 for n in MADE if KIND[n] in {g[0] for g in GROUPS}) == len(MADE)
    text = "\n".join(out).rstrip("\n") + "\n"
    assert "\r" not in text
    (OUT / "README.md").write_text(text, encoding="utf-8", newline="\n")


def main():
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("cheat-*.sh"):
        old.unlink()
    for build in READING_BUILDERS:
        build()
    for build in (const_unresolved, pos_first, pos_first_glob, replay_example, forge_hand,
                  probes, slow_variants):
        build()
    readme()
    kinds = {}
    for name in MADE:
        kinds[KIND[name]] = kinds.get(KIND[name], 0) + 1
    print("wrote %d cheats: %s" % (len(MADE), ", ".join("%d %s" % (v, k) for k, v in
                                                        sorted(kinds.items()))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
