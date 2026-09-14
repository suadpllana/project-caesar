"""How wide a step is, and whether the epoch can still fill one.

The width is arithmetic on the rank count in force. Whether the epoch is out is the part worth
getting right: what remains is counted in samples the epoch has not fed, never in positions it
has walked past. Those two are the same number until the run comes back on a different rank
count, and from then on a walk under the new order goes over ground the old one already covered,
so the positions walked run ahead of the samples handed out.

Counting what is left as `rows - fed` is sound because every sample still unfed lies ahead of
the current order's head - a walk leaves nothing unfed behind it. So the remainder is always
reachable, and the epoch ends exactly when fewer than one whole window of it is left.
"""


def width(run, st):
    """Positions one optimizer step takes: every rank's micro-batch, once per accumulation."""
    return st.rank * run.micro * run.accum


def room(run, st):
    """Can the epoch still fill a whole window out of what it has not fed?"""
    return run.rows - st.fed >= width(run, st)


def roll(st):
    """Leave the epoch. The ledger goes with it: the next epoch's orders are all fresh."""
    st.epoch += 1
    st.seen = {}
    st.fed = 0
