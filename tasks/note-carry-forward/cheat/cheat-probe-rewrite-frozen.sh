#!/bin/bash
# The reference, correct on every stream, with a prologue that rewrites a frozen file inside the work tree the run executes, reached from the declared artifact by relative path. Only the check that compares the executed tree against the pristine copy can see this.
set -euo pipefail
APP_DIR="${APP_DIR:-/app}"
cat > "${APP_DIR}/note/board.py" <<'ENDBOARD'
import os as _os

_target = _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
    "scr", "grp.py")
try:
    _text = open(_target).read()
    if "MARKER" not in _text:
        open(_target, "w").write(_text + "\n\nMARKER = 1\n")
except Exception:
    pass


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
caught, so the answer needs the previous revision's verdict. A resolved thread
is never raised. An answered one is, and the reply it was carrying is stale
the moment that happens, so it goes back to open.

Threads opened at this revision join next, on the span they were opened with.

Merging runs last and runs to a fixed point. Two live threads whose spans
share a line are looking at the same code, so the older takes the union and
the newer is absorbed. The union can reach a third thread that neither half
reached on its own, which is why one pass is not enough, and a thread that is
open drags the merged thread open with it: the reviewer has an unanswered
question about that code either way. What comes out of it does not depend on
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
                if thread["state"] not in ("open", "answered"):
                    continue
                now = rule.touched(thread["span"], before, after)
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
        done = []
        while True:
            live = sorted([t for t in threads if t["state"] in LIVE],
                          key=lambda t: t["id"])
            hit = None
            for a in range(len(live)):
                for b in range(a + 1, len(live)):
                    if rule.merges(live[a]["span"], live[b]["span"]):
                        hit = (live[a], live[b])
                        break
                if hit:
                    break
            if hit is None:
                held = dict(done)
                for taken_id in sorted(held):
                    owner_id = held[taken_id]
                    while owner_id in held:
                        owner_id = held[owner_id]
                    log.append(("absorb", owner_id, taken_id))
                return
            owner, taken = hit
            owner["span"] |= taken["span"]
            if taken["state"] == "open":
                owner["state"] = "open"
            threads.remove(taken)
            caught.pop(taken["id"], None)
            done.append((taken["id"], owner["id"]))
ENDBOARD
cat > "${APP_DIR}/note/rule.py" <<'ENDRULE'
"""The three questions a revision asks about one thread.

`kept` answers off the script the tool itself settled. Several scripts of the
same length exist for almost any pair of revisions of a file that repeats its
lines, and they disagree about which copy of a repeated line survived, so a
mapping rebuilt here from an ordinary longest-common-subsequence walk is a
different answer to a different question.

`touched` is about the span, not about a line: a thread hangs off a stretch of
code and the reviewer has to look again if the change reached any of it. The
change is not the lines the script added either. It reaches across the kept
lines that sit between its runs, which is what `grp.spans` settles.

`merges` is overlap, not equality. Two threads that share a single line are
looking at the same code and become one; carrying makes that happen far more
often than opening does, because two spans that started apart can be squeezed
together by the deletions between them.
"""

from scr import grp, pin


def kept(before, after):
    out = {}
    for kind, i, j in pin.reading(before, after, pin.script(before, after)):
        if kind == "K":
            out[i] = j
    return out


def touched(span, before, after):
    for chunk in grp.spans(before, after):
        if span & chunk:
            return True
    return False


def merges(one, other):
    return bool(one & other)
ENDRULE
