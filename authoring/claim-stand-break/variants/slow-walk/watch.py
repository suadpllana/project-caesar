"""Who stops standing, and when.

Three things can end a claim and all three are handled here: the claim being made at a base the
rows have already moved past, another transaction's commit, and this transaction's own rollback
uncovering a key a read was answered over. A transaction is dead from the first of them and
stays dead, so a value another transaction changes and a third changes back has already ended
the reader even though nothing at the end of the program shows it.

The index reported is the lowest of the claims that stopped standing at that moment, not the
lowest that is standing now and not the one noticed first, so every claim a moving key touches
is tested before anything is reported.

The keys that moved drive the work. Point reads are indexed by key and the standing changes
with them, so a commit of one key costs one lookup however many claims the transaction holds;
scans are few and are tested by whether their cover holds the key.
"""
from tx import cover, say


def kill(txn, i, out):
    if txn.dead is None:
        txn.dead = i
        say.dead(out, txn.tid, i)


def fresh(st, txn, c, out):
    """A claim has just been made."""
    if txn.dead is None and not cover.stands(st, txn, c):
        kill(txn, c.i, out)


def shifted(st, txn, keys, out):
    """These keys have moved: a commit stamped them, or a rollback uncovered them."""
    if txn.dead is not None:
        return
    low = None
    for c in txn.claims:
        for key in keys:
            if (low is None or c.i < low) and cover.moved(st, txn, c, key):
                low = c.i
    if low is not None:
        kill(txn, low, out)
