"""Generate authoring/variants/ from the reference plus one declared override.

A variant is a correct board that made a different implementation choice, and
each has to score 1. Hand-copied variants go stale the moment the reference
changes and the symptom is every correct implementation disagreeing at once,
so they are written from the reference here instead.
"""
import pathlib

TASK = pathlib.Path(__file__).resolve().parent.parent
BOARD = (TASK / "solution" / "board.py").read_text()
RULE = (TASK / "solution" / "rule.py").read_text()

PER_NOTE = '''"""Correct, arranged the other way round: the events are collected per
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
'''

PRECOMPUTED = BOARD.replace(
    '''        for step in range(1, self.store.count()):
            before = self.store.at(step - 1)
            after = self.store.at(step)
            carried = rule.kept(before, after)''',
    '''        ready = []
        for step in range(1, self.store.count()):
            ready.append((self.store.at(step - 1), self.store.at(step)))
        for step in range(1, self.store.count()):
            before, after = ready[step - 1]
            carried = rule.kept(before, after)''', 1)

MAPPING_FROM_OPS = RULE.replace(
    '''def kept(before, after):
    out = {}
    for kind, i, j in pin.reading(before, after, pin.script(before, after)):
        if kind == "K":
            out[i] = j
    return out''',
    '''def kept(before, after):
    walk = pin.reading(before, after, pin.script(before, after))
    return dict((entry[1], entry[2]) for entry in walk if entry[0] == "K")''', 1)

OVERRIDES = {
    "ok-buckets-then-order": {"board.py": PER_NOTE},
    "ok-precomputed-pairs": {"board.py": PRECOMPUTED},
    "ok-mapping-from-ops": {"rule.py": MAPPING_FROM_OPS},
}


def main():
    root = TASK / "authoring" / "variants"
    for name, overrides in OVERRIDES.items():
        for fname, text in overrides.items():
            base = BOARD if fname == "board.py" else RULE
            if text == base:
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
