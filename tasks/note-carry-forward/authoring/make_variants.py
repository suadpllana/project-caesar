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
    '''
    out = {}
    for kind, i, j in walk:
        if kind == "K":
            out[i] = j
    for change in _changes(walk):
        gone = [i for kind, i, j in change if kind == "D"]
        came = [j for kind, i, j in change if kind == "A"]
        for i, j in zip(gone, came):
            out[i] = j
    return out''',
    '''
    out = dict((e[1], e[2]) for e in walk if e[0] == "K")
    for change in _changes(walk):
        pairs = zip([e[1] for e in change if e[0] == "D"],
                    [e[2] for e in change if e[0] == "A"])
        out.update(pairs)
    return out''', 1)

GROUPS_BY_GAPS = RULE.replace(
    RULE[RULE.index("    out = []\n    cur = None\n    since = CONTEXT"):
         RULE.index("def kept(before, after):")],
    '''
    spots = [k for k, step in enumerate(walk) if step[0] != "K"]
    inside = set(spots)
    for one, two in zip(spots, spots[1:]):
        if two - one - 1 < CONTEXT:
            inside.update(range(one + 1, two))
    out = []
    cur = []
    for k, step in enumerate(walk):
        if k in inside:
            if step[0] != "K":
                cur.append(step)
        elif cur:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out

''', 1)

OVERRIDES = {
    "ok-buckets-then-order": {"board.py": PER_NOTE},
    "ok-precomputed-pairs": {"board.py": PRECOMPUTED},
    "ok-mapping-from-ops": {"rule.py": MAPPING_FROM_OPS},
    "ok-changes-by-gaps": {"rule.py": GROUPS_BY_GAPS},
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
