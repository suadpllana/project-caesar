from lm import spec


def compat(a, b):
    return a == "s" and b == "s"


def overlap(a, b):
    return a == b or spec.table_of(a) == b or spec.table_of(b) == a


def clash(tgt, mode, tgt2, mode2):
    return overlap(tgt, tgt2) and not compat(mode, mode2)


def grantable(held, txn, tgt, mode):
    for _u, t2, m2 in held.holders(txn):
        if clash(tgt, mode, t2, m2):
            return False
    return True
