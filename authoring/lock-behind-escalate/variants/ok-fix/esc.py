from lm import grant


def try_table(mgr, txn, table):
    modes = mgr.held.row_modes(txn, table)
    if len(modes) < mgr.cfg.k:
        return
    want = "x" if "x" in modes else "s"
    if mgr.held.covers(txn, table, want):
        return
    if grant.admissible(mgr.held, mgr.wait, txn, table, want, grant.NEWEST):
        mgr.record(txn, table, want)
        mgr.out.line("esc %s %s %s" % (txn, table, want))
