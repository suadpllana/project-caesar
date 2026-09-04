from scr import grp, pin
from note import rule


class Board(object):
    def __init__(self, store):
        self.store = store

    def build(self, opens):
        head = self.store.head()
        log = []
        live = []
        for at, nid, line in opens:
            here = self.store.at(at)
            there = self.store.at(head)
            walk = pin.reading(here, there, pin.script(here, there))
            keep = rule.kept(walk)
            if line in keep:
                live.append({"id": nid, "line": keep[line]})
            else:
                log.append(("retire", nid))
        if head > 0:
            before = self.store.at(head - 1)
            after = self.store.at(head)
            spans = grp.spans(before, after)
            for note in live:
                if rule.raised(note["line"], spans):
                    log.append(("raise", note["id"]))
        seen = {}
        for note in list(live):
            if note["line"] in seen:
                log.append(("absorb", seen[note["line"]], note["id"]))
                live.remove(note)
            else:
                seen[note["line"]] = note["id"]
        return live, log
