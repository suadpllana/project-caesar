"""The ledger, and the weight the service is holding.

Membership is derived, not logged.  `owed_here` is the rule itself: a row is owed to a
scroll when it carries that scroll's tag, its place is at or before the scroll's mark,
and the scroll has not been handed it.  Everything that can change one of those three
inputs - an edit, a hand-out, a step-over - asks this question again rather than editing
a record of what happened.

Order is the one thing membership does not decide, so the ledger keeps it: a dict from
row id to weight, in insertion order, which gives the front in O(1), removal from the
middle in O(1), and the order rows came to be owed for free.  A row that stops being owed
leaves; if it comes to be owed again it is inserted afresh and lands at the end.

`held` is a running total rather than a sum over the ledgers.  Owed weight changes only
where an entry enters or leaves one, and the step-over test reads it once per scan step,
so carrying it is the difference between a constant and a sweep over every scroll.
"""


def held(st):
    return st.owed


def owed_here(st, sc, i):
    r = st.rows.get(i)
    if r is None:
        return False
    if r[1] != sc.g:
        return False
    if i in sc.got:
        return False
    return sc.mk is not None and (r[0], i) <= sc.mk


def owe(st, sc, i):
    if i in sc.led:
        return
    w = st.rows[i][2]
    sc.led[i] = w
    st.owed += w


def unowe(st, sc, i):
    w = sc.led.pop(i, None)
    if w is not None:
        st.owed -= w


def settle(st, sc, i):
    if owed_here(st, sc, i):
        owe(st, sc, i)
    else:
        unowe(st, sc, i)


def front(sc):
    for i in sc.led:
        return i
    return None


def standing(sc):
    return len(sc.led)


def weight(sc):
    return sum(sc.led.values())
