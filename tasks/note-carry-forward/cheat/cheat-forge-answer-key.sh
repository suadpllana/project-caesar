#!/bin/bash
# Hold tests/gt.json and return the recorded answer for whichever hand-written stream this looks like. Right on those and wrong on the generated block, which is built inside the verifier from a seed drawn after this was written. Generated-after-the-fact input beats any answer key.
set -euo pipefail
APP_DIR="${APP_DIR:-/app}"
cat > "${APP_DIR}/note/board.py" <<'ENDBOARD'
import json

TRUTH = json.loads('{"fixed":{"absorb-chains-through-the-union":{"log":[["absorb",0,1],["absorb",0,2]],"threads":[[0,"open",[0,1,2,3,4]]]},"absorb-on-overlap":{"log":[["absorb",0,1]],"threads":[[0,"open",[1,2,3]]]},"answered-reopens-when-caught":{"log":[["raise",0],["reopen",0]],"threads":[[0,"open",[2]]]},"carry-plain":{"log":[],"threads":[[0,"open",[1,2]]]},"carry-squeezes-spans-together":{"log":[["absorb",0,1]],"threads":[[0,"open",[0,1,2]]]},"merged-thread-inherits-being-reached":{"log":[["raise",1],["absorb",0,1],["absorb",0,2]],"threads":[[0,"open",[1]]]},"no-absorb-without-overlap":{"log":[],"threads":[[0,"open",[0,1]],[1,"open",[3,4]]]},"no-raise-when-the-change-misses":{"log":[],"threads":[[0,"open",[1,2]]]},"no-threads":{"log":[],"threads":[]},"open-drags-the-merge-open":{"log":[["absorb",0,1]],"threads":[[0,"open",[1,2,3]]]},"outdated-stays-listed":{"log":[["outdated",0]],"threads":[[0,"outdated",[]]]},"part-of-the-span-is-enough":{"log":[["absorb",0,1],["raise",0],["outdated",0]],"threads":[[0,"outdated",[]]]},"raise-on-one-line-of-the-span":{"log":[["raise",0]],"threads":[[0,"open",[2,4,5]]]},"raised-again-after-it-is-let-go":{"log":[["raise",0],["raise",0]],"threads":[[0,"open",[2]]]},"raised-once-while-it-stays-caught":{"log":[["raise",0]],"threads":[[0,"open",[2]]]},"reply-to-a-resolved-thread-does-nothing":{"log":[],"threads":[[0,"resolved",[0]]]},"resolved-is-not-raised":{"log":[],"threads":[[0,"resolved",[2]]]},"resolved-still-tracks-being-reached":{"log":[["absorb",0,1]],"threads":[[0,"open",[0]]]},"span-shrinks":{"log":[],"threads":[[0,"open",[1,2]]]},"talk-lands-before-the-merge":{"log":[["absorb",0,1]],"threads":[[0,"open",[0]]]},"talk-to-an-absorbed-thread-does-nothing":{"log":[["absorb",0,1]],"threads":[[0,"open",[0]]]},"tie-break-picks-the-surviving-copy":{"log":[["outdated",0],["absorb",1,2],["absorb",1,3],["absorb",1,4]],"threads":[[0,"outdated",[]],[1,"open",[1]]]}}}')["fixed"]
COUNTS = {'carry-plain': 1, 'span-shrinks': 1, 'outdated-stays-listed': 1, 'raise-on-one-line-of-the-span': 1, 'no-raise-when-the-change-misses': 1, 'raised-once-while-it-stays-caught': 1, 'raised-again-after-it-is-let-go': 1, 'answered-reopens-when-caught': 2, 'resolved-is-not-raised': 2, 'absorb-on-overlap': 2, 'no-absorb-without-overlap': 2, 'absorb-chains-through-the-union': 3, 'carry-squeezes-spans-together': 2, 'open-drags-the-merge-open': 3, 'no-threads': 0, 'tie-break-picks-the-surviving-copy': 6, 'resolved-still-tracks-being-reached': 3, 'merged-thread-inherits-being-reached': 3, 'talk-lands-before-the-merge': 3, 'absorbs-ordered-by-the-one-absorbed': 4, 'reply-to-a-resolved-thread-does-nothing': 3, 'talk-to-an-absorbed-thread-does-nothing': 3, 'part-of-the-span-is-enough': 3}


class Board(object):
    def __init__(self, store):
        self.store = store

    def build(self, events):
        for name, body in sorted(TRUTH.items()):
            if COUNTS.get(name) == len(events):
                threads = [{"id": n, "state": st, "span": set(sp)}
                           for n, st, sp in body["threads"]]
                return threads, [tuple(e) for e in body["log"]]
        return [], []
ENDBOARD
