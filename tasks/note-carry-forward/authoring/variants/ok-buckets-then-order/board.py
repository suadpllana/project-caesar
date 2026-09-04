"""Correct, arranged the other way round: the events are collected per
revision into buckets and ordered at the end, rather than appended as the walk
goes. Same rule, opposite shape."""

from note import rule


class Board(object):
    def __init__(self, store):
        self.store = store

    def build(self, opens):
        steps = self.store.count()
        born = {}
        for at, nid, line in opens:
            born.setdefault(at, []).append((nid, line))
        events = dict((t, {"retire": [], "raise": [], "absorb": []}) for t in range(steps))
        where = {}
        for nid, line in sorted(born.get(0, [])):
            where[nid] = line
        self._collide(where, 0, events)
        for t in range(1, steps):
            before = self.store.at(t - 1)
            after = self.store.at(t)
            carried = rule.kept(before, after)
            for nid in sorted(where):
                if where[nid] in carried:
                    where[nid] = carried[where[nid]]
                else:
                    events[t]["retire"].append(nid)
            for nid in events[t]["retire"]:
                del where[nid]
            for nid in sorted(where):
                if rule.raised(where[nid], before, after):
                    events[t]["raise"].append(nid)
            for nid, line in sorted(born.get(t, [])):
                where[nid] = line
            self._collide(where, t, events)
        log = []
        for t in range(steps):
            for nid in sorted(events[t]["retire"]):
                log.append(("retire", nid))
            for nid in events[t]["raise"]:
                log.append(("raise", nid))
            for nid, owner in sorted(events[t]["absorb"]):
                log.append(("absorb", owner, nid))
        live = [{"id": nid, "line": where[nid]} for nid in sorted(where)]
        return live, log

    def _collide(self, where, t, events):
        seen = {}
        for nid in sorted(where):
            owner = seen.get(where[nid])
            if owner is None:
                seen[where[nid]] = nid
            else:
                events[t]["absorb"].append((nid, owner))
        for nid, _owner in events[t]["absorb"]:
            if nid in where:
                del where[nid]
