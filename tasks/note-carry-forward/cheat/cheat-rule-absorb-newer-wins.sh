#!/bin/bash
# Let the note that arrived last keep the line. The rule gives it to the older one.
set -euo pipefail
APP_DIR="${APP_DIR:-/app}"
cat > "${APP_DIR}/note/board.py" <<'ENDBOARD'
"""The note board, rebuilt from the store.

Nothing survives between requests, so the board is reconstructed by walking
the store from the first revision up to the head. The walk is the whole point,
twice over.

The pinned script does not compose: the script from r0 to r2 is not the script
from r0 to r1 followed by the one from r1 to r2, and on most of the streams we
grade the two disagree about which lines survived. A board that diffs a note's
own revision straight against the head is cheaper, is stateless in the way the
store asks for, and answers a different question.

And whether a note is raised is not a property of the revision it is being
carried through. It is raised when its line becomes part of a change, so the
board has to remember, per note, whether it was already inside one when the
revision before this one closed. A board that recomputes from the endpoints
has nowhere to keep that.

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
        seen_in_change = {}
        log = []
        self._open(live, seen_in_change, log, waiting.get(0, []))
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
                log.append(("retire", nid))
                seen_in_change.pop(nid, None)
            live[:] = held
            for note in sorted(live, key=lambda n: n["id"]):
                now = rule.inside(note["line"], before, after)
                if rule.should_raise(now, seen_in_change.get(note["id"], False)):
                    log.append(("raise", note["id"]))
                seen_in_change[note["id"]] = now
            self._open(live, seen_in_change, log, waiting.get(step, []))
        live.sort(key=lambda n: n["id"])
        return live, log

    def _open(self, live, seen_in_change, log, fresh):
        for nid, line in fresh:
            live.append({"id": nid, "line": line})
            seen_in_change[nid] = False
        seen = {}
        held = []
        taken = []
        for note in sorted(live, key=lambda n: -n["id"]):
            owner = seen.get(note["line"])
            if owner is None:
                seen[note["line"]] = note["id"]
                held.append(note)
            else:
                taken.append((note["id"], owner))
        for nid, owner in sorted(taken):
            log.append(("absorb", nid, owner))
            seen_in_change.pop(nid, None)
        live[:] = held
ENDBOARD
cat > "${APP_DIR}/note/rule.py" <<'ENDRULE'
"""What a revision keeps, what its change covers, and when to say so.

`kept` and `inside` both answer off the script the tool itself settled, which
is the only reason they agree with the rest of the tool on a file that repeats
its lines: several scripts of the same length exist for almost any pair of
revisions of one, and they disagree about which copy of a repeated line
survived.

`should_raise` is the one that is not a question about this revision at all. A
note is raised when its line becomes part of a change. While it stays part of
one the reviewer has already been asked, so raising again says nothing, and
the answer therefore depends on where the note stood at the revision before -
which only a board that walks the store one revision at a time can supply.
"""

from scr import grp, pin


def kept(before, after):
    out = {}
    for kind, i, j in pin.reading(before, after, pin.script(before, after)):
        if kind == "K":
            out[i] = j
    return out


def inside(line, before, after):
    for chunk in grp.spans(before, after):
        if line in chunk:
            return True
    return False


def should_raise(inside_now, inside_before):
    return inside_now and not inside_before
ENDRULE
