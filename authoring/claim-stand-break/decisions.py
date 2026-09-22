"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones the shipped tree exposes at the moment the decision is made: the row limit a scan
asked for, how many rows it got, whether the key that moved is one of them, what it answered
then and what it answers now, and whether the transaction has a change of its own standing over
it. Nothing says how far the scan's cover reaches, because the shipped tree has no such field
and working that out is the task.

The verdict to want is that at least one graded quantity has no short rule. Whether a change
claim stops standing should be short - it is a stated rule with nothing behind it, and
`cheat-val-claim` and `cheat-no-stamp` cover the readings that get it wrong. Whether a scan
stops standing should not be: it needs the row limit, the rows returned and the values together.

The watched copy below is the reference itself, and every program it is run over is asserted to
reproduce the sealed model, so a copy that drifted could not quietly report on another engine.

    python3 tools/onelinecheck.py claim-stand-break
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

ROWS = {"span-stands": [], "read-stands": [], "change-stands": []}
CAP = 6


def _small(x):
    if x is None:
        return -1
    return max(-1, min(CAP, x))


def _watch(cover, hold, view):
    real = cover.moved

    def moved(st, txn, c, key):
        got = real(st, txn, c, key)
        if c.kind == hold.SPAN:
            then = c.seen.get(key)
            now = view.one(st, txn, key, c.i, st.ver)
            ROWS["span-stands"].append(({
                "n": _small(c.n),
                "got": _small(len(c.seen)),
                "insee": 1 if key in c.seen else 0,
                "then": _small(then),
                "now": _small(now),
                "same": 1 if then == now else 0,
                "under": 0 if view.under(txn, key, c.i) is hold.MISS else 1,
                "inrange": 1 if c.lo <= key <= c.hi else 0,
            }, bool(got)))
        elif c.kind == hold.GET:
            now = view.one(st, txn, key, c.i, st.ver)
            ROWS["read-stands"].append(({
                "mine": 1 if c.key == key else 0,
                "then": _small(c.val),
                "now": _small(now),
                "same": 1 if c.val == now else 0,
                "under": 0 if view.under(txn, key, c.i) is hold.MISS else 1,
            }, bool(got)))
        else:
            ROWS["change-stands"].append(({
                "mine": 1 if c.key == key else 0,
                "on": 1 if c.on else 0,
                "after": 1 if st.after(key, txn.base) else 0,
                "same": 1 if st.at(key, txn.base) == st.at(key, st.ver) else 0,
            }, bool(got)))
        return got

    cover.moved = moved


def samples():
    here = lab.tree(lab.ROOT / "tasks" / "claim-stand-break" / "solution")
    run_tx = lab.engine(here)
    from tx import cover, hold, view
    _watch(cover, hold, view)

    _cases, gen, model = lab.sealed()
    for fam, big in gen.FAMILIES:
        if big:
            continue
        for _name, name, lines in [w for w in gen.programs("decide", 12) if w[0] == fam]:
            got = run_tx.run("\n".join(lines) + "\n")
            assert got == model.expect(lines), \
                "the watched copy drifted from the contract on %s" % name
    return ROWS


if __name__ == "__main__":
    for name, rows in sorted(samples().items()):
        kinds = len({str(y) for _r, y in rows})
        print("%-14s %d rows, %d outcomes" % (name, len(rows), kinds))
