#!/bin/bash
# Drop a note whose line is gone without logging it. The table at the head comes out right and the log is shorter.
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
        waiting = {}
        for at, nid, line in opens:
            waiting.setdefault(at, []).append((nid, line))
        live = []
        log = []
        self._open(live, log, waiting.get(0, []))
        for step in range(1, self.store.count()):
            before = self.store.at(step - 1)
            after = self.store.at(step)
            carried = rule.kept(before, after)
            held = []
            lost = []
            for note in live:
                if note["line"] in carried:
                    note["line"] = carried[note["line"]]
                    held.append(note)
                else:
                    lost.append(note["id"])
            for nid in sorted(lost):
                pass
            live[:] = held
            for note in sorted(live, key=lambda n: n["id"]):
                if rule.raised(note["line"], before, after):
                    log.append(("raise", note["id"]))
            self._open(live, log, waiting.get(step, []))
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
