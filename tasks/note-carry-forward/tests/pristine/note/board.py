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
        seen = {}
        held = []
        for note in live:
            owner = seen.get(note["line"])
            if owner is None:
                seen[note["line"]] = note["id"]
                held.append(note)
            else:
                log.append(("absorb", owner, note["id"]))
        return held, log
