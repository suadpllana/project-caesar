#!/usr/bin/env python3
"""Every wrong reading a solver is likely to hold, as the reference with one thing changed.

Each reading is built by substitutions that must each fire exactly as often as stated: a
substitution that matches nothing ships the reference under a reading's name, which is how a
cheat once scored 0 for the wrong reason (CLAUDE.md, reach-pair-sweep). The same builders feed
emit.py, so the cheats that ship and the readings measured here cannot drift apart.

    python3 readings.py            which enumerated case catches each reading, and how often
                                   each generated family does
    python3 readings.py --cases    the enumerated half only
"""
import pathlib
import sys

import lab

PARTS = lab.PARTS


def base():
    return {p: (lab.SOL / p).read_text(encoding="utf-8") for p in PARTS}


def sub(files, part, old, new, times=1):
    text = files[part]
    n = text.count(old)
    if n != times:
        raise AssertionError("%s: expected %d match(es) of %r, found %d" % (part, times, old[:60], n))
    files[part] = text.replace(old, new)


# The decorator collects (fn, why, case) here; the public READINGS below is {name: files},
# because tools/readingcheck.py reads that shape. WHY and CASE carry the rest.
_SPECS = {}


def reading(name, why, case):
    def wrap(fn):
        _SPECS[name] = (fn, why, case)
        return fn
    return wrap


# --- the distance and the passes ---------------------------------------------------------

@reading("dist-view-top", "distance measured from the top of the view, band ignored", "settle-cycle")
def _(f):
    sub(f, "hold.py", "chain.append((x, lay.top(v, x) - u))", "chain.append((x, lay.top(v, x) - s))")
    sub(f, "hold.py", "want = clamp(lay.top(v, x) - d - band)", "want = clamp(lay.top(v, x) - d)")


@reading("one-pass", "a single pass, no settling", "settle-stick")
def _(f):
    sub(f, "hold.py", "    for _ in range(4):\n", "    for _ in range(1):\n")


@reading("cap-three", "three passes at most", "settle-fourth")
def _(f):
    sub(f, "hold.py", "    for _ in range(4):\n", "    for _ in range(3):\n")


@reading("cap-five", "five passes at most", "settle-drift")
def _(f):
    sub(f, "hold.py", "    for _ in range(4):\n", "    for _ in range(5):\n")


@reading("last-offset", "after four passes the last offset, not the smallest", "settle-cycle")
def _(f):
    sub(f, "hold.py", "    best = min(want for want, _x in seen)\n",
        "    best = seen[-1][0]\n")


@reading("min-last-holder", "the smallest offset, but printed with the last pass's holder",
         "settle-holder")
def _(f):
    sub(f, "hold.py", "    for want, x in seen:\n        if want == best:\n            return want, x.id\n",
        "    return best, seen[-1][1].id\n")


@reading("clamp-last", "passes run unclamped and only the result is clamped", "clamp-pass")
def _(f):
    sub(f, "hold.py", "        want = clamp(lay.top(v, x) - d - band)\n        if want == s:\n            return s, x.id\n",
        "        want = lay.top(v, x) - d - band\n        if want == s:\n            return clamp(s), x.id\n")
    sub(f, "hold.py", "        if held is None:\n            return clamp(s), \"none\"\n",
        "        if held is None:\n            return clamp(s), \"none\"\n", 1)
    sub(f, "hold.py", "            return want, x.id\n    raise", "            return clamp(want), x.id\n    raise")


@reading("clamp-first", "the old offset is clamped to the new range before the first pass",
         "clamp-start")
def _(f):
    sub(f, "hold.py", "    s = v.s\n    seen = []\n", "    s = clamp(v.s)\n    seen = []\n")


# --- the holder across the frame -----------------------------------------------------------

@reading("fresh-pick", "a disqualified holder is replaced by a fresh pick, with no adjustment",
         "fall-dropped")
def _(f):
    sub(f, "hold.py", "    s = v.s\n    seen = []\n",
        "    if not qualifies(v, v.chain[0][0], v.s):\n"
        "        got = pick.first(v, v.s, stick.band(v, v.s))\n"
        "        return clamp(v.s), \"none\" if got is None else got.id\n"
        "    s = v.s\n    seen = []\n")


@reading("holder-distance", "the container takes over at the holder's distance", "fall-dropped")
def _(f):
    sub(f, "hold.py", "                held = (x, d)\n", "                held = (x, v.chain[0][1])\n")


@reading("eligible-once", "the holder is resolved once, at the old offset, for every pass",
         "turn-back")
def _(f):
    sub(f, "hold.py", "    s = v.s\n    seen = []\n    for _ in range(4):\n        band = stick.band(v, s)\n        held = None\n        for x, d in v.chain:\n            if qualifies(v, x, s):\n                held = (x, d)\n                break\n",
        "    s = v.s\n    seen = []\n    held = None\n    for x, d in v.chain:\n        if qualifies(v, x, s):\n            held = (x, d)\n            break\n    for _ in range(4):\n        band = stick.band(v, s)\n")


@reading("pick-after", "the holder is picked on the tree after the edits", "hold-ordinary")
def _(f):
    sub(f, "hold.py", "    lay.sync(v)\n    most = lay.span(v)\n",
        "    lay.sync(v)\n    before(v)\n    most = lay.span(v)\n")


@reading("none-old-offset", "a pass with no qualifying box ends the frame at the old offset",
         "none-late")
def _(f):
    sub(f, "hold.py", "        if held is None:\n            return clamp(s), \"none\"\n",
        "        if held is None:\n            return clamp(v.s), \"none\"\n")


@reading("stuck-contents-ok", "only a stuck box itself is disqualified, not what is inside it",
         "stuck-inside")
def _(f):
    sub(f, "stick.py", "        if x.pin is not None and drawn(v, x, s) is not None:\n            return True\n        x = x.par\n",
        "        if x.pin is not None and drawn(v, x, s) is not None:\n            return True\n        x = None\n")


@reading("hidden-qualifies", "a box under a shut row still qualifies", "fall-hidden")
def _(f):
    sub(f, "hold.py", "    return lay.laid(x) and x.hh > 0 and not stick.stuck_in(v, x, s)",
        "    return not x.gone and not x.lift and x.hh > 0 and not stick.stuck_in(v, x, s)")


@reading("empty-qualifies", "a box of no height still qualifies", "fall-empty")
def _(f):
    sub(f, "hold.py", "    return lay.laid(x) and x.hh > 0 and not stick.stuck_in(v, x, s)",
        "    return lay.laid(x) and not stick.stuck_in(v, x, s)")


# --- sticking and the band ---------------------------------------------------------------

@reading("band-sum", "the band is the sum of the stuck headers' heights", "band-lowest")
def _(f):
    sub(f, "stick.py", "            if r is not None and r + c.hh - s > best:\n                best = r + c.hh - s\n",
        "            if r is not None:\n                best += c.hh\n")


@reading("no-push", "a stuck header ignores the end of its section", "stick-push")
def _(f):
    sub(f, "stick.py", "    r = min(s + b.pin, lay.end_of_section(v, b) - b.hh)\n",
        "    r = s + b.pin\n")


@reading("stick-at-line", "a header sticks once the stick line reaches its top", "stick-strict")
def _(f):
    sub(f, "stick.py", "    if r > lay.top(v, b):\n", "    if r >= lay.top(v, b):\n")


@reading("band-no-floor", "a header pushed above the view makes the band negative", "band-floor")
def _(f):
    old_band = f["stick.py"][f["stick.py"].index("def band(v, s):"):]
    sub(f, "stick.py", old_band, """def band(v, s):
    best = None
    for b in v.box.values():
        if b.pin is None or not lay.laid(b) or b.hh <= 0:
            continue
        r = drawn(v, b, s)
        if r is not None and (best is None or r + b.hh - s > best):
            best = r + b.hh - s
    return 0 if best is None else best
""")


@reading("empty-header-sticks", "a pinned box of no height sticks", "stick-none")
def _(f):
    sub(f, "stick.py", "    if b.pin is None or b.hh <= 0:\n        return None\n",
        "    if b.pin is None:\n        return None\n")
    sub(f, "stick.py", "            if c.lift or c.hh <= 0:\n                continue\n",
        "            if c.lift:\n                continue\n")


# --- the pick ----------------------------------------------------------------------------

@reading("pick-whole-view", "the pick looks at the whole view, band ignored", "pick-below")
def _(f):
    sub(f, "hold.py", "    got = pick.first(v, s, band)\n", "    got = pick.first(v, s, 0)\n")


@reading("pick-whole-only", "only a box wholly below the band is picked", "pick-partial")
def _(f):
    sub(f, "pick.py", "                if got is not None:\n                    return got\n            return c\n",
        "                if got is not None:\n                    return got\n            continue\n")


@reading("pick-zero", "a box of no height can be picked", "pick-skips")
def _(f):
    sub(f, "pick.py", "            if c.cf == 0 or c.live:\n                continue\n",
        "            if c.lift or c.live:\n                continue\n")


@reading("pick-live", "a live box can be picked", "pick-skips")
def _(f):
    sub(f, "pick.py", "            if c.cf == 0 or c.live:\n                continue\n",
        "            if c.cf == 0:\n                continue\n")


@reading("pick-at-zero", "nothing is held at offset zero", "top-held")
def _(f):
    sub(f, "hold.py", "    if v.chain is None:\n        return clamp(v.s), \"none\"\n",
        "    if v.chain is None:\n        return clamp(v.s), \"none\"\n"
        "    if v.s == 0:\n        return 0, v.chain[0][0].id\n")


# --- the switches ------------------------------------------------------------------------

@reading("live-ignored", "edits inside live boxes are held like any other", "off-live")
def _(f):
    sub(f, "hold.py", "        elif not live and lay.in_live(b):\n            live = True\n",
        "        elif False:\n            live = True\n")


@reading("live-new-ignored", "adding a live box does not count", "off-live-add")
def _(f):
    sub(f, "hold.py", "        elif not live and lay.in_live(b):\n",
        "        elif not live and kind != \"add\" and lay.in_live(b):\n")


@reading("live-first", "a live edit outranks an explicit scroll", "off-both")
def _(f):
    sub(f, "hold.py", "    if ask is not None:\n        return clamp(ask), \"off scroll\"\n    if live:\n        return clamp(v.s), \"off live\"\n",
        "    if live:\n        return clamp(v.s), \"off live\"\n    if ask is not None:\n        return clamp(ask), \"off scroll\"\n")


@reading("scroll-first", "the first explicit scroll of a frame counts", "off-scroll")
def _(f):
    sub(f, "hold.py", "        if kind == \"to\":\n            ask = arg\n",
        "        if kind == \"to\":\n            ask = arg if ask is None else ask\n")


@reading("pick-touch", "a box ending exactly on the band line still shows", "pick-edges")
def _(f):
    sub(f, "pick.py", "        j = bisect_right(ends, u - start)\n", "        j = bisect_right(ends, u - start - 1)\n")


@reading("pick-straddle", "a band covering the view still lets a box straddle it", "pick-empty")
def _(f):
    sub(f, "pick.py", "    if u >= w:\n        return None\n", "")


@reading("lifted-qualifies", "a lifted box still qualifies", "fall-lifted")
def _(f):
    sub(f, "hold.py", "    return lay.laid(x) and x.hh > 0 and not stick.stuck_in(v, x, s)",
        "    return (lay.laid(x) or (x.lift and not x.gone)) and x.hh > 0 and not stick.stuck_in(v, x, s)")


# The same names as a literal list, because tools/tracecheck.py reads reading names statically
# and the decorator table above is only filled at import. The assertion keeps the two in step.
EDITS = [
    "dist-view-top",
    "one-pass",
    "cap-three",
    "cap-five",
    "last-offset",
    "min-last-holder",
    "clamp-last",
    "clamp-first",
    "fresh-pick",
    "holder-distance",
    "eligible-once",
    "pick-after",
    "none-old-offset",
    "stuck-contents-ok",
    "hidden-qualifies",
    "empty-qualifies",
    "band-sum",
    "no-push",
    "stick-at-line",
    "band-no-floor",
    "empty-header-sticks",
    "pick-whole-view",
    "pick-whole-only",
    "pick-zero",
    "pick-live",
    "pick-at-zero",
    "live-ignored",
    "live-new-ignored",
    "live-first",
    "scroll-first",
    "pick-touch",
    "pick-straddle",
    "lifted-qualifies",
]
assert list(_SPECS) == EDITS, "readings.py: EDITS and the decorated readings disagree"


def build(name):
    fn = _SPECS[name][0]
    files = base()
    fn(files)
    return files


# The public shapes the tools read: READINGS maps a name to the four files with one decision
# changed, and WHY / CASE carry the description and the enumerated case that separates it.
READINGS = {name: build(name) for name in _SPECS}
WHY = {name: _SPECS[name][1] for name in _SPECS}
CASE = {name: _SPECS[name][2] for name in _SPECS}


# --- the surface tools/readingcheck.py loads: it iterates READINGS, builds a policy dir per
# reading with policy_dir, and separates it against REFERENCE over enumerated then generated
# programs with run(). The values in READINGS are (fn, why, case); policy_dir reads the fn.
import tempfile  # noqa: E402

REFERENCE = str(lab.SOL)
_TREES = {}


def _tree_for(d):
    key = str(d)
    if key not in _TREES:
        _TREES[key] = lab.tree(policy=d)
    return _TREES[key]


def run(ref, text):
    return lab.run_text(_tree_for(ref), text)


def enumerated():
    cases, _gen, _model = lab.sealed()
    for c in cases.ORDER:
        yield c, "\n".join(cases.prog(c)) + "\n"


def generated(rounds):
    _cases, gen, _model = lab.sealed()
    for _f, n, lines in gen.programs("readingcheck", max(1, rounds), small_only=True):
        yield n, "\n".join(lines) + "\n"


def main(argv):
    cases, gen, model = lab.sealed()
    trees = {}
    for name in READINGS:
        trees[name] = lab.tree(files=build(name))
    truth = {c: model.expect(cases.prog(c)) for c in cases.ORDER}
    ok = True
    print("%-20s %-16s %s" % ("reading", "named case", "cases that catch it"))
    for name, (_fn, why, named) in _SPECS.items():
        caught = []
        for c in cases.ORDER:
            got = lab.run_text(trees[name], "\n".join(cases.prog(c)) + "\n")
            if got != truth[c]:
                caught.append(c)
        mark = "ok" if named in caught else "MISSED"
        ok = ok and named in caught
        print("%-20s %-16s %-6s %s" % (name, named, mark, ", ".join(caught) or "-"))
    if "--cases" in argv:
        return 0 if ok else 1
    per = 12
    progs = gen.programs("readings", per, small_only=True)
    want = {n: model.expect(lines) for _f, n, lines in progs}
    fams = [f for f, big in gen.FAMILIES if not big]
    print("\nfraction of generated programs each reading gets wrong, per family (%d each)" % per)
    print("%-20s " % "" + " ".join("%6s" % f[:6] for f in fams) + "   all")
    for name in READINGS:
        row, tot, bad = [], 0, 0
        for fam in fams:
            mine = [(n, l) for f, n, l in progs if f == fam]
            wrong = sum(1 for n, l in mine if lab.run_text(trees[name], "\n".join(l) + "\n") != want[n])
            row.append("%5.0f%%" % (100.0 * wrong / len(mine)))
            tot += len(mine)
            bad += wrong
        print("%-20s " % name + " ".join(row) + "  %4.0f%%" % (100.0 * bad / tot))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
