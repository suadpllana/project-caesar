"""Whole-solver readings of the rules, each a complete engine a submission could actually ship.

Every entry below is the reference with one decision changed, laid over the shipped tree the way
the verifier lays over a submission - so what is measured is a reachable answer, not a mutant of
a file nobody edits. `report()` prints, per reading, how many graded programs it moves and which
enumerated hand case names it. A reading that moves nothing is either unreachable or the rule it
changes is not exercised by the population, and both are authoring defects.

Usage:
    python3 readings.py [per] [seed]
"""
import sys

import harness

sys.path.insert(0, str(harness.TASK / "tests"))
import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

REF = {name: (harness.REF / name).read_text(encoding="utf-8") for name in harness.PARTS}


def swap(name, old, new):
    text = REF[name]
    if old not in text:
        raise SystemExit("reading text not found in %s: %r" % (name, old))
    return {name: text.replace(old, new, 1)}


READINGS = {
    # step.py - what a pulled candidate costs, and which units a source name can denote.
    "cost-drops-source": swap(
        "step.py", "return (rs if rs > rv else rv) + 1", "return rv + 1"),
    "cost-adds-source": swap(
        "step.py", "return (rs if rs > rv else rv) + 1", "return rs + rv + 1"),
    "src-local-only": swap(
        "step.py",
        "    out = []\n"
        "    b = at(deck, u.nm, s)\n"
        "    if b is not None and b[0] == UNIT:\n"
        "        out.append((b[1], b[2]))\n"
        "    if find(prog, s) is not None:\n"
        "        out.append((s, 0))\n"
        "    return out",
        "    b = at(deck, u.nm, s)\n"
        "    if b is not None and b[0] == UNIT:\n"
        "        return [(b[1], b[2])]\n"
        "    if find(prog, s) is not None:\n"
        "        return [(s, 0)]\n"
        "    return []"),
    "src-global-only": swap(
        "step.py",
        "    b = at(deck, u.nm, s)\n"
        "    if b is not None and b[0] == UNIT:\n"
        "        out.append((b[1], b[2]))\n",
        ""),
    "src-free-rank": swap(
        "step.py", "        out.append((b[1], b[2]))", "        out.append((b[1], 0))"),

    # show.py - which names each kind of pull can reach.
    "wide-takes-shut": swap(
        "show.py",
        "if b[0] == CLASH or x in v.hides or x in v.shuts:",
        "if b[0] == CLASH or x in v.hides:"),
    "narrow-blocks-shut": swap(
        "show.py",
        "if b is None or b[0] == CLASH or x in v.hides:",
        "if b is None or b[0] == CLASH or x in v.hides or x in v.shuts:"),
    "narrow-takes-hidden": swap(
        "show.py",
        "if b is None or b[0] == CLASH or x in v.hides:",
        "if b is None or b[0] == CLASH:"),
    "clash-carries": swap(
        "show.py",
        "if b[0] == CLASH or x in v.hides or x in v.shuts:",
        "if x in v.hides or x in v.shuts:"),

    # pick.py - what a set of lowest-ranked candidates settles to.
    "first-wins": swap(
        "pick.py",
        "    head = cands[0]\n"
        "    for c in cands:\n"
        "        if c != head:\n"
        "            return (CLASH, None)\n"
        "    return head",
        "    return cands[0]"),
    "clash-on-any-two": swap(
        "pick.py",
        "    head = cands[0]\n"
        "    for c in cands:\n"
        "        if c != head:\n"
        "            return (CLASH, None)\n"
        "    return head",
        "    if len(cands) > 1:\n"
        "        return (CLASH, None)\n"
        "    return cands[0]"),
    "clash-by-unit-only": swap(
        "pick.py",
        "        if c != head:",
        "        if c[1] != head[1]:"),
}


def _turn(body):
    return {"turn.py": body}


# turn.py - how the settlement is driven. These are whole rewrites rather than one-line swaps,
# because that is the shape a submission would actually take.
IN_PLACE = '''from prog.deck import OWN, UNIT, at, blank, put
from prog.unit import find

from .pick import settle
from .show import out_all, out_one
from .step import cost, srcs


def gather(deck, prog, u):
    got = {}
    for x in u.owns:
        got.setdefault(x, []).append((OWN, u.nm, 0))
    for x, vn in u.als:
        if find(prog, vn) is not None:
            got.setdefault(x, []).append((UNIT, vn, 0))
    for s, what in u.pulls:
        for vn, rs in srcs(deck, prog, u, s):
            if what == "*":
                for x, b in out_all(deck, prog, vn):
                    got.setdefault(x, []).append((b[0], b[1], cost(rs, b[2])))
            else:
                b = out_one(deck, prog, vn, what)
                if b is not None:
                    got.setdefault(what, []).append((b[0], b[1], cost(rs, b[2])))
    return got


def run(prog):
    deck = blank(prog.units)
    for _ in range(4000):
        moved = False
        for u in prog.units.values():
            for x, cands in gather(deck, prog, u).items():
                low = min(c[2] for c in cands)
                kind, tgt = settle([(c[0], c[1]) for c in cands if c[2] == low])
                if at(deck, u.nm, x) != (kind, tgt, low):
                    put(deck, u.nm, x, kind, tgt, low)
                    moved = True
        if not moved:
            break
    return deck
'''

READINGS["in-place-sweep"] = _turn(IN_PLACE)


def turn_swap(old, new, tag):
    ref = REF["turn.py"]
    if old not in ref:
        raise SystemExit("%s reading text not found in turn.py: %r" % (tag, old))
    return _turn(ref.replace(old, new, 1))


# A clash stops being terminal: a slot that settled to one can be settled again later.
READINGS["clash-retry"] = turn_swap(
    "def done(deck, un, x):\n"
    "    return at(deck, un, x) is not None",
    "def done(deck, un, x):\n"
    "    got = at(deck, un, x)\n"
    "    return got is not None and got[0] != \"clash\"",
    "clash-retry")

# `als` costs a step rather than sitting where the unit declared it.
READINGS["als-costs-one"] = turn_swap(
    "def owned(prog, deck, u, rank, got):\n"
    "    if rank:\n"
    "        return\n"
    "    for x in u.owns:\n"
    "        if not done(deck, u.nm, x):\n"
    "            got.setdefault(x, []).append((OWN, u.nm))\n"
    "    for x, vn in u.als:\n"
    "        if find(prog, vn) is not None and not done(deck, u.nm, x):\n"
    "            got.setdefault(x, []).append((UNIT, vn))",
    "def owned(prog, deck, u, rank, got):\n"
    "    if rank == 0:\n"
    "        for x in u.owns:\n"
    "            if not done(deck, u.nm, x):\n"
    "                got.setdefault(x, []).append((OWN, u.nm))\n"
    "    elif rank == 1:\n"
    "        for x, vn in u.als:\n"
    "            if find(prog, vn) is not None and not done(deck, u.nm, x):\n"
    "                got.setdefault(x, []).append((UNIT, vn))",
    "als-costs-one")

# `hide` is read as taking the name out of its own unit as well.
READINGS["hide-drops-local"] = turn_swap(
    "            for x, cands in got.items():\n"
    "                kind, tgt = settle(cands)",
    "            for x, cands in got.items():\n"
    "                if x in u.hides:\n"
    "                    continue\n"
    "                kind, tgt = settle(cands)",
    "hide-drops-local")


def report(per, seed):
    progs = [("hand", n, cases.CASES[n]) for n in cases.ORDER]
    progs += gen.programs(seed, per)
    want = {name: model.expect(lines) for _, name, lines in progs}

    base = harness.tree(harness.REF)
    go, drop = harness.in_proc(base)
    same = [n for _, n, ln in progs if go(ln) != want[n]]
    drop()
    if same:
        raise SystemExit("reference disagrees with the model on %d programs: %s"
                         % (len(same), same[:4]))

    print("population: %d programs (%d hand, %d generated)"
          % (len(progs), len(cases.ORDER), len(progs) - len(cases.ORDER)), flush=True)
    rows = []
    for name in sorted(READINGS):
        dst = harness.tree(harness.REF)
        for fname, text in READINGS[name].items():
            (dst / "res" / fname).write_text(text, encoding="utf-8", newline="\n")
        go, drop = harness.in_proc(dst)
        moved, hands = [], []
        for fam, pname, lines in progs:
            try:
                got = go(lines)
            except Exception:  # noqa: BLE001
                got = None
            if got != want[pname]:
                moved.append(pname)
                if fam == "hand":
                    hands.append(pname)
        drop()
        rows.append((name, len(moved), len(progs), hands))
    for name, n, total, hands in sorted(rows, key=lambda r: -r[1]):
        mark = "  " if hands else "  NO HAND CASE  "
        print("%-22s %5.1f%%  %4d/%d%s%s"
              % (name, 100.0 * n / total, n, total, mark, ",".join(hands[:3])), flush=True)
    dead = [r[0] for r in rows if r[1] == 0]
    if dead:
        print("UNSEPARATED: %s" % ", ".join(dead), flush=True)
    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(report(int(sys.argv[1]) if len(sys.argv) > 1 else 100,
                    sys.argv[2] if len(sys.argv) > 2 else "readings"))


# --- the contract tools/readingcheck.py drives ------------------------------------------

REFERENCE = str(harness.REF)

_TREES = {}


def run(policy, text):
    """Drive one program under one policy directory, returning the printed trace."""
    key = str(policy)
    got = _TREES.get(key)
    if got is None:
        got = harness.in_proc(harness.tree(policy))[0]
        _TREES[key] = got
    return got([ln for ln in text.splitlines()])


def enumerated():
    return [(name, "\n".join(cases.ops(name))) for name in cases.ORDER]


def generated(n):
    per = max(8, (n * 100) // 318)
    out = []
    for fam, name, lines in gen.programs("readingcheck", per):
        out.append((name, "\n".join(lines)))
        if len(out) >= n:
            break
    return out
