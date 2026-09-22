"""The settle rules written the obvious way: every question re-walks the whole journal.

This file is the specification in code. It is deliberately the slowest possible correct
resolver - a clean board and a full pass for every question and every wake - because it is
what the resource gate has to kill while staying exactly right. Everything else in this task
(the reference, the sealed model, the two correct variants) is checked against it on programs
small enough that its cost does not matter.

Nothing here ships. It also becomes `cheat-slow-walk`.
"""

# ---------------------------------------------------------------------------
# Reading a program.
#
# A line is [if g w | once g w] <op> <args>, or a structural or question line. Entries are
# numbered from 0 in the order they appear; changes are numbered from 0 in the order they are
# opened, and an entry outside a bracket is a change of its own.

ENTRY_ARGS = {"sec": 1, "set": 2, "clr": 1, "cut": 1, "add": 2, "lnk": 1}


class Bad(Exception):
    pass


class Ent:
    __slots__ = ("kind", "a", "b", "guard", "g", "w", "chg")

    def __init__(self, kind, a, b, guard, g, w, chg):
        self.kind = kind
        self.a = a
        self.b = b
        self.guard = guard          # None, "if" or "once"
        self.g = g
        self.w = w
        self.chg = chg


def _ints(part, want, head):
    if len(part) != want:
        raise Bad("%s takes %d numbers, got %d" % (head, want, len(part)))
    try:
        return [int(x) for x in part]
    except ValueError:
        raise Bad("%s takes numbers" % head)


def parse(text):
    ents = []
    steps = []
    nchg = 0
    openchg = None
    for raw in text.splitlines():
        part = raw.split()
        if not part:
            continue
        head = part[0]
        if head == "open":
            if part[1:]:
                raise Bad("open takes nothing")
            if openchg is not None:
                raise Bad("open inside a change")
            openchg = nchg
            nchg += 1
            continue
        if head == "shut":
            if part[1:]:
                raise Bad("shut takes nothing")
            if openchg is None:
                raise Bad("shut without open")
            openchg = None
            continue
        if head in ("off", "back"):
            (c,) = _ints(part[1:], 1, head)
            if c < 0 or c >= nchg:
                raise Bad("%s names no change" % head)
            steps.append((head, c))
            continue
        if head == "get":
            s, n = _ints(part[1:], 2, "get")
            if s < 0 or n < 0:
                raise Bad("get takes a section and a name")
            steps.append(("get", s, n))
            continue
        if head == "all":
            if part[1:]:
                raise Bad("all takes nothing")
            steps.append(("all",))
            continue

        guard, g, w = None, 0, 0
        if head in ("if", "once"):
            if len(part) < 4:
                raise Bad("%s takes a name, a number and an entry" % head)
            guard = head
            g, w = _ints(part[1:3], 2, head)
            if g < 0:
                raise Bad("%s takes a name" % head)
            part = part[3:]
            head = part[0]
        if head not in ENTRY_ARGS:
            raise Bad("unknown op %s" % head)
        args = _ints(part[1:], ENTRY_ARGS[head], head)
        if head in ("sec", "lnk") and args[0] < 0:
            raise Bad("%s takes a section" % head)
        if head in ("set", "clr", "cut", "add") and args[0] < 0:
            raise Bad("%s takes a name" % head)
        if openchg is None:
            chg = nchg
            nchg += 1
        else:
            chg = openchg
        ents.append(Ent(head, args[0], args[1] if len(args) > 1 else 0,
                        guard, g, w, chg))
        steps.append(("ent", len(ents) - 1))
    if openchg is not None:
        raise Bad("open without shut")
    return ents, steps, nchg


# ---------------------------------------------------------------------------
# The board, and reading a name in a section.

class Board:
    __slots__ = ("val", "mask", "link")

    def __init__(self):
        self.val = {}
        self.mask = set()
        self.link = {}

    def read(self, sec, name):
        seen = set()
        cur = sec
        while True:
            if cur in seen:
                return None
            seen.add(cur)
            key = (cur, name)
            if key in self.val:
                return self.val[key]
            if key in self.mask:
                return None
            nxt = self.link.get(cur)
            if nxt is None:
                return None
            cur = nxt


def apply(board, ent, cur):
    """Apply one entry in section `cur`; return the section the walk carries on with."""
    kind = ent.kind
    if kind == "sec":
        return ent.a
    if kind == "lnk":
        board.link[cur] = ent.a
        return cur
    key = (cur, ent.a)
    if kind == "set":
        board.val[key] = ent.b
        board.mask.discard(key)
    elif kind == "clr":
        board.val.pop(key, None)
        board.mask.discard(key)
    elif kind == "cut":
        board.val.pop(key, None)
        board.mask.add(key)
    elif kind == "add":
        found = board.read(cur, ent.a)
        if found is not None:
            board.val[key] = found + ent.b
            board.mask.discard(key)
    return cur


def walk(ents, upto, dead, awake):
    """One pass over the live awake entries, from a clean board.

    Returns the board it produced and, for every position below `upto`, the section the walk
    was carrying when it reached that position.
    """
    board = Board()
    seclist = [0] * upto
    cur = 0
    for i in range(upto):
        seclist[i] = cur
        ent = ents[i]
        if ent.chg in dead:
            continue
        if ent.guard == "once" and i not in awake:
            continue
        if ent.guard == "if" and board.read(cur, ent.g) != ent.w:
            continue
        cur = apply(board, ent, cur)
    return board, seclist


def settle(ents, upto, dead):
    """Work the board out from nothing: every sleeping entry starts asleep again."""
    asleep = [i for i in range(upto)
              if ents[i].guard == "once" and ents[i].chg not in dead]
    awake = set()
    passes = 0
    while True:
        board, seclist = walk(ents, upto, dead, awake)
        passes += 1
        woke = None
        for i in asleep:
            if board.read(seclist[i], ents[i].g) == ents[i].w:
                woke = i
                break
        if woke is None:
            return board, passes
        asleep.remove(woke)
        awake.add(woke)


# ---------------------------------------------------------------------------
# Running a program.

def run(text):
    ents, steps, _nchg = parse(text)
    dead = set()
    upto = 0
    out = []
    for step in steps:
        head = step[0]
        if head == "ent":
            upto = step[1] + 1
        elif head == "off":
            dead.add(step[1])
        elif head == "back":
            dead.discard(step[1])
        elif head == "get":
            board, passes = settle(ents, upto, dead)
            found = board.read(step[1], step[2])
            out.append("get %d %d %s %d" % (step[1], step[2],
                                            "-" if found is None else found, passes))
        elif head == "all":
            board, passes = settle(ents, upto, dead)
            out.append("all %d %d %d %d" % (passes, len(board.val), len(board.mask),
                                            len(board.link)))
            for key in sorted(board.val):
                out.append("v %d %d %d" % (key[0], key[1], board.val[key]))
            for key in sorted(board.mask):
                out.append("m %d %d" % key)
            for sec in sorted(board.link):
                out.append("l %d %d" % (sec, board.link[sec]))
    return out
