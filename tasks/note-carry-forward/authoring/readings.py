"""Every wrong reading of the board rule, measured against the reference.

Answers the question the difficulty argument rests on: does a plausible
misreading move a real share of the graded streams, or is it a lottery ticket
that a hand-written set would only catch by luck? Run it after any change to
the rule.

    python3 authoring/readings.py 500
"""
import pathlib
import random
import sys

TASK = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "environment" / "app_src"))
sys.path.insert(0, str(TASK / "tests"))

import scen  # noqa: E402
from scr import grp, pin  # noqa: E402


def _pinned(before, after):
    return dict((i, j) for kind, i, j in
                pin.reading(before, after, pin.script(before, after)) if kind == "K")


def _textbook(before, after):
    n, m = len(before), len(after)
    best = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            if before[i] == after[j]:
                best[i][j] = best[i + 1][j + 1] + 1
            else:
                best[i][j] = max(best[i + 1][j], best[i][j + 1])
    out = {}
    i = j = 0
    while i < n and j < m:
        if before[i] == after[j] and best[i][j] == best[i + 1][j + 1] + 1:
            out[i] = j
            i += 1
            j += 1
        elif best[i + 1][j] >= best[i][j + 1]:
            i += 1
        else:
            j += 1
    return out


def _difflib(before, after):
    import difflib
    out = {}
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
            None, before, after, autojunk=False).get_opcodes():
        if tag == "equal":
            for d in range(i2 - i1):
                out[i1 + d] = j1 + d
    return out


MAPS = {"textbook": _textbook, "difflib": _difflib}


def run(revs, opens, mode="ref"):
    carry = MAPS.get(mode, _pinned)
    born = {}
    for at, nid, line in opens:
        born.setdefault(at, []).append((nid, line))
    where = {}
    was = {}
    log = []

    def settle():
        seen = {}
        taken = []
        order = sorted(where, reverse=True) if mode == "absorb-newer" else sorted(where)
        for nid in order:
            owner = seen.get(where[nid])
            if owner is None or mode == "no-absorb":
                seen.setdefault(where[nid], nid)
            else:
                taken.append((nid, owner) if mode != "absorb-newer" else (owner, nid))
        for a, b in sorted(taken):
            log.append(("absorb", b, a))
            where.pop(a, None)
            was.pop(a, None)

    if mode == "origin-to-head":
        head = len(revs) - 1
        for at, nid, line in sorted(opens, key=lambda o: o[1]):
            table = _pinned(revs[at], revs[head])
            if line in table:
                where[nid] = table[line]
                was[nid] = False
            else:
                log.append(("retire", nid))
        if head > 0:
            spans = grp.spans(revs[head - 1], revs[head])
            for nid in sorted(where):
                if any(where[nid] in c for c in spans):
                    log.append(("raise", nid))
        settle()
        return sorted(where.items()), log

    for nid, line in sorted(born.get(0, [])):
        where[nid] = line
        was[nid] = False
    settle()
    for step in range(1, len(revs)):
        before, after = revs[step - 1], revs[step]
        table = carry(before, after)
        lost = []
        for nid in sorted(where):
            if where[nid] in table:
                where[nid] = table[where[nid]]
            else:
                lost.append(nid)
        for nid in lost:
            if mode != "retire-silent":
                log.append(("retire", nid))
            where.pop(nid); was.pop(nid, None)
        spans = grp.spans(before, after)
        landed = set(_pinned(before, after).values())
        for nid in sorted(where):
            if mode == "raise-added-only":
                now = where[nid] not in landed
            else:
                now = any(where[nid] in c for c in spans)
            if mode == "level-raise":
                fire = now
            else:
                fire = now and not was[nid]
            if fire:
                log.append(("raise", nid))
            was[nid] = now
        for nid, line in sorted(born.get(step, [])):
            where[nid] = line
            was[nid] = False
        settle()
    return sorted(where.items()), log


MODES = ["origin-to-head", "level-raise", "textbook", "difflib",
         "raise-added-only", "absorb-newer", "no-absorb", "retire-silent"]


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    streams = scen.generated(count, 11)
    hits = dict((m, 0) for m in MODES)
    for item in streams:
        base = run(item["revs"], item["opens"], "ref")
        for mode in MODES:
            if run(item["revs"], item["opens"], mode) != base:
                hits[mode] += 1
    print("streams %d" % len(streams))
    weak = []
    for mode in MODES:
        share = 100.0 * hits[mode] / len(streams)
        print("   %-18s moves %5d  (%.1f%%)" % (mode, hits[mode], share))
        if share < 10.0:
            weak.append(mode)
    if weak:
        print("FAIL a reading under a tenth of the set is a lottery ticket: %s"
              % ", ".join(weak))
        return 1
    print("every wrong reading moves at least a tenth of the graded streams")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
