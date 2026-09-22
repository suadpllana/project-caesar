from lm import grant


def after_row(mgr, txn, table):
    rows = mgr.held.rows(txn, table)
    if len(rows) < mgr.cfg.k:
        return
    mode = "x" if any(m == "x" for _t, m in rows) else "s"
    have = mgr.held.mode(txn, table)
    if have is not None and (have == "x" or mode == "s"):
        return
    if grant.grantable(mgr.held, mgr.wait, txn, table, mode, grant.LATEST):
        mgr.take(txn, table, mode)
        mgr.out.line("esc %s %s %s" % (txn, table, mode))
