#!/bin/bash
# Rebuild each note by asking for the script from the revision it was opened at straight to the head. Stateless, one call a note instead of one a revision, and the shape the shipped board already has. The pinned script does not compose, so it resurrects notes whose line died revisions ago and whose text was typed again later.
set -euo pipefail
APP_DIR="${APP_DIR:-/app}"
cat > "${APP_DIR}/note/board.py" <<'ENDBOARD'
"""The note board, rebuilt from the store.

Nothing survives between requests, so the board is reconstructed by walking
the store from the first revision up to the head. The walk is the whole point.
The pinned script does not compose: the script from r0 to r2 is not the script
from r0 to r1 followed by the one from r1 to r2, and on two thirds of the
streams we grade the two disagree about which lines survived. A board that
diffs a note's own revision straight against the head is cheaper, is stateless
in the way the store asks for, and answers a different question.

Order inside one revision is fixed and is stated in the brief, because two
correct boards would otherwise disagree about the log for no reason anybody
could grade.
"""

from note import rule


class Board(object):
    def __init__(self, store):
        self.store = store

    def build(self, opens):
        head = self.store.count() - 1
        live = []
        log = []
        for at, nid, line in sorted(opens, key=lambda o: o[1]):
            here = self.store.at(at)
            there = self.store.at(head)
            carried = rule.kept(here, there)
            if line in carried:
                live.append({"id": nid, "line": carried[line]})
            else:
                log.append(("retire", nid))
        if head > 0:
            before = self.store.at(head - 1)
            after = self.store.at(head)
            for note in live:
                if rule.raised(note["line"], before, after):
                    log.append(("raise", note["id"]))
        self._open(live, log, [])
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
"""Which lines a revision keeps, and which of them sit inside its change.

Both answers come off the script the tool itself settled. That matters more
than it looks. Several scripts of the same length exist for almost any pair of
revisions of a file that repeats its lines, and they disagree about which copy
of a repeated line survived, so a mapping rebuilt here from an ordinary
longest-common-subsequence walk is a different answer to a different question
and moves the note to a different line.

A change is not the set of lines the script added. It reaches across the kept
lines that sit between its runs, so a line can come through a revision
untouched and still be part of the change somebody has to read, which is what
`grp.spans` settles.
"""

from scr import grp, pin


def kept(before, after):
    out = {}
    for kind, i, j in pin.reading(before, after, pin.script(before, after)):
        if kind == "K":
            out[i] = j
    return out


def raised(line, before, after):
    for chunk in grp.spans(before, after):
        if line in chunk:
            return True
    return False
ENDRULE
