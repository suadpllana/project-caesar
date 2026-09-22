from lm import grant


def attempt(mgr, txn, table):
    modes = mgr.held.row_modes(txn, table)
    if len(modes) < mgr.cfg.k:
        return
    mode = "x" if "x" in modes else "s"
    if mgr.held.covered(txn, table, mode):
        return
    if grant.admissible(mgr.held, mgr.wait, txn, table, mode, grant.NEWEST):
        mgr.absorb(txn, table, mode)
        mgr.out.line("esc %s %s %s" % (txn, table, mode))
