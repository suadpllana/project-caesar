#!/bin/bash
# Admit the notes opened at a revision before carrying the ones already there, so a note opened at that revision is carried through the script that produced it.
set -euo pipefail
APP_DIR="${APP_DIR:-/app}"
cat > "${APP_DIR}/note/board.py" <<'ENDBOARD'
"""The note board, rebuilt from the store.

Nothing survives between requests, so the board is reconstructed by replaying
the store from the first revision up to the head. The replay is the whole
point. The pinned script does not compose: the script from r0 to r2 is not the
script from r0 to r1 followed by the one from r1 to r2, and on two thirds of
the streams we grade the two disagree about which lines survived. A board that
diffs a note's own revision straight against the head is cheaper, is stateless
in the way the store asks for, and answers a different question.

Order inside one revision is fixed and is stated in the brief, because two
correct implementations would otherwise disagree about the log: everything the
carry retired, then everything it raised, then the absorbing, each in
ascending note order.
"""

from scr import grp, pin
from note import rule


class Board(object):
    def __init__(self, store):
        self.store = store

    def build(self, opens):
        waiting = {}
        for at, nid, line in opens:
            waiting.setdefault(at, []).append((nid, line))
        live = []
        log = []
        self._open(live, log, waiting.get(0, []))
        for step in range(1, self.store.count()):
            before = self.store.at(step - 1)
            after = self.store.at(step)
            self._open(live, log, waiting.get(step, []))
            keep = rule.kept(pin.reading(before, after, pin.script(before, after)))
            spans = grp.spans(before, after)
            held = []
            lost = []
            for note in live:
                if note["line"] in keep:
                    note["line"] = keep[note["line"]]
                    held.append(note)
                else:
                    lost.append(note["id"])
            for nid in sorted(lost):
                log.append(("retire", nid))
            live[:] = held
            for note in sorted(live, key=lambda n: n["id"]):
                if rule.raised(note["line"], spans):
                    log.append(("raise", note["id"]))
            pass
        live.sort(key=lambda n: n["id"])
        return live, log

    def _open(self, live, log, fresh):
        for nid, line in fresh:
            live.append({"id": nid, "line": line})
        seen = {}
        held = []
        taken = []
        for note in sorted(live, key=lambda n: n["id"]):
            owner = seen.get(note["line"])
            if owner is None:
                seen[note["line"]] = note["id"]
                held.append(note)
            else:
                taken.append((note["id"], owner))
        for nid, owner in sorted(taken):
            log.append(("absorb", owner, nid))
        live[:] = held
ENDBOARD
cat > "${APP_DIR}/note/rule.py" <<'ENDRULE'
"""Which lines a script keeps, and which of them sit inside a change.

`kept` reads the mapping straight off the walk the pinned engine produced.
That matters more than it looks: several scripts of the same length exist for
almost any pair whose lines repeat, and they disagree about which copy of a
repeated line survived. Rebuilding the mapping from a textbook diff, or from
the opcodes the standard library's matcher returns, answers a different
question and moves the note to a different line.

`raised` asks whether a line the script kept nevertheless falls inside one of
the changes of that same script. It can: a change absorbs the kept lines that
sit between its runs, so a line can survive the revision untouched and still
be part of the change the reviewer has to look at again.
"""


def kept(walk):
    out = {}
    for kind, i, j in walk:
        if kind == "K":
            out[i] = j
    return out


def raised(line, spans):
    for s in spans:
        if line in s:
            return True
    return False
ENDRULE
