from note import rule

STATES = ("open", "answered", "resolved", "outdated")
EVENTS = ("outdated", "raise", "reopen", "absorb")
LIVE = STATES[:3]


class Board(object):
    def __init__(self, store):
        self.store = store

    def build(self, events):
        opened = {}
        talk = {}
        for step, kind, payload in events:
            if kind == "open":
                opened.setdefault(step, []).append(payload)
            else:
                talk.setdefault(step, []).append((kind, payload))
        threads = []
        log = []
        self._join(threads, opened.get(0, []))
        self._talk(threads, talk.get(0, []))
        self._merge(threads, log)
        for step in range(1, self.store.count()):
            before = self.store.at(step - 1)
            after = self.store.at(step)
            carried = rule.kept(before, after)
            gone = []
            for thread in threads:
                thread["span"] = set(carried[x] for x in thread["span"] if x in carried)
                if not thread["span"]:
                    gone.append(thread)
            for thread in sorted(gone, key=lambda t: t["id"]):
                log.append(("outdated", thread["id"]))
                threads.remove(thread)
            for thread in sorted(threads, key=lambda t: t["id"]):
                if thread["state"] != "open":
                    continue
                if rule.touched(thread["span"], before, after):
                    log.append(("raise", thread["id"]))
            self._join(threads, opened.get(step, []))
            self._talk(threads, talk.get(step, []))
            self._merge(threads, log)
        threads.sort(key=lambda t: t["id"])
        return threads, log

    def _join(self, threads, fresh):
        for nid, span in fresh:
            threads.append({"id": nid, "span": set(span), "state": "open"})

    def _talk(self, threads, said):
        by_id = dict((t["id"], t) for t in threads)
        for kind, nid in said:
            thread = by_id.get(nid)
            if thread is None:
                continue
            if kind == "reply" and thread["state"] == "open":
                thread["state"] = "answered"
            elif kind == "resolve" and thread["state"] in ("open", "answered"):
                thread["state"] = "resolved"

    def _merge(self, threads, log):
        live = sorted([t for t in threads if t["state"] in LIVE], key=lambda t: t["id"])
        taken = []
        done = []
        for a in range(len(live)):
            if live[a] in taken:
                continue
            for b in range(a + 1, len(live)):
                if live[b] in taken:
                    continue
                if rule.merges(live[a]["span"], live[b]["span"]):
                    live[a]["span"] |= live[b]["span"]
                    taken.append(live[b])
                    done.append((live[b]["id"], live[a]["id"]))
        held = dict(done)
        for taken_id in sorted(held):
            owner_id = held[taken_id]
            while owner_id in held:
                owner_id = held[owner_id]
            log.append(("absorb", owner_id, taken_id))
        for thread in taken:
            threads.remove(thread)
