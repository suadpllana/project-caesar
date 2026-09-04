"""Generate authoring/variants/ from the reference plus one declared override.

A variant is a correct board that made a different implementation choice. Each
must score 1. Hand-copied variants drift the moment the reference changes, and
the symptom is every correct implementation disagreeing at once, so they are
written from the reference here instead.
"""
import pathlib

TASK = pathlib.Path(__file__).resolve().parent.parent
BOARD = (TASK / "solution" / "board.py").read_text()
RULE = (TASK / "solution" / "rule.py").read_text()

PER_NOTE = '''"""Correct, arranged the other way round: each note is followed on its own
from the revision it was opened at to the head, and the events are collected
per revision and ordered at the end. Same rule, opposite shape."""

from scr import grp, pin
from note import rule


class Board(object):
    def __init__(self, store):
        self.store = store

    def build(self, opens):
        steps = self.store.count()
        maps = []
        spans = []
        for t in range(1, steps):
            before = self.store.at(t - 1)
            after = self.store.at(t)
            maps.append(rule.kept(pin.reading(before, after, pin.script(before, after))))
            spans.append(grp.spans(before, after))
        born = {}
        for at, nid, line in opens:
            born.setdefault(at, []).append((nid, line))
        events = dict((t, {"retire": [], "raise": [], "absorb": []}) for t in range(steps))
        where = {}
        for nid, line in sorted(born.get(0, [])):
            where[nid] = line
        self._collide(where, 0, events)
        for t in range(1, steps):
            table = maps[t - 1]
            for nid in sorted(where):
                if where[nid] in table:
                    where[nid] = table[where[nid]]
                else:
                    events[t]["retire"].append(nid)
            for nid in events[t]["retire"]:
                del where[nid]
            for nid in sorted(where):
                if rule.raised(where[nid], spans[t - 1]):
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
'''

OVERRIDES = {
    "ok-per-note": {"board.py": PER_NOTE},
    "ok-precomputed-scripts": {"board.py": BOARD.replace(
        '''        for step in range(1, self.store.count()):
            before = self.store.at(step - 1)
            after = self.store.at(step)
            keep = rule.kept(pin.reading(before, after, pin.script(before, after)))
            spans = grp.spans(before, after)
''',
        '''        ready = []
        for step in range(1, self.store.count()):
            before = self.store.at(step - 1)
            after = self.store.at(step)
            ready.append((rule.kept(pin.reading(before, after, pin.script(before, after))),
                          grp.spans(before, after)))
        for step in range(1, self.store.count()):
            keep, spans = ready[step - 1]
''', 1)},
    "ok-mapping-from-ops": {"rule.py": RULE.replace(
        '''def kept(walk):
    out = {}
    for kind, i, j in walk:
        if kind == "K":
            out[i] = j
    return out''',
        '''def kept(walk):
    out = {}
    seen = 0
    for entry in walk:
        if entry[0] == "K":
            out[entry[1]] = entry[2]
            seen += 1
    assert seen == len(out)
    return out''', 1)},
}


def main():
    root = TASK / "authoring" / "variants"
    for name, overrides in OVERRIDES.items():
        for fname, text in overrides.items():
            if text in (BOARD, RULE):
                raise SystemExit("override for %s/%s changed nothing" % (name, fname))
        d = root / name
        d.mkdir(parents=True, exist_ok=True)
        for fname, base in (("board.py", BOARD), ("rule.py", RULE)):
            with open(d / fname, "w", newline="\n") as fh:
                fh.write(overrides.get(fname, base))
        with open(d / "solve.sh", "w", newline="\n") as fh:
            fh.write('#!/bin/bash\nset -euo pipefail\n'
                     'HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
                     'APP_DIR="${APP_DIR:-/app}"\n'
                     'cp "${HERE}/board.py" "${APP_DIR}/note/board.py"\n'
                     'cp "${HERE}/rule.py"  "${APP_DIR}/note/rule.py"\n')
        (d / "solve.sh").chmod(0o755)
        print("wrote variant", name)


if __name__ == "__main__":
    main()
