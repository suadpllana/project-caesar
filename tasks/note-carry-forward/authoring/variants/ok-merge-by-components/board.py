"""The board of review threads, rebuilt from the store.

Nothing survives between requests, so the board is reconstructed by walking
the store from the first revision to the head. The walk carries three things a
board that recomputed from the endpoints could not: the span each thread has
been squeezed down to, the state its replies and resolutions left it in, and
whether the revision before this one had already caught it inside a change.

Four things happen when a revision lands, in this order and no other.

The carry maps every span through the script for that revision. A span that
loses every line leaves its thread outdated, which is a resting state: it
stays on the board with the empty span it ended on, and nothing later carries
it, raises it or merges it.

The raise is edge triggered, and it is about the span. A thread is raised when
the change first reaches any line it holds, and not again while it stays
caught, so the answer needs the previous revision's verdict. Being reached is
a fact about the span rather than about the thread's standing, so every thread
still on the board has it settled, resolved ones included: a resolved thread
is never raised, but a revision still reaches its lines or lets them go, and
that verdict is what a later raise is measured against once a merge has
dragged it open again. An answered thread is raised, and the reply it was
carrying is stale the moment that happens, so it goes back to open.

Threads opened at this revision join next, on the span they were opened with.

Merging runs last and runs to a fixed point. Two live threads whose spans
share a line are looking at the same code, so the older takes the union and
the newer is absorbed. The union can reach a third thread that neither half
reached on its own, which is why one pass is not enough, and a thread that is
open drags the merged thread open with it: the reviewer has an unanswered
question about that code either way. The same follows for being reached, for
the same reason it follows for the span: the survivor holds the union, so a
change that reached either half has reached what the survivor now holds. What comes out of it does not depend on
the order the pairs are found in: the spans settle into the connected groups of
the overlap graph and the oldest id in each group owns it. The log says so too.
It is ordered by the thread that was absorbed, and it names the thread that
ends up holding it rather than whichever one happened to reach it first, so a
board that hunts the pairs in another order still writes the same log.
"""

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
        caught = {}
        log = []
        self._join(threads, caught, opened.get(0, []))
        self._talk(threads, talk.get(0, []))
        self._merge(threads, caught, log)
        for step in range(1, self.store.count()):
            before = self.store.at(step - 1)
            after = self.store.at(step)
            carried = rule.kept(before, after)
            gone = []
            for thread in threads:
                if thread["state"] == "outdated":
                    continue
                thread["span"] = set(carried[x] for x in thread["span"] if x in carried)
                if not thread["span"]:
                    gone.append(thread)
            for thread in sorted(gone, key=lambda t: t["id"]):
                thread["state"] = "outdated"
                caught.pop(thread["id"], None)
                log.append(("outdated", thread["id"]))
            for thread in sorted(threads, key=lambda t: t["id"]):
                if thread["state"] == "outdated":
                    continue
                now = rule.touched(thread["span"], before, after)
                if thread["state"] != "resolved":
                    if now and not caught.get(thread["id"], False):
                        log.append(("raise", thread["id"]))
                        if thread["state"] == "answered":
                            thread["state"] = "open"
                            log.append(("reopen", thread["id"]))
                caught[thread["id"]] = now
            self._join(threads, caught, opened.get(step, []))
            self._talk(threads, talk.get(step, []))
            self._merge(threads, caught, log)
        threads.sort(key=lambda t: t["id"])
        return threads, log

    def _join(self, threads, caught, fresh):
        for nid, span in fresh:
            threads.append({"id": nid, "span": set(span), "state": "open"})
            caught[nid] = False

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

    def _merge(self, threads, caught, log):
        live = sorted([t for t in threads if t["state"] in LIVE],
                      key=lambda t: t["id"])
        seen = {}
        groups = []
        for thread in live:
            found = None
            for group in groups:
                if any(rule.merges(thread["span"], other["span"]) for other in group):
                    if found is None:
                        found = group
                        group.append(thread)
                    else:
                        found.extend(group)
                        group[:] = []
            if found is None:
                groups.append([thread])
        taken = []
        for group in groups:
            group = [t for t in group if t]
            if len(group) < 2:
                continue
            group.sort(key=lambda t: t["id"])
            owner = group[0]
            for other in group[1:]:
                owner["span"] |= other["span"]
                if other["state"] == "open":
                    owner["state"] = "open"
                taken.append((other["id"], owner["id"]))
                threads.remove(other)
                if caught.pop(other["id"], False):
                    caught[owner["id"]] = True
        for taken_id, owner_id in sorted(taken):
            log.append(("absorb", owner_id, taken_id))
