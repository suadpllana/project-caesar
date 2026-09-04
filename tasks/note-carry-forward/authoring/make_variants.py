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

MERGE_BY_COMPONENTS = BOARD[:BOARD.index("    def _merge(self, threads, caught, log):")] + \
    '''    def _merge(self, threads, caught, log):
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
'''

MAPPING_FROM_OPS = RULE.replace(
    '''def kept(before, after):
    out = {}
    for kind, i, j in pin.reading(before, after, pin.script(before, after)):
        if kind == "K":
            out[i] = j
    return out''',
    '''def kept(before, after):
    walk = pin.reading(before, after, pin.script(before, after))
    return dict((step[1], step[2]) for step in walk if step[0] == "K")''', 1)

TOUCHED_WRITTEN_OUT = RULE.replace(
    '''    for chunk in chunks:
        if span & chunk:
            return True
    return False''',
    '''    reached = set()
    for chunk in chunks:
        reached |= chunk
    return not span.isdisjoint(reached)''', 1)

# The pair has to be settled once rather than once per thread, but nothing says
# how it is held. This one keeps the last pair in a slot instead of a mapping,
# so the resource gate grades the invariant and not one way of writing it down.
SETTLED_IN_A_SLOT = RULE.replace(
    '''_SETTLED = {}


def touched(span, before, after):
    key = (tuple(before), tuple(after))
    chunks = _SETTLED.get(key)
    if chunks is None:
        _SETTLED.clear()
        chunks = _SETTLED[key] = grp.spans(before, after)''',
    '''_LAST = [None, None, None]


def touched(span, before, after):
    if _LAST[0] != before or _LAST[1] != after:
        _LAST[0] = list(before)
        _LAST[1] = list(after)
        _LAST[2] = grp.spans(before, after)
    chunks = _LAST[2]''', 1)

PRECOMPUTED = BOARD.replace(
    '''        for step in range(1, self.store.count()):
            before = self.store.at(step - 1)
            after = self.store.at(step)
            carried = rule.kept(before, after)''',
    '''        pairs = []
        for step in range(1, self.store.count()):
            pairs.append((self.store.at(step - 1), self.store.at(step)))
        for step in range(1, self.store.count()):
            before, after = pairs[step - 1]
            carried = rule.kept(before, after)''', 1)

OVERRIDES = {
    "ok-merge-by-components": {"board.py": MERGE_BY_COMPONENTS},
    "ok-precomputed-pairs": {"board.py": PRECOMPUTED},
    "ok-mapping-from-ops": {"rule.py": MAPPING_FROM_OPS},
    "ok-touched-written-out": {"rule.py": TOUCHED_WRITTEN_OUT},
    "ok-settled-in-a-slot": {"rule.py": SETTLED_IN_A_SLOT},
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
