from lm import grant


def after_row(mgr, txn, table):
    n = mgr.tally.get((txn, table), 0) + 1
    mgr.tally[(txn, table)] = n
    if n < mgr.cfg.k or mgr.held.mode(txn, table) is not None:
        return
    mode = "x" if any(m == "x" for _t, m in mgr.held.rows(txn, table)) else "s"
    if grant.grantable(mgr.held, txn, table, mode):
        mgr.held.put(txn, table, mode)
        mgr.out.line("esc %s %s %s" % (txn, table, mode))
    else:
        mgr.park(txn, table, mode)
