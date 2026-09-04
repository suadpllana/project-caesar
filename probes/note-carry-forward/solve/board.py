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
        self._open(live, log, waiting.get(0, []), self.store.at(0))
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
            live[:] = held
            for note in sorted(live, key=lambda n: n["id"]):
                if rule.raised(note["line"], before, after):
                    log.append(("raise", note["id"]))
            self._open(live, log, waiting.get(step, []), after)
        live.sort(key=lambda n: n["id"])
        return live, log

    def _open(self, live, log, arrivals, rev):
        for nid, line in sorted(arrivals):
            if line < 0 or line >= len(rev):
                continue
            owner = None
            for note in live:
                if note["line"] == line:
                    owner = note["id"]
                    break
            if owner is None:
                live.append({"id": nid, "line": line})
            else:
                log.append(("absorb", min(owner, nid), max(owner, nid)))
                if nid < owner:
                    for note in live:
                        if note["id"] == owner:
                            note["id"] = nid
