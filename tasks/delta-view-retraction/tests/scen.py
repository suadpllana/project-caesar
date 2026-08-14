"""The scenario set.

Each entry names the reading of the rule it is aimed at, and that text is quoted in the
verifier's failure messages so a failing run says which distinction it got wrong.

The set is fenced from both sides on purpose: for every case where a cell MUST be rebuilt
there is a case where rebuilding is wrong because the accumulator could have absorbed the
edit. A submission that plays safe and rebuilds on every retraction produces every value
correctly and fails on folds and scans.
"""

CAP = 3


def _ins(k, g, v, ts):
    return {"op": "ins", "src": "ord", "k": k, "g": g, "v": v, "ts": ts}


def _del(k, ts):
    return {"op": "del", "src": "ord", "k": k, "ts": ts}


def _upd(k, v, ts, g=None):
    r = {"op": "upd", "src": "ord", "k": k, "v": v, "ts": ts}
    if g is not None:
        r["g"] = g
    return r


SCENARIOS = [
    {
        "name": "insert-only",
        "aim": "No retraction anywhere. Every edit is absorbable for every kind, so a "
               "submission that rebuilds here is paying for nothing.",
        "ops": [_ins("a", "g1", 5, 1), _ins("b", "g1", 3, 2), _ins("c", "g1", 9, 2),
                _ins("d", "g1", 1, 3), _ins("e", "g1", 7, 4), _ins("f", "g1", 4, 5)],
    },
    {
        "name": "retract-inside-kept",
        "aim": "The group holds no more distinct values than the cap, so the accumulator "
               "is a complete witness and every retraction is absorbable. Rebuilding is "
               "the safe answer and it is wrong on work.",
        "ops": [_ins("a", "g1", 5, 1), _ins("b", "g1", 3, 2), _ins("c", "g1", 9, 3),
                _del("b", 4), _del("a", 5), _ins("d", "g1", 6, 6)],
    },
    {
        "name": "retract-drains-witness",
        "aim": "Five distinct values with cap three: two were dropped and never recorded. "
               "Retracting the kept ones leaves the accumulator claiming an answer the "
               "group does not have, so these must rebuild from the row store.",
        "ops": [_ins("a", "g1", 5, 1), _ins("b", "g1", 3, 1), _ins("c", "g1", 9, 2),
                _ins("d", "g1", 1, 2), _ins("e", "g1", 7, 3),
                _del("d", 4), _del("b", 4), _del("a", 5)],
    },
    {
        "name": "duplicates-inflate-n",
        "aim": "Many rows, few distinct values, nothing ever dropped. A rule that compares "
               "acc.n against len(acc.top) rebuilds every time and is wrong on work; the "
               "distinct live count is what decides.",
        "ops": [_ins("a", "g1", 4, 1), _ins("b", "g1", 4, 1), _ins("c", "g1", 4, 2),
                _ins("d", "g1", 6, 2), _ins("e", "g1", 6, 3), _ins("f", "g1", 4, 3),
                _del("a", 4), _del("d", 4), _del("b", 5)],
    },
    {
        "name": "retract-outside-kept",
        "aim": "Values were dropped, but the retraction targets a value the cell is not "
               "holding, so the answer cannot move and the edit is absorbable even though "
               "the witness is incomplete.",
        "ops": [_ins("a", "g1", 1, 1), _ins("b", "g1", 2, 1), _ins("c", "g1", 3, 2),
                _ins("d", "g1", 8, 2), _ins("e", "g1", 9, 3), _del("e", 4), _del("d", 5)],
    },
    {
        "name": "update-in-place",
        "aim": "An update is a retraction and an insert on one key in one group. Both "
               "halves have to reach the cell, and the retraction half follows the same "
               "rule as a delete.",
        "ops": [_ins("a", "g1", 5, 1), _ins("b", "g1", 3, 1), _ins("c", "g1", 9, 2),
                _ins("d", "g1", 2, 2), _ins("e", "g1", 7, 3),
                _upd("a", 11, 4), _upd("c", 1, 5)],
    },
    {
        "name": "update-moves-group",
        "aim": "The update carries a new group, so the two halves land on different cells: "
               "one loses a row and one gains it, and each side is judged separately.",
        "ops": [_ins("a", "g1", 5, 1), _ins("b", "g1", 3, 1), _ins("c", "g2", 9, 2),
                _ins("d", "g1", 1, 2), _ins("e", "g1", 7, 3),
                _upd("a", 5, 4, g="g2"), _upd("d", 1, 5, g="g2")],
    },
    {
        "name": "two-groups-independent",
        "aim": "Two groups interleaved. Work done for one must not be charged to the "
               "other, and a rebuild of one group must not rebuild the other.",
        "ops": [_ins("a", "g1", 5, 1), _ins("p", "g2", 6, 1), _ins("b", "g1", 3, 2),
                _ins("q", "g2", 2, 2), _ins("c", "g1", 9, 3), _ins("r", "g2", 8, 3),
                _ins("s", "g2", 4, 4), _ins("t", "g2", 7, 4),
                _del("q", 5), _del("s", 5), _del("b", 6)],
    },
    {
        "name": "delete-unknown-key",
        "aim": "A delete for a key that was never inserted, and a second delete of a key "
               "already retracted. Neither is an edit, so neither may touch a cell.",
        "ops": [_ins("a", "g1", 5, 1), _ins("b", "g1", 3, 2), _del("zz", 3),
                _del("a", 4), _del("a", 5), _ins("c", "g1", 7, 6)],
    },
    {
        "name": "empty-then-refill",
        "aim": "Every row in the group is retracted and the group then refills. The empty "
               "cell must read zero and the refill must not inherit anything.",
        "ops": [_ins("a", "g1", 5, 1), _ins("b", "g1", 3, 1), _ins("c", "g1", 9, 2),
                _ins("d", "g1", 4, 2), _del("a", 3), _del("b", 3), _del("c", 4),
                _del("d", 4), _ins("e", "g1", 2, 5), _ins("f", "g1", 8, 6)],
    },
    {
        "name": "late-arrival",
        "aim": "Deltas arriving behind the watermark. They still edit the view and are "
               "still counted as revisions; lateness changes nothing about the repair.",
        "ops": [_ins("a", "g1", 5, 1), _ins("b", "g1", 3, 4), _ins("c", "g1", 9, 6),
                _ins("d", "g1", 1, 2), _del("a", 3), _ins("e", "g1", 7, 8),
                _del("d", 2), _ins("f", "g1", 6, 9)],
    },
    {
        "name": "rebuild-narrows-deps",
        "aim": "A group wider than the cap is rebuilt, and afterwards the cell's "
               "dependency map names the rows that were folded rather than the rows the "
               "group holds. Anything that reads the accountable set off the cell now "
               "reads a cell that has lost values as complete, and absorbs a retraction "
               "that empties a candidate slot.",
        "ops": [_ins("k1", "g1", 1, 2), _ins("k0", "g1", 7, 5), _ins("k2", "g1", 10, 5),
                _ins("k3", "g1", 2, 5), _ins("k2", "g1", 11, 5), _upd("k1", 4, 5),
                _ins("k2", "g1", 1, 5), _del("k0", 5)],
    },
    {
        "name": "duplicates-at-the-cap",
        "aim": "The surviving values carry several rows each, and the aggregates rank "
               "them in opposite directions, so how much a reread has to fold is neither "
               "the size of the group nor the cap: it is the number of rows standing on "
               "the values that survive, and it differs between min and max on the same "
               "group at the same moment.",
        "ops": [_ins("a", "g1", 9, 1), _ins("b", "g1", 9, 1), _ins("c", "g1", 7, 2),
                _ins("d", "g1", 7, 2), _ins("e", "g1", 5, 3), _ins("f", "g1", 5, 3),
                _ins("g", "g1", 3, 4), _ins("h", "g1", 1, 4),
                _del("a", 5), _del("b", 5), _del("e", 6), _del("f", 6),
                _ins("i", "g1", 8, 7), _del("g", 7)],
    },
    {
        "name": "wide-group-churn",
        "aim": "A long run over a group far wider than the cap, mixing inserts, deletes "
               "and updates so the witness repeatedly completes and breaks. This is where "
               "an implementation that never rebuilds diverges on values.",
        "ops": [_ins("a", "g1", 12, 1), _ins("b", "g1", 5, 1), _ins("c", "g1", 19, 2),
                _ins("d", "g1", 3, 2), _ins("e", "g1", 8, 3), _ins("f", "g1", 15, 3),
                _ins("g", "g1", 1, 4), _del("d", 4), _del("g", 5), _upd("b", 20, 5),
                _del("a", 6), _ins("h", "g1", 2, 6), _del("c", 7), _upd("e", 4, 7),
                _ins("i", "g1", 11, 8), _del("f", 8)],
    },
]


def by_name(name):
    for s in SCENARIOS:
        if s["name"] == name:
            return s
    return None
