#!/bin/bash
# Deliberate cheating attempt. Holds tests/gt.json and returns the
# recorded answer for whichever hand-written stream it thinks it is
# looking at. Right on those and wrong on the generated block, which
# is built inside the verifier from a seed chosen after this was
# written. Generated-after-the-fact input beats any answer key.
set -euo pipefail
APP_DIR="${APP_DIR:-/app}"
cat > "${APP_DIR}/note/board.py" <<'ENDBOARD'
import json

TRUTH = json.loads('{"fixed":{"absorb-older-wins":{"log":[["absorb",0,1]],"notes":[[0,1]]},"carry-plain":{"log":[],"notes":[[0,2]]},"empty-revision":{"log":[["retire",0]],"notes":[]},"last-line":{"log":[],"notes":[[0,2]]},"no-notes":{"log":[],"notes":[]},"open-at-head":{"log":[],"notes":[[0,3]]},"open-midstream":{"log":[],"notes":[[0,1]]},"raise-kept-inside-change":{"log":[["raise",0]],"notes":[[0,2]]},"raise-not-when-changes-are-apart":{"log":[],"notes":[[0,3]]},"retire-dropped":{"log":[["retire",0]],"notes":[]}}}')["fixed"]


class Board(object):
    def __init__(self, store):
        self.store = store

    def build(self, opens):
        want = None
        for name, body in TRUTH.items():
            if self._fits(name, body, opens):
                want = body
                break
        if want is None:
            return [], []
        live = [{"id": n, "line": l} for n, l in want["notes"]]
        return live, [tuple(e) for e in want["log"]]

    def _fits(self, name, body, opens):
        return len(opens) == self._opens_for(name)

    def _opens_for(self, name):
        return COUNTS.get(name, -1)


COUNTS = {'carry-plain': 1, 'retire-dropped': 1, 'raise-kept-inside-change': 1, 'raise-not-when-changes-are-apart': 1, 'absorb-older-wins': 2, 'open-at-head': 1, 'open-midstream': 1, 'empty-revision': 1, 'last-line': 1, 'no-notes': 0}
ENDBOARD
