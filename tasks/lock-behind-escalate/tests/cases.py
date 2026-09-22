"""The enumerated scripts: one per graded decision, and both sides of every fence.

Each entry is a threshold and the ops of two to five transactions, written small enough that
the whole trace can be read by hand. The name of a case is the name of the rule it pins, so a
failure says which rule broke rather than "a generated script was wrong".

  conf-mode            shared with shared is compatible; anything with exclusive is not
  conf-overlap         a table lock overlaps every row of its table, both ways round
  plain-pass           a request on a row nobody has queued for is granted at once
  behind-writer        a reader waits behind a queued writer on its row, holder or not
  behind-conflict      a reader is not behind a queued reader it does not conflict with
  cross-behind         a queued table request holds back a later row request on that table
  skip-upgrade         a holder upgrading passes a queued writer that waits on its own lock
  skip-two             two queued writers that both wait on the requester are both passed
  skip-late            a queued request is granted when its blocker later comes to wait on it
  skip-chain           dependence runs through a holder that is itself waiting
  skip-soft-path       dependence runs through a waiter queued behind another waiter
  soft-not-dead        a cycle that closes only through a queued request is no deadlock
  settle-earliest      of two requests freed by one commit the earlier is granted first
  settle-order         a writer between two readers keeps the second reader behind it
  cover-same           a target already held in that mode or stronger records nothing
  cover-table          rows under a table record are granted without a record
  upgrade-place        shared to exclusive on one target is one record, raised in place
  subsume-s            a shared table grant releases shared rows and keeps exclusive ones
  subsume-x            an exclusive table grant releases every row record on the table
  esc-trigger          K row records on one table escalate to a table lock
  esc-mode             one exclusive row among them makes the table lock exclusive
  esc-holder-blocks    another transaction's row record refuses the escalation
  esc-holder-shared    another transaction's shared row does not refuse a shared escalation
  esc-abandon          a refused escalation does not queue; the transaction keeps working
  esc-waiter-blocks    a queued writer that does not wait on the escalator refuses it
  esc-waiter-depends   a queued writer that waits on the escalator does not refuse it
  esc-retry            a refused escalation is tried again at the next row grant, not before
  esc-count-drop       a dropped row no longer counts toward the threshold
  esc-count-cover      a covered row grant adds no record and counts for nothing
  esc-under-shared     exclusive rows under a shared table record escalate to exclusive
  dead-fewest          the victim is the transaction on the cycle holding fewest records
  dead-tie-recent      equal records: the transaction that asked most recently dies
  dead-then-grant      once the victim is gone the survivor's request is granted
  drop-none            dropping a lock that is not held changes nothing
  drop-table           dropping a table record uncovers its rows for everyone
  order-first-line     transactions act in the order of their first line
  ordinary             no contention anywhere: every request is granted, nothing escalates
"""


def _s(k, *ops):
    return ["cfg %d" % k] + list(ops)


CASES = {
    # --- what conflicts with what -----------------------------------------------------
    "conf-mode": _s(50,
        "T1 lock t.1 s", "T1 commit",
        "T2 lock t.1 s", "T2 commit",
        "T3 lock t.1 x", "T3 commit"),
    "conf-overlap": _s(50,
        "T1 lock t x", "T1 lock u.1 s", "T1 commit",
        "T2 lock t.1 s", "T2 commit",
        "T3 lock u s", "T3 commit",
        "T4 lock u x", "T4 commit"),

    # --- behind an earlier waiter, or not --------------------------------------------
    "plain-pass": _s(50,
        "T1 lock t.1 x", "T1 lock t.3 s", "T1 commit",
        "T2 lock t.1 s", "T2 commit",
        "T3 lock t.2 s", "T3 lock t.3 s", "T3 commit"),
    "behind-writer": _s(50,
        "T1 lock t.1 s", "T1 lock t.2 s", "T1 commit",
        "T2 lock t.1 x", "T2 commit",
        "T3 lock t.1 s", "T3 commit"),
    "behind-conflict": _s(50,
        "T1 lock t.1 s", "T1 lock t.2 s", "T1 lock t.3 s", "T1 commit",
        "T2 lock t.1 x", "T2 commit",
        "T3 lock t s", "T3 commit",
        "T4 lock t.2 s", "T4 commit"),
    "cross-behind": _s(50,
        "T1 lock t.1 s", "T1 lock t.3 s", "T1 commit",
        "T2 lock t x", "T2 commit",
        "T3 lock t.2 s", "T3 commit"),

    # --- the exception: a waiter that waits on the requester --------------------------
    "skip-upgrade": _s(50,
        "T1 lock t.1 s", "T1 lock t.2 s", "T1 lock t.1 x", "T1 commit",
        "T2 lock t.1 x", "T2 commit"),
    "skip-two": _s(50,
        "T1 lock t.1 s", "T1 lock t.2 s", "T1 lock t.1 x", "T1 commit",
        "T2 lock t.1 x", "T2 commit",
        "T3 lock t.1 x", "T3 commit"),
    "skip-late": _s(50,
        "T1 lock t.1 s", "T1 lock t.3 s", "T1 lock t.2 s", "T1 commit",
        "T2 lock t.1 x", "T2 commit",
        "T3 lock t.2 x", "T3 lock t.1 s", "T3 commit"),
    "skip-soft-path": _s(50,
        "T1 lock t.1 s", "T1 lock t.2 s", "T1 lock t.1 x", "T1 commit",
        "T2 lock t.1 x", "T2 commit",
        "T3 lock t.1 s", "T3 commit"),
    "soft-not-dead": _s(50,
        "T3 lock t.1 s", "T3 lock t.3 s", "T3 lock t.4 s", "T3 commit",
        "T1 lock t.1 s", "T1 lock t.2 s", "T1 lock t.1 x", "T1 commit",
        "T2 lock t.1 x", "T2 commit"),
    "skip-chain": _s(50,
        "T1 lock t.1 s", "T1 lock t.4 s", "T1 lock t.2 s", "T1 commit",
        "T2 lock t.2 s", "T2 commit",
        "T3 lock t.1 x", "T3 commit",
        "T4 lock t.2 x", "T4 lock t.1 s", "T4 commit"),

    # --- settling after every op --------------------------------------------------------
    "settle-earliest": _s(50,
        "T1 lock t.1 x", "T1 lock t.2 x", "T1 lock u.1 s", "T1 commit",
        "T2 lock u.2 s", "T2 lock t.2 s", "T2 commit",
        "T3 lock u.3 s", "T3 lock t.1 s", "T3 commit"),
    "settle-order": _s(50,
        "T1 lock t.1 x", "T1 lock t.2 s", "T1 commit",
        "T2 lock t.1 s", "T2 commit",
        "T3 lock t.1 x", "T3 commit",
        "T4 lock t.1 s", "T4 commit"),

    # --- what a grant records ------------------------------------------------------------
    "cover-same": _s(50,
        "T1 lock t.1 x", "T1 lock t.1 s", "T1 lock t.1 x", "T1 commit",
        "T2 lock t.2 s", "T2 lock t.2 s", "T2 commit"),
    "cover-table": _s(50,
        "T1 lock t x", "T1 lock t.1 s", "T1 lock t.2 x", "T1 commit",
        "T2 lock u s", "T2 lock u.1 s", "T2 commit"),
    "upgrade-place": _s(50,
        "T1 lock t.1 s", "T1 lock t.2 s", "T1 lock t.1 x", "T1 commit",
        "T2 lock t.1 s", "T2 commit"),
    "subsume-s": _s(50,
        "T1 lock t.1 s", "T1 lock t.2 x", "T1 lock t s", "T1 commit",
        "T2 lock t.2 s", "T2 commit"),
    "subsume-x": _s(50,
        "T1 lock t.1 s", "T1 lock t.2 x", "T1 lock t x", "T1 commit",
        "T2 lock t.1 s", "T2 commit"),

    # --- escalation ---------------------------------------------------------------------
    "esc-trigger": _s(2,
        "T1 lock t.1 s", "T1 lock t.2 s", "T1 commit",
        "T2 lock u.3 x", "T2 commit"),
    "esc-mode": _s(2,
        "T1 lock t.1 s", "T1 lock t.2 x", "T1 commit",
        "T2 lock u.3 s", "T2 commit"),
    "esc-holder-blocks": _s(2,
        "T1 lock t.5 s", "T1 lock u.1 s", "T1 commit",
        "T2 lock t.1 x", "T2 lock t.2 x", "T2 commit"),
    "esc-holder-shared": _s(2,
        "T1 lock t.5 s", "T1 lock u.1 s", "T1 commit",
        "T2 lock t.1 s", "T2 lock t.2 s", "T2 commit"),
    "esc-abandon": _s(2,
        "T1 lock t.5 s", "T1 lock u.1 s", "T1 lock u.2 s", "T1 commit",
        "T2 lock t.1 x", "T2 lock t.2 x", "T2 lock t.3 x", "T2 commit"),
    "esc-waiter-blocks": _s(2,
        "T1 lock t.5 s", "T1 lock u.1 s", "T1 lock v.1 s", "T1 commit",
        "T2 lock t.5 x", "T2 commit",
        "T3 lock t.1 s", "T3 lock t.2 s", "T3 commit"),
    "esc-waiter-depends": _s(2,
        "T1 lock t.5 s", "T1 lock u.1 s", "T1 lock t.1 s", "T1 commit",
        "T2 lock t.5 x", "T2 commit"),
    "esc-retry": _s(2,
        "T1 lock t.5 x", "T1 lock u.9 s", "T1 commit",
        "T2 lock t.1 s", "T2 lock t.2 s", "T2 lock u.1 s", "T2 lock t.3 s", "T2 commit"),
    "esc-count-drop": _s(2,
        "T1 lock t.1 s", "T1 drop t.1", "T1 lock t.2 s", "T1 lock t.3 s", "T1 commit"),
    "esc-count-cover": _s(2,
        "T1 lock t x", "T1 lock t.1 s", "T1 lock t.2 s", "T1 lock t.3 x", "T1 commit"),
    "esc-under-shared": _s(2,
        "T1 lock t s", "T1 lock t.1 x", "T1 lock t.2 x", "T1 commit",
        "T2 lock t.3 s", "T2 commit"),

    # --- the victim ---------------------------------------------------------------------
    "dead-fewest": _s(50,
        "T1 lock t.1 x", "T1 lock t.3 s", "T1 drop t.3", "T1 lock t.2 s", "T1 commit",
        "T2 lock t.2 x", "T2 lock t.4 s", "T2 lock t.1 s", "T2 commit"),
    "dead-tie-recent": _s(50,
        "T1 lock t.1 x", "T1 lock t.3 s", "T1 drop t.3", "T1 lock t.2 s", "T1 commit",
        "T2 lock t.2 x", "T2 lock t.1 s", "T2 commit"),
    "dead-then-grant": _s(50,
        "T1 lock t.1 x", "T1 lock t.2 s", "T1 commit",
        "T2 lock t.2 x", "T2 lock t.1 s", "T2 commit",
        "T3 lock t.1 s", "T3 commit"),

    # --- drops ------------------------------------------------------------------------------
    "drop-none": _s(50,
        "T1 lock t.1 s", "T1 drop t.2", "T1 drop t", "T1 commit"),
    "drop-table": _s(50,
        "T1 lock t.1 x", "T1 lock t x", "T1 drop t.1", "T1 drop t", "T1 lock u.1 s", "T1 commit",
        "T2 lock t.1 s", "T2 commit",
        "T3 lock v.1 s", "T3 lock v.2 s", "T3 lock v.3 s", "T3 lock v.4 s", "T3 commit"),

    # --- the driver's order, and the everyday case -------------------------------------------
    "order-first-line": _s(50,
        "T2 lock t.1 x", "T2 commit",
        "T1 lock t.1 x", "T1 commit"),
    "ordinary": _s(50,
        "T1 lock t.1 s", "T1 lock t.2 x", "T1 lock u s", "T1 commit",
        "T2 lock t.1 s", "T2 lock t.3 x", "T2 commit",
        "T3 lock v.1 x", "T3 lock v.2 x", "T3 commit"),
}

ORDER = sorted(CASES)


def prog(name):
    """One enumerated script, as its lines."""
    return list(CASES[name])
