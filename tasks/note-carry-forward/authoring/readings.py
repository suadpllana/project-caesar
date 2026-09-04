"""Every wrong reading of the board rule, measured against the reference.

Answers the question the difficulty argument rests on: does a plausible
misreading move a real share of the graded streams, or is it a lottery ticket
that a hand-written set would only catch by luck? Run it after any change to
the rule.

    python3 authoring/readings.py 500
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


def _changes(walk, context=pin.CONTEXT, runs=False):
    """The moves of a walk cut into changes. `runs` cuts at every kept line,
    which is the reading that misses the merging the tool does."""
    out = []
    cur = None
    since = context
    for step in walk:
        if step[0] == "K":
            since += 1
            if cur is not None and (runs or since >= context):
                out.append(cur)
                cur = None
            continue
        if cur is None:
            cur = []
        since = 0
        cur.append(step)
    if cur is not None:
        out.append(cur)
    return out


def _carry(walk, **kw):
    """Where each line of the before side lands: kept lines where the script
    keeps them, dropped lines on whatever their own change put in their
    place."""
    out = dict((i, j) for kind, i, j in walk if kind == "K")
    back = kw.pop("back", False)
    for change in _changes(walk, **kw):
        gone = [i for kind, i, j in change if kind == "D"]
        came = [j for kind, i, j in change if kind == "A"]
        if back:
            gone = gone[::-1]
        for i, j in zip(gone, came):
            out[i] = j
    return out


def _walk(before, after):
    return pin.reading(before, after, pin.script(before, after))


def _pinned(before, after):
    return _carry(_walk(before, after))


def _no_pairing(before, after):
    return dict((i, j) for kind, i, j in _walk(before, after) if kind == "K")


def _one_run(before, after):
    return _carry(_walk(before, after), runs=True)


def _near_context(before, after):
    return _carry(_walk(before, after), context=pin.CONTEXT + 1)


def _reverse_pairs(before, after):
    return _carry(_walk(before, after), back=True)


def _textbook(before, after):
    """The mapping an ordinary longest-common-subsequence walk gives, carried
    the same way afterwards, so what this measures is the script and not the
    carrying."""
    n, m = len(before), len(after)
    best = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            if before[i] == after[j]:
                best[i][j] = best[i + 1][j + 1] + 1
            else:
                best[i][j] = max(best[i + 1][j], best[i][j + 1])
    walk = []
    i = j = 0
    while i < n or j < m:
        if i < n and j < m and before[i] == after[j] \
                and best[i][j] == best[i + 1][j + 1] + 1:
            walk.append(("K", i, j))
            i += 1
            j += 1
        elif i < n and (j >= m or best[i + 1][j] >= best[i][j + 1]):
            walk.append(("D", i, None))
            i += 1
        else:
            walk.append(("A", None, j))
            j += 1
    return _carry(walk)


def _difflib(before, after):
    """The same, off the standard library's matcher."""
    walk = []
    i = j = 0
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
            None, before, after, autojunk=False).get_opcodes():
        if tag == "equal":
            for step in range(i2 - i1):
                walk.append(("K", i1 + step, j1 + step))
            continue
        for x in range(i1, i2):
            walk.append(("D", x, None))
        for y in range(j1, j2):
            walk.append(("A", None, y))
    return _carry(walk)


MAPS = {"textbook": _textbook, "difflib": _difflib,
        "no-pairing": _no_pairing, "pair-in-one-run": _one_run,
        "near-context": _near_context, "reverse-pairs": _reverse_pairs}


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
         "absorb-newer", "no-absorb", "retire-silent",
         "no-pairing", "pair-in-one-run", "near-context", "reverse-pairs"]


def _enumerated(mode):
    """Does a hand-written stream separate this reading on its own?

    A reading that moves few generated streams is not automatically a lottery
    ticket. It is one only when nothing in the enumerated set names it, so
    that its failure surfaces as "some of three hundred streams are wrong"
    rather than as a stream whose name says which rule was misread.
    """
    for item in scen.FIXED:
        if run(item["revs"], item["opens"], mode) != run(item["revs"], item["opens"], "ref"):
            return item["name"]
    return None


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    streams = scen.generated(count, 11)
    hits = dict((m, 0) for m in MODES)
    for item in streams:
        base = run(item["revs"], item["opens"], "ref")
        for mode in MODES:
            if run(item["revs"], item["opens"], mode) != base:
                hits[mode] += 1
    print("streams %d generated, %d written by hand" % (len(streams), len(scen.FIXED)))
    loose = []
    for mode in MODES:
        share = 100.0 * hits[mode] / len(streams)
        named = _enumerated(mode)
        print("   %-18s moves %5d  (%4.1f%%)   %s"
              % (mode, hits[mode], share, named or "NOT NAMED BY ANY CASE"))
        if named is None and share < 10.0:
            loose.append(mode)
    if loose:
        print("FAIL a reading that moves under a tenth of the set and that no "
              "enumerated case names is a lottery ticket: %s" % ", ".join(loose))
        return 1
    print("every wrong reading is either common on the graded set or named by a case")
    return 0


if __name__ == "__main__":
    sys.exit(main())
