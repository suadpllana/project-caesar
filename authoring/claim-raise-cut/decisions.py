"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` looks for the shortest exact rule over these. The features offered are
the raw ones the tree exposes at that moment - what a transaction asked for, what the others
hold, how many of those marks exclude what was asked, where the request sits in the queue, how
many claims a transaction has and when it made its request. Nothing derived is offered, because
every derivation here is the task: the mark covering a stack, whether a raise is stuck, whether
an item is pinned, and whether one transaction leaving would let another through.

The verdict to want is that at least one graded quantity has no short rule, and the one that
should not is who a blocked request waits for: the conflict test is exactly one term, it is what
a frontier model writes cold, and it is wrong.

    python3 authoring/claim-raise-cut/decisions.py
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "claim-raise-cut"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import gen  # noqa: E402
import lab  # noqa: E402

MARKS = ("scan", "edit", "grow", "pin", "seal")


def samples():
    app = lab.tree(TASK / "solution", "decisions")
    out, txn = lab.load(app)
    sys.path.insert(0, str(app))
    import hold.cyc as cyc
    import hold.item as item
    import hold.mark as mark
    import hold.wait as wait

    grant_rows, cut_rows, wait_rows = [], [], []

    def about(it, r):
        """What the tree shows about one pending request, with nothing derived."""
        others = [(t, m) for t, m in it.eff.items() if t != r.tx]
        pend = it.pend
        pos = pend.index(r) if r in pend else -1
        return {
            "is_raise": int(r.tx in it.eff),
            "ask": MARKS.index(r.ask),
            "own_claims": len(it.stack.get(r.tx, ())),
            "holders": len(others),
            "excluded_by": sum(1 for _t, m in others if not mark.fits(r.ask, m)),
            "queue_pos": pos,
            "raisers_pending": sum(1 for x in pend if x.tx in it.eff),
            "fresh_ahead": sum(1 for x in pend[:max(pos, 0)] if x.tx not in it.eff),
        }

    real_pass = txn.Svc.pass_over
    real_pick = cyc.pick
    real_edges = wait.edges

    def watch_pass(self, k):
        before = list(k.pend)
        rows = [(r, about(k, r)) for r in before]
        real_pass(self, k)
        left = {id(r) for r in k.pend}
        for r, row in rows:
            grant_rows.append((row, int(id(r) not in left)))

    def watch_pick(txs):
        got = real_pick(txs)
        if len(txs) > 1:
            for t in txs:
                cut_rows.append(({
                    "items_held": t.nk,
                    "request_seq": t.req.seq,
                    "number": t.num,
                    "ring_size": len(txs),
                    "backlog": len(t.back),
                }, int(t is got)))
        return got

    def watch_edges(it):
        got = real_edges(it)
        for tx, who in got.items():
            r = next((x for x in it.pend if x.tx == tx), None)
            if r is None:
                continue
            base = about(it, r)
            for other, m in it.eff.items():
                if other == tx:
                    continue
                row = dict(base)
                row["other_holds"] = 1
                row["other_mark"] = MARKS.index(m)
                row["other_excludes_ask"] = int(not mark.fits(r.ask, m))
                row["other_asks"] = int(any(x.tx == other for x in it.pend))
                row["other_pos"] = next((i for i, x in enumerate(it.pend) if x.tx == other), -1)
                wait_rows.append((row, int(other in who)))
        return got

    txn.Svc.pass_over = watch_pass
    cyc.pick = watch_pick
    wait.edges = watch_edges
    try:
        for name, steps in gen.programs("decisions", 6, 0):
            svc = txn.Svc(out.Trace())
            for st in steps:
                svc.step(st)
    finally:
        txn.Svc.pass_over = real_pass
        cyc.pick = real_pick
        wait.edges = real_edges

    return {"grant_now": grant_rows, "cut_who": cut_rows, "waits_for": wait_rows}


if __name__ == "__main__":
    got = samples()
    for k, v in sorted(got.items()):
        print("%-12s %6d rows, %d distinct labels" % (k, len(v), len({y for _, y in v})))
