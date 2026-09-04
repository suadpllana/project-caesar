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
    log = []

    def settle(live):
        seen = {}
        held = []
        taken = []
        order = sorted(live, key=lambda n: -n["id"]) if mode == "absorb-newer" \
            else sorted(live, key=lambda n: n["id"])
        for note in order:
            owner = seen.get(note["line"])
            if owner is None or mode == "no-absorb":
                seen.setdefault(note["line"], note["id"])
                held.append(note)
            elif mode == "absorb-newer":
                taken.append((owner, note["id"]))
                held.append(note)
            else:
                taken.append((note["id"], owner))
        for a, b in sorted(taken):
            log.append(("absorb", b, a) if mode == "absorb-newer" else ("absorb", b, a))
        live[:] = sorted(held, key=lambda n: n["id"])

    if mode == "origin-to-head":
        head = len(revs) - 1
        live = []
        for at, nid, line in sorted(opens, key=lambda o: o[1]):
            table = _pinned(revs[at], revs[head])
            if line in table:
                live.append({"id": nid, "line": table[line]})
            else:
                log.append(("retire", nid))
        if head > 0:
            for note in live:
                if any(note["line"] in c for c in grp.spans(revs[head - 1], revs[head])):
                    log.append(("raise", note["id"]))
        settle(live)
        return sorted((n["id"], n["line"]) for n in live), log

    live = [{"id": n, "line": l} for n, l in sorted(born.get(0, []))]
    settle(live)
    for step in range(1, len(revs)):
        before, after = revs[step - 1], revs[step]
        table = carry(before, after)
        held, lost = [], []
        for note in live:
            if note["line"] in table:
                note["line"] = table[note["line"]]
                held.append(note)
            else:
                lost.append(note["id"])
        if mode != "retire-silent":
            for nid in sorted(lost):
                log.append(("retire", nid))
        live = held
        spans = grp.spans(before, after)
        landed = set(_pinned(before, after).values())
        for note in sorted(live, key=lambda n: n["id"]):
            if mode == "raise-added-only":
                hit = note["line"] not in landed
            else:
                hit = any(note["line"] in c for c in spans)
            if hit:
                log.append(("raise", note["id"]))
        for nid, line in sorted(born.get(step, [])):
            live.append({"id": nid, "line": line})
        settle(live)
    return sorted((n["id"], n["line"]) for n in live), log


MODES = ["origin-to-head", "textbook", "difflib", "raise-added-only",
         "absorb-newer", "no-absorb", "retire-silent"]


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
