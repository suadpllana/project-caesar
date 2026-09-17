"""Build every wrong reading once, and write the cheat that carries it.

`readings.py` measures these against the enumerated set and `cheat/` ships them, so both come
from this file and cannot drift apart. A reading is a patch of the reference: every replacement
has to fire, and a patch that matches nothing raises here rather than shipping as the reference
with its docstring moved.

    python3 authoring/queue-hold-drop/emit.py            write cheat/cheat-*.sh
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "queue-hold-drop"
REF = TASK / "solution"
CHEAT = TASK / "cheat"
PARTS = ("line.py", "fold.py", "hold.py", "view.py", "lay.py", "reach.py")

SRC = {name: (REF / name).read_text(encoding="utf-8") for name in PARTS}

BUILT = {}
WHY = {}


def reading(name, why, *patches):
    """One wrong reading, as the files it replaces. Every replacement must fire."""
    files = {}
    for part, old, new in patches:
        base = files.get(part, SRC[part])
        if old not in base:
            raise SystemExit("patch for %s did not match in %s" % (name, part))
        files[part] = base.replace(old, new, 1)
    BUILT[name] = files
    WHY[name] = why
    return files


# --- which changes go out -----------------------------------------------------------------

reading(
    "hold-no-spread",
    "a change that stays behind does not hold the later changes naming its record",
    ("hold.py",
     "        if wait or held.intersection(nm):\n"
     "            held.add(line.about(c))\n"
     "            continue\n",
     "        if wait:\n"
     "            continue\n"),
)

reading(
    "hold-new-free",
    "a creation goes out whether or not the record it names as parent carries an id",
    ("hold.py",
     '            if c.kind == "new" and x == c.a:\n',
     '            if c.kind == "new":\n'),
)

reading(
    "name-mov-flat",
    "a move names only the record it moves, not the record it moves it under",
    ("line.py",
     '    if c.kind in ("new", "mov") and c.b != "-":\n',
     '    if c.kind == "new" and c.b != "-":\n'),
)

reading(
    "id-at-send",
    "a creation takes its id when it goes out instead of when it is answered",
    ("hold.py",
     "        c.sent = True\n"
     '        st.out.append(say.wire("out", c.kind, bind.show(st, c.a)))',
     '        if c.kind == "new":\n'
     "            bind.hand(st, c.a)\n"
     "        c.sent = True\n"
     '        st.out.append(say.wire("out", c.kind, bind.show(st, c.a)))'),
    ("fold.py",
     '        if c.kind == "new":\n'
     "            bind.hand(st, c.a)\n",
     ""),
)

# --- which change an answer lands on, and what it does --------------------------------------

reading(
    "ans-front",
    "an answer lands on the front of the queue rather than on the oldest change sent",
    ("line.py",
     "def waiting(st):\n"
     "    for i, c in enumerate(st.q):\n"
     "        if c.sent:\n"
     "            return i\n"
     "    return -1\n",
     "def waiting(st):\n"
     "    return 0 if st.q else -1\n"),
)

reading(
    "ack-early",
    "the acceptance prints the identity the record had before the id was handed out",
    ("fold.py",
     '        if c.kind == "new":\n'
     "            bind.hand(st, c.a)\n"
     '        st.out.append(say.wire("ack", c.kind, bind.show(st, c.a)))',
     "        seen = bind.show(st, c.a)\n"
     '        if c.kind == "new":\n'
     "            bind.hand(st, c.a)\n"
     '        st.out.append(say.wire("ack", c.kind, seen))'),
)

reading(
    "take-twice",
    "an accepted change goes into the confirmed records and stays on the queue as well",
    ("fold.py",
     "    c = st.q.pop(i)\n    if good:",
     "    c = st.q[i]\n    if not good:\n        st.q.pop(i)\n    if good:"),
)

# --- what a refusal takes with it -----------------------------------------------------------

reading(
    "gone-one",
    "a refusal takes only the change refused",
    ("fold.py",
     '        st.out.append("gone %d" % (1 + sweep(st, i, {line.about(c)})))',
     '        st.out.append("gone 1")'),
)

reading(
    "gone-flat",
    "the take-away does not spread: only changes naming the refused record go",
    ("fold.py",
     "            seed.add(line.about(c))\n            took += 1\n",
     "            took += 1\n"),
)

reading(
    "gone-all",
    "a refusal takes every later change on the queue",
    ("fold.py",
     "        if seed.intersection(line.names(c)):",
     "        if seed or True:"),
)

reading(
    "gone-both",
    "the take-away spreads backwards over the queue as well as forwards",
    ("fold.py",
     "    keep = st.q[:at]\n    took = 0\n    for c in st.q[at:]:",
     "    keep = []\n    took = 0\n    for c in st.q:"),
)

# --- the removal of a record the server has never confirmed ------------------------------------

reading(
    "stop-queued",
    "a removal of a record with no id joins the queue like any other change",
    ("line.py",
     '    if c.kind == "cut" and not bind.got(st, c.a):\n'
     "        at = -1\n"
     "        for i, q in enumerate(st.q):\n"
     '            if q.kind == "new" and q.a == c.a:\n'
     "                at = i\n"
     "                break\n"
     "        if at >= 0:\n"
     "            seed = {about(st.q[at])}\n"
     "            del st.q[at]\n"
     "            fold.sweep(st, at, seed)\n"
     "            view.fresh(st)\n"
     "            return\n",
     ""),
)

reading(
    "stop-only",
    "cancelling takes the creation off and leaves the changes queued behind it",
    ("line.py",
     "            seed = {about(st.q[at])}\n"
     "            del st.q[at]\n"
     "            fold.sweep(st, at, seed)\n",
     "            del st.q[at]\n"),
)

# --- what a removal takes, and the move under one's own descendant -------------------------------

reading(
    "reach-kids",
    "a removal takes the records directly under it and stops there",
    ("reach.py",
     "def under(rec, name):\n"
     "    down = kids(rec)\n"
     "    out = []\n"
     "    seen = {name}\n"
     "    edge = list(down.get(name, ()))\n"
     "    while edge:\n"
     "        one = edge.pop()\n"
     "        if one in seen:\n"
     "            continue\n"
     "        seen.add(one)\n"
     "        out.append(one)\n"
     "        edge.extend(down.get(one, ()))\n"
     "    return out\n",
     "def under(rec, name):\n"
     "    return list(kids(rec).get(name, ()))\n"),
)

reading(
    "reach-fixed",
    "what a removal takes is worked out when the user makes it, not when it is laid over",
    ("line.py",
     "from . import bind, fold, view",
     "from . import bind, fold, reach, view"),
    ("line.py",
     "    st.q.append(c)\n    view.push(st, c)",
     '    if c.kind == "cut":\n'
     "        c.fix = tuple(reach.under(view.of(st), c.a))\n"
     "    st.q.append(c)\n"
     "    view.push(st, c)"),
    ("lay.py",
     "        for name in reach.under(rec, c.a):\n            rec.pop(name, None)\n",
     '        for name in getattr(c, "fix", None) or reach.under(rec, c.a):\n'
     "            rec.pop(name, None)\n"),
)

reading(
    "mov-cycle",
    "a move is allowed to put a record under one of its own descendants",
    ("reach.py",
     "def inside(rec, name, p):\n"
     "    at = p\n"
     "    seen = 0\n"
     "    while at is not None:\n"
     "        if at == name:\n"
     "            return True\n"
     "        r = rec.get(at)\n"
     "        if r is None:\n"
     "            return False\n"
     "        at = r.up\n"
     "        seen += 1\n"
     "        if seen > len(rec):\n"
     "            return False\n"
     "    return False\n",
     "def inside(rec, name, p):\n"
     "    return False\n"),
)

# --- what one change does to the records it is laid over -------------------------------------------

reading(
    "lay-upsert",
    "a field change to a record that is not there brings the record back",
    ("lay.py",
     '    elif c.kind == "set":\n'
     "        r = rec.get(c.a)\n"
     "        if r is not None:\n"
     "            r.fld[c.b] = c.c\n"
     '    elif c.kind == "add":\n'
     "        r = rec.get(c.a)\n"
     "        if r is not None:\n"
     "            r.fld[c.b] = r.fld.get(c.b, 0) + c.c\n",
     '    elif c.kind == "set":\n'
     "        if c.a not in rec:\n"
     "            rec[c.a] = Rec(None)\n"
     "        rec[c.a].fld[c.b] = c.c\n"
     '    elif c.kind == "add":\n'
     "        if c.a not in rec:\n"
     "            rec[c.a] = Rec(None)\n"
     "        rec[c.a].fld[c.b] = rec[c.a].fld.get(c.b, 0) + c.c\n"),
)

reading(
    "add-set",
    "adding to a field puts the number in it instead of adding to what it holds",
    ("lay.py",
     "            r.fld[c.b] = r.fld.get(c.b, 0) + c.c\n",
     "            r.fld[c.b] = c.c\n"),
)

reading(
    "zero-hidden",
    "setting a field to zero is the same as never having set it",
    ("lay.py",
     '    elif c.kind == "set":\n'
     "        r = rec.get(c.a)\n"
     "        if r is not None:\n"
     "            r.fld[c.b] = c.c\n",
     '    elif c.kind == "set":\n'
     "        r = rec.get(c.a)\n"
     "        if r is not None:\n"
     "            if c.c == 0:\n"
     "                r.fld.pop(c.b, None)\n"
     "            else:\n"
     "                r.fld[c.b] = c.c\n"),
)

# --- the laid-over view -----------------------------------------------------------------------------

reading(
    "view-skip-sent",
    "a change that has gone out is already the server's, so it is not laid over",
    ("view.py",
     "        for c in st.q:\n            lay.one(vw, c)\n",
     "        for c in st.q:\n            if not c.sent:\n                lay.one(vw, c)\n"),
    ("view.py",
     "def push(st, c):\n"
     '    vw = getattr(st, "vw", None)\n'
     "    if vw is not None:\n"
     "        lay.one(vw, c)\n",
     "def push(st, c):\n"
     "    st.vw = None\n"),
)

reading(
    "ask-base",
    "the questions are answered from the confirmed records, without the queue over them",
    ("view.py",
     "def of(st):\n"
     '    vw = getattr(st, "vw", None)\n'
     "    if vw is None:\n"
     "        vw = {}\n"
     "        for name, r in st.base.items():\n"
     "            vw[name] = r.copy()\n"
     "        for c in st.q:\n"
     "            lay.one(vw, c)\n"
     "        st.vw = vw\n"
     "    return vw\n",
     "def of(st):\n"
     "    return st.base\n"),
)

reading(
    "order-name",
    "the listing comes out in name order rather than the order records entered the view",
    ("view.py",
     "    for name, r in of(st).items():",
     "    for name, r in sorted(of(st).items()):"),
)

reading(
    "say-unsorted",
    "a record's fields print in the order they were first written",
    ("view.py",
     "from . import bind, lay, say",
     "from . import bind, lay, say  # noqa: F401"),
    ("view.py",
     '    st.out.append(say.shelf("rec", bind.show(st, name), up, r.fld))',
     '    st.out.append(" ".join(["rec", bind.show(st, name), up]\n'
     '                           + ["%s=%d" % kv for kv in r.fld.items()]))'),
    ("view.py",
     '        st.out.append(say.shelf("row", bind.show(st, name), up, r.fld))',
     '        st.out.append(" ".join(["row", bind.show(st, name), up]\n'
     '                               + ["%s=%d" % kv for kv in r.fld.items()]))'),
)

# --- right, and outside the limit ---------------------------------------------------------------------

SLOW = {}


def slow(name, why, *patches):
    files = reading(name, why, *patches)
    SLOW[name] = files
    del BUILT[name]
    return files


slow(
    "slow-rebuild",
    "exactly right, and derives the view again for every question",
    ("view.py",
     "def of(st):\n"
     '    vw = getattr(st, "vw", None)\n'
     "    if vw is None:\n"
     "        vw = {}\n"
     "        for name, r in st.base.items():\n"
     "            vw[name] = r.copy()\n"
     "        for c in st.q:\n"
     "            lay.one(vw, c)\n"
     "        st.vw = vw\n"
     "    return vw\n\n\n"
     "def push(st, c):\n"
     '    vw = getattr(st, "vw", None)\n'
     "    if vw is not None:\n"
     "        lay.one(vw, c)\n",
     "def of(st):\n"
     "    vw = {}\n"
     "    for name, r in st.base.items():\n"
     "        vw[name] = r.copy()\n"
     "    for c in st.q:\n"
     "        lay.one(vw, c)\n"
     "    return vw\n\n\n"
     "def push(st, c):\n"
     "    return None\n"),
)

slow(
    "slow-copy",
    "exactly right, and hands out a copy of the whole view for every question",
    ("view.py",
     "        st.vw = vw\n    return vw\n",
     "        st.vw = vw\n"
     "    return {name: r.copy() for name, r in vw.items()}\n"),
)


# --- writing the cheats ---------------------------------------------------------------------------------

HEAD = "#!/bin/bash\n# %s\nset -euo pipefail\n\n"


def script(why, files):
    """The reference's six files with this reading's patch in them.

    A cheat shipping only the files it patches would leave the rest of the service as the shipped
    one, whose `view.py` is right but rebuilds per question; the worker would then die on the
    clock and the run would prove nothing about the reading.
    """
    whole = dict(SRC)
    whole.update(files)
    out = [HEAD % why]
    for name in sorted(whole):
        out.append("cat > /app/pend/%s <<'PYEOF'\n%sPYEOF\n\n" % (name, whole[name]))
    return "".join(out)


def write():
    CHEAT.mkdir(exist_ok=True)
    made = []
    for name in sorted(list(BUILT) + list(SLOW)):
        files = BUILT.get(name) or SLOW[name]
        path = CHEAT / ("cheat-%s.sh" % name)
        path.write_text(script(WHY[name], files), encoding="utf-8", newline="\n")
        path.chmod(0o755)
        made.append(path.name)
    print("%d cheats written" % len(made))
    return made


if __name__ == "__main__":
    write()
