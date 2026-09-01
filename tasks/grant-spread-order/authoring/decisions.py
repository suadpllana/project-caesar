"""The graded decisions the reference makes, as rows of integer features, for onelinecheck.

The contract is samples() -> {question: [(features, label), ...]}, where the features are
things an agent can read off the state at the moment the decision is taken and the label is
what the reference chose. tools/onelinecheck.py then searches for the shortest exact rule
over those features, and a graded decision that a two-term rule reproduces is an easiness
rejection waiting to happen.

Four questions are put, and they are deliberately the whole graded surface rather than the
flattering part of it:

  crosses-the-edge   given a record on a parent and a child below it, does the child end
                     up holding a copy? This is the materialisation rule, and it is short
                     by construction - scope, the bar, and the origin filter. It is
                     expected to come back with an exact rule and that is fine.
  survives-a-move    given a record a node was holding and a structural change, is the
                     node still holding it afterwards? The re-flow rule.
  verdict            the answer a question gets, from what is standing on the node.
  winner-is-own      whether the entry that carried the answer was placed on that node.

The last two are the ones that matter. If either of them is reproducible by a short rule
over what the state exposes, the ordering is guessable and the task is in trouble.
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(HERE))

import gen  # noqa: E402
import harness  # noqa: E402


def replay(text):
    """Everything the reference did on one journal, as the frozen driver reported it."""
    return harness.ref(text)


def state_at(rows, upto):
    """Rebuild node -> holdings by reading the driver's own event stream up to an op."""
    # The final dump is authoritative for the end state; for intermediate states we walk
    # the journal ourselves through the same reference policy, which is what harness does.
    out = {}
    for row in rows:
        if row[0] == "fin":
            out[row[1]] = (row[2], row[3], [tuple(x) for x in row[4]])
    return out


def cuts(text, many=6):
    """Intermediate states, taken by replaying prefixes of the journal.

    Sampling only the final state answers the wrong question: at the end of a journal
    almost every child mirrors its parent, so "did it cross" comes back with one outcome
    and onelinecheck rightly says that is not a decision. The interesting states are the
    ones just after a bar goes up.
    """
    lines = text.strip().split("\n")
    step = max(1, len(lines) // many)
    return ["\n".join(lines[:at]) + "\n"
            for at in range(step, len(lines) + 1, step)]


def edge_rows(texts):
    """For every parent record and every child, did the record cross?"""
    rows = []
    for text in texts:
        for piece in cuts(text):
            ev = replay(piece)
            fin = {r[1]: (r[2], r[3], [tuple(x) for x in r[4]])
                   for r in ev if r[0] == "fin"}
            for nid, (up, barred, held) in fin.items():
                if up == "-" or up not in fin:
                    continue
                above = fin[up][2]
                mine = set((r[4], r[0], r[1]) for r in held)
                for r in above:
                    sb, rt, vd, sc, og, bn = r
                    rows.append(({"sc": sc, "barred": barred,
                                  "origin_is_me": 1 if og == nid else 0,
                                  "verdict": vd},
                                 bool((og, sb, rt) in mine)))
    return rows


def ask_rows(texts):
    """For every question, what was decided and what the node had to decide it from."""
    verdicts, owns = [], []
    for text in texts:
        ev = replay(text)
        state = {}
        for row in ev:
            if row[0] == "fin":
                state[row[1]] = [tuple(x) for x in row[4]]
        asked = [r for r in ev if r[0] == "ak"]
        for row in asked:
            _, _, sb, nid, rt, vd, wsb, wog, wbn, wsc = row
            held = state.get(nid, [])
            live = [r for r in held if r[1] == rt and r[3] != 2]
            if not live:
                continue
            feats = {
                "candidates": len(live),
                "own_here": sum(1 for r in live if r[4] == nid),
                "refusals": sum(1 for r in live if r[2] == 0),
                "permissions": sum(1 for r in live if r[2] == 1),
                "named_outright": sum(1 for r in live if r[0] == sb),
                "newest_is_own": 1 if live and max(live, key=lambda r: r[5])[4] == nid else 0,
            }
            verdicts.append((dict(feats), bool(vd)))
            owns.append((dict(feats), bool(wog == nid)))
    return verdicts, owns


def move_rows(texts):
    """A record a node held before a structural change, and whether it survived it."""
    rows = []
    for text in texts:
        lines = text.strip().split("\n")
        marks = [i for i, ln in enumerate(lines) if ln.split()[0] in ("mv", "us")]
        for at in marks[:3]:
            before = replay("\n".join(lines[:at]) + "\n")
            after = replay("\n".join(lines[:at + 1]) + "\n")
            fb = {r[1]: (r[2], r[3], [tuple(x) for x in r[4]]) for r in before if r[0] == "fin"}
            fa = {r[1]: (r[2], r[3], [tuple(x) for x in r[4]]) for r in after if r[0] == "fin"}
            for nid in fb:
                if nid not in fa:
                    continue
                up_now = fa[nid][0]
                chain = []
                walk = nid
                seen = set()
                while walk in fa and walk not in seen:
                    seen.add(walk)
                    chain.append(walk)
                    walk = fa[walk][0]
                kept = set(fa[nid][2])
                for r in fb[nid][2]:
                    rows.append(({"sc": r[3],
                                  "barred": fa[nid][1],
                                  "origin_still_above": 1 if r[4] in chain else 0,
                                  "origin_is_me": 1 if r[4] == nid else 0},
                                 bool(r in kept)))
    return rows


def samples():
    texts = [gen.text("decide/%d" % i) for i in range(14)]
    verdicts, owns = ask_rows(texts)
    return {
        "crosses-the-edge": edge_rows(texts),
        "survives-a-move": move_rows(texts),
        "verdict": verdicts,
        "winner-is-own": owns,
    }
