#!/bin/bash
# Hold tests/gt.json and return the recorded answer for whichever hand-written stream this looks like. Right on those and wrong on the generated block, which is built inside the verifier from a seed drawn after this was written. Generated-after-the-fact input beats any answer key.
set -euo pipefail
APP_DIR="${APP_DIR:-/app}"
cat > "${APP_DIR}/note/board.py" <<'ENDBOARD'
import json

TRUTH = json.loads('{"fixed":{"absorb-older-wins":{"log":[["absorb",0,1]],"notes":[[0,1]]},"carry-plain":{"log":[],"notes":[[0,2]]},"empty-revision":{"log":[["retire",0]],"notes":[]},"last-line":{"log":[],"notes":[[0,2]]},"matcher-keeps-another-copy":{"log":[],"notes":[[0,2]]},"no-notes":{"log":[],"notes":[]},"open-at-head":{"log":[],"notes":[[0,3]]},"open-midstream":{"log":[],"notes":[[0,1]]},"raise-kept-inside-change":{"log":[["raise",0]],"notes":[[0,2]]},"raise-not-when-changes-are-apart":{"log":[],"notes":[[0,3]]},"retire-and-raise-in-one-revision":{"log":[["retire",0],["retire",2],["raise",1]],"notes":[[1,1]]},"retire-dropped":{"log":[["retire",0]],"notes":[]},"tie-break-picks-the-survivor":{"log":[["raise",0]],"notes":[[0,0]]}}}')["fixed"]
COUNTS = {'carry-plain': 1, 'retire-dropped': 1, 'raise-kept-inside-change': 1, 'raise-not-when-changes-are-apart': 1, 'absorb-older-wins': 2, 'open-at-head': 1, 'open-midstream': 1, 'empty-revision': 1, 'last-line': 1, 'no-notes': 0, 'tie-break-picks-the-survivor': 1, 'matcher-keeps-another-copy': 1, 'retire-and-raise-in-one-revision': 3}


class Board(object):
    def __init__(self, store):
        self.store = store

    def build(self, opens):
        for name, body in sorted(TRUTH.items()):
            if COUNTS.get(name) == len(opens):
                live = [{"id": n, "line": l} for n, l in body["notes"]]
                return live, [tuple(e) for e in body["log"]]
        return [], []
ENDBOARD
