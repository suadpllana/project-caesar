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
