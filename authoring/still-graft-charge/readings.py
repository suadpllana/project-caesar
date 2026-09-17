"""Every plausible wrong reading of the rules, as the file it would replace in the reference.

    python3 ../../tools/readingcheck.py still-graft-charge

Each reading is a patch of the reference source, and each patch asserts that it fired: a
replacement that matched nothing would ship as the reference with its docstring changed and
report "equivalent", which is the quietest way for this file to lie.

A reading that no enumerated case separates is either a case this task still owes or a correct
variant; either way `readingcheck` says which, and `emit.py` turns each one into a cheat.
"""
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "still-graft-charge"
REFERENCE = str(TASK / "solution")
sys.path.insert(0, str(TASK / "tests"))

import cases  # noqa: E402
import gen  # noqa: E402

SRC = {p.name: p.read_text(encoding="utf-8") for p in Path(REFERENCE).glob("*.py")}


def patch(name, *pairs):
    """The reference file with each replacement applied, or an error if one matched nothing."""
    text = SRC[name]
    for old, new in pairs:
        text, n = text.replace(old, new), text.count(old)
        if n != 1:
            raise SystemExit("patch on %s matched %d times: %r" % (name, n, old[:60]))
    return {name: text}


SCAN = '''from led import hold


def blocks(st):
    seen = set()
    for one in st.lines.values():
        for chain in one.cells.values():
            for e in chain.ents:
                if id(e.blk) not in seen:
                    seen.add(id(e.blk))
                    yield e.blk


def charge(st, name):
    total = 0
    for b in blocks(st):
        if %s:
            total += b.size
    return total
'''

PLACES = '''from bisect import bisect_left, bisect_right

from led import hold


def places(st, b):
    """Every place holding a block: a head counts as one and so does each still."""
    out = []
    top = hold.kit(st).g
    for e in b.spots:
        line = st.lines[e.line]
        hi = top if e.died is None else e.died
        if e.died is None:
            out.append(e.line)
        lo = bisect_left(line.taken, e.born)
        for idx in line.taken[lo:bisect_right(line.taken, hi - 1)]:
            owner = e.line
            for i, who in line.away:
                if i == idx:
                    owner = who
            out.append(owner)
    return out


def blocks(st):
    seen = set()
    for one in st.lines.values():
        for chain in one.cells.values():
            for e in chain.ents:
                if id(e.blk) not in seen:
                    seen.add(id(e.blk))
                    yield e.blk


def charge(st, name):
    total = 0
    for b in blocks(st):
        where = places(st, b)
        if len(where) == 1 and where[0] == name:
            total += b.size
    return total
'''

PARENT = '''from led import hold


def above(st, name):
    origin = st.lines[name].origin
    return None if origin is None else st.stills[origin].owner


def blocks(st):
    seen = set()
    for one in st.lines.values():
        for chain in one.cells.values():
            for e in chain.ents:
                if id(e.blk) not in seen:
                    seen.add(id(e.blk))
                    yield e.blk


def charge(st, name):
    up = above(st, name)
    total = 0
    for b in blocks(st):
        who = hold.who(st, b)
        if name in who and (up is None or up not in who):
            total += b.size
    return total
'''

READINGS = {
    # --- what a holder is ---------------------------------------------------------------
    "charge-refs": {"cost.py": PLACES},
    "charge-head": {"cost.py": SCAN % (
        "hold.who(st, b) == {name} and any(e.line == name and e.died is None"
        " for e in b.spots)")},
    "charge-parent": {"cost.py": PARENT},
    "charge-any": {"cost.py": SCAN % "name in hold.who(st, b)"},

    # --- what a still holds -------------------------------------------------------------
    "still-now": patch(
        "cell.py",
        ("        e = one.under(rec.idx)", "        e = one.open()"),
    ),
    "graft-live": patch(
        "tree.py",
        ("    for c, b in cell.held(st, still):",
         "    for c, b in [(c, ch.open().blk) for c, ch in\n"
         "                 cell.line(st, st.stills[still].on).cells.items()\n"
         "                 if ch.open() is not None]:"),
    ),

    # --- the lift -------------------------------------------------------------------------
    "lift-all": patch(
        "tree.py",
        ("    cut = above.stills.index(still) + 1", "    cut = len(above.stills)"),
    ),
    "lift-after": patch(
        "tree.py",
        ("    cut = above.stills.index(still) + 1\n"
         "    moved = above.stills[:cut]\n"
         "    above.stills = above.stills[cut:]",
         "    cut = above.stills.index(still)\n"
         "    moved = above.stills[cut:]\n"
         "    above.stills = above.stills[:cut]"),
    ),
    "lift-keep": patch(
        "tree.py",
        ("    one.origin = above.origin\n    above.origin = still\n", ""),
    ),
    "lift-noown": patch(
        "tree.py",
        ("        hold.shift(st, rec.on, rec.idx, name)\n", ""),
    ),

    # --- the cap ----------------------------------------------------------------------------
    "cap-added": patch(
        "gate.py",
        ("    made, shut = cell.write(st, name, lo, hi, size)\n"
         "    if one.cap is not None and cost.charge(st, name) > one.cap:\n"
         "        cell.undo(st, made, shut)\n"
         "        say.full(st, name)\n"
         "        return",
         "    if one.cap is not None and \\\n"
         "            cost.charge(st, name) + (hi - lo + 1) * size > one.cap:\n"
         "        say.full(st, name)\n"
         "        return\n"
         "    made, _shut = cell.write(st, name, lo, hi, size)"),
    ),
    "cap-number": patch(
        "gate.py",
        ("    made, shut = cell.write(st, name, lo, hi, size)",
         "    num = st.mint()\n    made, shut = cell.write(st, name, lo, hi, size)"),
        ("    num = st.mint()\n    for e in made:", "    for e in made:"),
    ),
    "cap-before": patch(
        "gate.py",
        ("    if one.cap is not None and cost.charge(st, name) > one.cap:",
         "    if one.cap is not None and cost.charge(st, name) >= one.cap:"),
    ),

    # --- the drop ------------------------------------------------------------------------------
    "drop-held": patch(
        "free.py",
        ("        if not now:\n            size += b.size", "        size += b.size"),
    ),
    "drop-stills": patch(
        "free.py",
        ("        if not now:\n            size += b.size",
         "        if not [e for e in b.spots if e.died is None]:\n            size += b.size"),
    ),
    "drop-any": patch(
        "tree.py",
        ("    for one in st.lines.values():\n        if one.origin == still:\n"
         "            return True\n    return False",
         "    return False"),
    ),
    "drop-grafted": patch(
        "tree.py",
        ("    for one in st.lines.values():\n        if one.origin == still:\n"
         "            return True\n    return False",
         "    owner = st.stills[still].owner\n    for one in st.lines.values():\n"
         "        if one.origin is not None and st.stills[one.origin].owner == owner:\n"
         "            return True\n    return False"),
    ),

    # --- what a write and a cut let go of --------------------------------------------------------
    "put-release": patch(
        "cell.py",
        ("    for e in shut:\n        hold.touch(st, e.blk)\n    return made, shut",
         "    for e in shut:\n        hold.settle(st, e.blk, set())\n    return made, shut"),
    ),
    "cut-release": patch(
        "cell.py",
        ("    for e in shut:\n        hold.touch(st, e.blk)\n\n\ndef at(",
         "    for e in shut:\n        hold.settle(st, e.blk, set())\n\n\ndef at("),
    ),
}


# --- driving one program under one policy ------------------------------------------------------

_TREES = {}


def tree(policy):
    room = _TREES.get(str(policy))
    if room is None:
        room = Path(tempfile.mkdtemp(prefix="policy-")) / "app"
        shutil.copytree(TASK / "tests" / "pristine", room)
        for one in Path(policy).glob("*.py"):
            shutil.copy(one, room / "led" / one.name)
        _TREES[str(policy)] = room
    return room


def run(policy, text):
    here = str(tree(policy))
    for mod in [m for m in list(sys.modules) if m == "ops" or m == "led"
                or m.startswith("led.")]:
        del sys.modules[mod]
    sys.path.insert(0, here)
    try:
        import ops
        from led import store
        st = store.Led()
        for line in text.strip().splitlines():
            if line.strip():
                ops.ex(st, tuple(line.split()))
        return list(st.out)
    finally:
        sys.path.remove(here)
        for mod in [m for m in list(sys.modules) if m == "ops" or m == "led"
                    or m.startswith("led.")]:
            del sys.modules[mod]


def enumerated():
    return [(name, "\n".join(cases.ops(name))) for name in cases.ORDER]


def generated(n):
    out = []
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for i in range(max(1, n // 9)):
            name = "%s-%d" % (fam, i)
            out.append((name, "\n".join(gen.one(fam, "readings/%s" % name))))
    return out


def reductions(text):
    """Structure-aware candidates: drop an op, and drop a line with everything about it."""
    lines = [one for one in text.split("\n") if one.strip()]
    for i in range(len(lines) - 1, -1, -1):
        yield "\n".join(lines[:i] + lines[i + 1:])
    for name in {one.split()[1] for one in lines if one.split()[0] == "line"}:
        keep = [one for one in lines if name not in one.split()]
        if len(keep) < len(lines):
            yield "\n".join(keep)
