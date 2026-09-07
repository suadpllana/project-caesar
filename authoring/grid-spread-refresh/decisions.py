"""The reference's graded decisions, as rows of integers an agent could read cold.

tools/onelinecheck.py searches these for a rule of at most two comparisons that reproduces
the label. If one exists for every graded quantity, the answer to this task is something a
solver writes before running anything, whatever the brief says around it.

Three quantities are sampled, and the features are restricted to what is actually on the
page when the decision has to be made: the addresses a formula names, where it sits, what
the edit touched, and what the cells around it look like. Nothing derived from the settled
sheet is offered as a feature, because the settled sheet is the thing being decided.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tasks", "grid-spread-refresh", "tests"))

import gen  # noqa: E402
import oracle  # noqa: E402

CAP = 700


def about(m, cell, edit):
    e = m.ow[cell]
    refs = e[3]
    below = [t for t in refs if t[1] == cell[1] and t[0] > cell[0]]
    above = 0
    for r in range(1, cell[0]):
        other = m.ow.get((r, cell[1]))
        if other is not None and other[0] == "f" and other[1] == "v":
            above += 1
    owned = 0
    for r in range(cell[0] + 1, min(m.nr, cell[0] + 8) + 1):
        owned += 1 if (r, cell[1]) in m.ow else 0
    return {
        "named": len(refs),
        "names_edit": 1 if edit in refs else 0,
        "is_block": 1 if e[1] == "v" else 0,
        "row": cell[0],
        "col": cell[1],
        "edit_row": edit[0],
        "edit_col": edit[1],
        "same_col": 1 if cell[1] == edit[1] else 0,
        "blocks_above": above,
        "names_below": len(below),
        "owned_below": owned,
        "rows_below": m.nr - cell[0],
        "showing": 0 if m.dv.get(cell) is None else 1,
    }


def samples():
    out = {"recomputed": [], "display_moved": [], "block_fits": []}
    for _, text in gen.batch("decide-v1", 3):
        m = None
        live = False
        for raw in text.split("\n"):
            s = raw.strip()
            if not s:
                continue
            t = s.split(None, 2)
            if t[0] == "size":
                m = oracle.Model(int(t[1]))
                continue
            if t[0] == "go":
                live = True
                continue
            edit = oracle.pa(t[1])
            before = {}
            if live:
                for cell, e in m.ow.items():
                    if e[0] == "f":
                        before[cell] = (about(m, cell, edit), m.dv.get(cell))
            m.apply(s)
            if not live:
                continue
            for cell, (feats, was) in before.items():
                if len(out["recomputed"]) < CAP:
                    out["recomputed"].append((feats, cell in m.hit))
                if len(out["display_moved"]) < CAP:
                    out["display_moved"].append((dict(feats), m.dv.get(cell) != was))
                if feats["is_block"] and len(out["block_fits"]) < CAP:
                    out["block_fits"].append((dict(feats), m.dv.get(cell) != oracle.BLK))
    return out
