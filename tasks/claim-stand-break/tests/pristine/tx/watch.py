from tx import cover, hold, say


def kill(txn, i, out):
    if txn.dead is None:
        txn.dead = i
        say.dead(out, txn.tid, i)


def fresh(st, txn, c, out):
    if txn.dead is None and c.kind == hold.CHG and st.after(c.key, txn.base):
        kill(txn, c.i, out)


def shifted(st, txn, out):
    if txn.dead is not None:
        return
    for c in txn.claims:
        if not cover.stands(st, txn, c):
            kill(txn, c.i, out)
            return
