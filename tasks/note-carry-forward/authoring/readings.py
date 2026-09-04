"""Every wrong reading of the board rule, measured against the reference.

Answers the question the difficulty argument rests on: does a plausible
misreading move a real share of the graded streams, or is it a lottery ticket
a hand-written set would only catch by luck? Run it after any change to the
rule.

    python3 authoring/readings.py 400
"""
import difflib
import pathlib
import random
import sys

TASK = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "environment" / "app_src"))
sys.path.insert(0, str(TASK / "tests"))

import scen  # noqa: E402
from scr import grp, pin  # noqa: E402

LIVE = ("open", "answered", "resolved")


def _pinned(before, after):
    return dict((i, j) for kind, i, j in
                pin.reading(before, after, pin.script(before, after)) if kind == "K")


def _textbook(before, after):
    n, m = len(before), len(after)
    best = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            best[i][j] = (best[i + 1][j + 1] + 1 if before[i] == after[j]
                          else max(best[i + 1][j], best[i][j + 1]))
    out, i, j = {}, 0, 0
    while i < n and j < m:
        if before[i] == after[j] and best[i][j] == best[i + 1][j + 1] + 1:
            out[i] = j; i += 1; j += 1
        elif best[i + 1][j] >= best[i][j + 1]:
            i += 1
        else:
            j += 1
    return out


def _difflib_map(before, after):
    out = {}
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
            None, before, after, autojunk=False).get_opcodes():
        if tag == "equal":
            for d in range(i2 - i1):
                out[i1 + d] = j1 + d
    return out


MAPS = {"textbook": _textbook, "difflib": _difflib_map}


def run(revs, events, mode="ref"):
    carry = MAPS.get(mode, _pinned)
    opened, said = {}, {}
    for step, kind, payload in events:
        if kind == "open":
            opened.setdefault(step, []).append(payload)
        else:
            said.setdefault(step, []).append((kind, payload))
    span, state, caught, log = {}, {}, {}, []

    def join(t):
        for nid, lines in opened.get(t, []):
            span[nid] = set(lines); state[nid] = "open"; caught[nid] = False

    def talk(t):
        for kind, nid in said.get(t, []):
            if nid not in state:
                continue
            if kind == "reply" and state[nid] == "open":
                state[nid] = "answered"
            elif kind == "resolve" and state[nid] in ("open", "answered"):
                state[nid] = "resolved"

    def overlap(a, b):
        return a == b if mode == "merge-equality" else bool(a & b)

    def merge():
        done = []
        while True:
            live = sorted(n for n in span if state[n] != "outdated")
            pair = None
            for x in range(len(live)):
                for y in range(x + 1, len(live)):
                    if overlap(span[live[x]], span[live[y]]):
                        pair = (live[x], live[y]); break
                if pair:
                    break
            if pair is None:
                break
            owner, taken = pair
            if mode != "merge-keeps-own-span":
                span[owner] |= span[taken]
            if state[taken] == "open" and mode != "open-does-not-drag":
                state[owner] = "open"
            done.append((taken, owner))
            del span[taken]; del state[taken]; caught.pop(taken, None)
            if mode == "merge-one-pass":
                break
        for taken, owner in sorted(done):
            log.append(("absorb", owner, taken))

    join(0); talk(0); merge()
    for t in range(1, len(revs)):
        before, after = revs[t - 1], revs[t]
        table = carry(before, after)
        hunks = grp.spans(before, after)
        if mode == "touched-added":
            landed = set(_pinned(before, after).values())
        gone = []
        for nid in sorted(span):
            if state[nid] == "outdated":
                continue
            span[nid] = set(table[x] for x in span[nid] if x in table)
            if not span[nid]:
                gone.append(nid)
        for nid in gone:
            state[nid] = "outdated"; caught.pop(nid, None)
            log.append(("outdated", nid))
            if mode == "outdated-removed":
                del span[nid]; del state[nid]
        for nid in sorted(span):
            if state[nid] == "outdated":
                continue
            if state[nid] == "resolved" and mode != "raise-resolved":
                continue
            if mode == "touched-all":
                reached = set()
                for c in hunks:
                    reached |= c
                now = bool(span[nid]) and span[nid] <= reached
            elif mode == "touched-added":
                now = bool(span[nid] & landed) is False and bool(span[nid])
            else:
                now = any(span[nid] & c for c in hunks)
            fire = now if mode == "level-raise" else (now and not caught.get(nid, False))
            if fire:
                log.append(("raise", nid))
                if state[nid] == "answered" and mode != "no-reopen":
                    state[nid] = "open"; log.append(("reopen", nid))
            caught[nid] = now
        join(t); talk(t); merge()
    table = sorted([nid, state[nid], tuple(sorted(span[nid]))] for nid in span)
    return table, log


MODES = ["textbook", "difflib", "touched-all", "touched-added", "level-raise",
         "no-reopen", "raise-resolved", "outdated-removed", "merge-equality",
         "merge-one-pass", "merge-keeps-own-span", "open-does-not-drag"]


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    streams = scen.generated(count, 11)
    hits = dict((m, 0) for m in MODES)
    for item in streams:
        base = run(item["revs"], item["events"], "ref")
        for mode in MODES:
            if run(item["revs"], item["events"], mode) != base:
                hits[mode] += 1
    print("streams %d" % len(streams))
    weak = []
    for mode in MODES:
        share = 100.0 * hits[mode] / len(streams)
        print("   %-22s moves %5d  (%.1f%%)" % (mode, hits[mode], share))
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
