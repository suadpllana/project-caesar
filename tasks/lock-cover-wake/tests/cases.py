"""The enumerated scripts: one per graded decision, and both sides of every fence.

Each one is short enough that the whole trace can be read by hand, and the name of a case is
the name of the rule it pins, so a failure says which rule broke rather than "a generated
script was wrong". Transaction numbers are deliberately not in begin order.

  plain           slack everywhere: nothing is covered, queued, felled or raised
  cov-own         a request for a mode the transaction already holds takes nothing
  cov-table       a row under a table lock strong enough for it takes nothing
  cov-six         SIX covers a row S; it does not cover a row X
  cov-not         IX covers neither a row S nor a row X
  int-first       a row request takes the intention on its table first
  int-wait        an intention request that queues carries its row request with it
  int-drop        a felled transaction loses the row request it was carrying
  conv-cover      a conversion goes to the cover of the two modes, not to the requested one
  conv-self       a conversion is tested against the other holders only
  conv-jump       a conversion passes queued new requests
  conv-behind     a conversion waits behind a queued conversion
  new-behind      a compatible new request waits behind a queued request
  fell-young      an older requester fells a younger holder
  fell-older      a younger requester queues instead
  fell-order      several conflicting holders are felled in begin order
  fell-shield     a holder with an older waiter on another entry it holds is not felled
  fell-queued     a request blocked only by the queue fells all the same
  fell-skip       the entry being asked for does not shield its own holder
  age-beg         age is begin order, not the transaction number
  wake-oldest     one commit frees two entries; the earlier-begun head goes first
  wake-cont       a granted head's row request joins the queue behind a waiting one
  wake-nofell     a waiting head that reaches the front fells nobody
  sub-covered     a table grant releases the rows that mode covers, and only those
  sub-none        a grant to IX releases no rows at all
  sub-tally       rows released by subsumption leave the threshold tally behind them
  esc-fires       the threshold raises the table lock and the rows go
  esc-mode        one row in X makes the raise go to X rather than S
  esc-drop        a raise the table is held against is abandoned and prints nothing
  esc-again       the next row grant at the threshold tries the raise again
  esc-nofell      a raise fells nobody, however old the transaction raising is
  esc-nocount     covered requests never count toward the threshold
  pass-wait       a command for a waiting transaction is passed over
  pass-cut        a command for a felled transaction is passed over
  pass-done       a command for a committed transaction is passed over
  rep-order       locks are reported in acquisition order, a retaken one at the end
  rep-res         queues are reported in resource order, a table before its own rows
  rep-state       the four state words
  plan-tiny       the sample script the brief quotes a line of, graded as it ships
  plan-pair       the second sample script, graded as it ships
"""

CASES = {
    # --- the ordinary side: a workload that needs none of the machinery ---------------
    "plain": """
        cfg 9
        beg 7
        beg 3
        beg 5
        req 7 1 IS
        req 3 1 IX
        req 5 1 IS
        req 7 1.0 S
        req 3 1.1 X
        req 5 1.2 S
        req 3 1.2 S
        com 7
    """,

    # --- covering ---------------------------------------------------------------------
    "cov-own": """
        cfg 9
        beg 4
        req 4 2 X
        req 4 2 S
        req 4 2 IS
        req 4 2 X
    """,
    "cov-table": """
        cfg 9
        beg 6
        req 6 3 S
        req 6 3.1 S
        req 6 3.2 S
        req 6 3.1 X
    """,
    "cov-six": """
        cfg 9
        beg 8
        req 8 5 S
        req 8 5.3 X
        req 8 5.4 S
        req 8 5.3 X
    """,
    "cov-not": """
        cfg 9
        beg 2
        req 2 4.0 X
        req 2 4.1 S
        req 2 4.0 S
    """,

    # --- the intention, and what a blocked intention carries ---------------------------
    "int-first": """
        cfg 9
        beg 1
        req 1 6.2 S
    """,
    "int-wait": """
        cfg 9
        beg 9
        beg 4
        req 9 7 S
        req 4 7.1 X
        com 9
    """,
    "int-drop": """
        cfg 9
        beg 8
        beg 5
        beg 2
        req 8 8 S
        req 2 9.0 X
        req 2 8.1 X
        req 5 9.0 S
        com 8
    """,

    # --- conversions and the two queue classes -----------------------------------------
    "conv-cover": """
        cfg 9
        beg 3
        req 3 1 IX
        req 3 1 S
    """,
    "conv-self": """
        cfg 9
        beg 7
        req 7 2 S
        req 7 2 X
    """,
    "conv-jump": """
        cfg 9
        beg 1
        beg 6
        beg 4
        req 1 3 IS
        req 6 3 IS
        req 4 3 X
        req 1 3 S
    """,
    "conv-behind": """
        cfg 9
        beg 9
        beg 6
        beg 3
        req 9 4 IS
        req 6 4 IS
        req 3 4 IS
        req 3 4 X
        req 6 4 IX
    """,
    "new-behind": """
        cfg 9
        beg 8
        beg 5
        beg 2
        req 8 5 IX
        req 5 5 S
        req 2 5 IS
    """,

    # --- felling ------------------------------------------------------------------------
    "fell-young": """
        cfg 9
        beg 4
        beg 7
        req 7 6.0 X
        req 4 6.0 S
    """,
    "fell-older": """
        cfg 9
        beg 7
        beg 4
        req 7 6.0 X
        req 4 6.0 S
    """,
    "fell-order": """
        cfg 9
        beg 1
        beg 9
        beg 5
        beg 3
        req 5 7 IS
        req 3 7 IS
        req 9 7 IS
        req 1 7 X
    """,
    "fell-shield": """
        cfg 9
        beg 1
        beg 2
        beg 4
        beg 5
        req 2 1 IS
        req 4 1.5 X
        req 5 1 X
        req 1 1 IX
        req 2 1.5 S
    """,
    "fell-queued": """
        cfg 9
        beg 5
        beg 2
        beg 9
        req 2 8 IX
        req 9 8 S
        req 5 8 S
    """,
    "fell-skip": """
        cfg 9
        beg 1
        beg 6
        beg 4
        beg 8
        req 4 1 IX
        req 8 1 X
        req 1 1 IS
        req 6 1 S
    """,
    "age-beg": """
        cfg 9
        beg 9
        beg 1
        req 1 2.0 X
        req 9 2.0 S
    """,

    # --- the wake pass --------------------------------------------------------------------
    "wake-oldest": """
        cfg 9
        beg 4
        beg 1
        beg 6
        req 4 2 X
        req 4 7 X
        req 1 7 S
        req 6 2 S
        com 4
    """,
    "wake-cont": """
        cfg 9
        beg 4
        beg 1
        beg 2
        req 4 9 S
        req 4 9.9 X
        req 2 9.9 S
        req 1 9.9 X
        com 4
    """,
    "wake-nofell": """
        cfg 9
        beg 9
        beg 3
        beg 7
        req 9 2 S
        req 7 2 IS
        req 3 2 IX
        req 7 2 S
        com 9
    """,

    # --- subsumption ------------------------------------------------------------------------
    "sub-covered": """
        cfg 9
        beg 1
        req 1 7.1 S
        req 1 7.2 X
        req 1 7.3 S
        req 1 7 S
    """,
    "sub-none": """
        cfg 9
        beg 3
        req 3 2.0 S
        req 3 2.1 X
    """,
    "sub-tally": """
        cfg 3
        beg 4
        req 4 2.0 S
        req 4 2.1 S
        req 4 2.2 S
        req 4 2.3 X
        req 4 2.4 X
    """,

    # --- the raise -----------------------------------------------------------------------------
    "esc-fires": """
        cfg 3
        beg 5
        req 5 3.0 S
        req 5 3.1 S
        req 5 3.2 S
    """,
    "esc-mode": """
        cfg 3
        beg 5
        req 5 3.0 S
        req 5 3.1 X
        req 5 3.2 S
    """,
    "esc-drop": """
        cfg 3
        beg 8
        beg 2
        req 8 3.9 X
        req 2 3.0 S
        req 2 3.1 S
        req 2 3.2 S
    """,
    "esc-again": """
        cfg 3
        beg 8
        beg 2
        req 8 3.9 X
        req 2 3.0 S
        req 2 3.1 S
        req 2 3.2 S
        com 8
        req 2 3.3 S
    """,
    "esc-nofell": """
        cfg 3
        beg 2
        beg 8
        req 2 3.0 S
        req 2 3.1 S
        req 8 3.9 X
        req 2 3.2 S
    """,
    "esc-nocount": """
        cfg 4
        beg 7
        req 7 8 S
        req 7 8.0 X
        req 7 8.1 S
        req 7 8.2 S
        req 7 8.3 X
    """,

    # --- commands that are passed over ------------------------------------------------------------
    "pass-wait": """
        cfg 9
        beg 1
        beg 6
        req 1 3 S
        req 6 3.1 X
        req 6 3.2 X
        req 6 4 X
        com 6
    """,
    "pass-cut": """
        cfg 9
        beg 4
        beg 7
        req 7 6.0 X
        req 4 6.0 S
        req 7 6.1 X
        com 7
    """,
    "pass-done": """
        cfg 9
        beg 3
        req 3 5.0 S
        com 3
        req 3 5.1 X
        com 3
    """,

    # --- the report ---------------------------------------------------------------------------------
    "rep-order": """
        cfg 9
        beg 5
        req 5 1.0 S
        req 5 1.1 S
        req 5 2.0 S
        req 5 1 S
        req 5 1.0 X
    """,
    "rep-res": """
        cfg 9
        beg 7
        beg 2
        beg 5
        beg 3
        req 7 10 X
        req 7 2.5 X
        req 2 10 S
        req 5 2.5 S
        req 3 2 S
    """,
    "rep-state": """
        cfg 9
        beg 6
        beg 1
        beg 8
        beg 4
        req 8 4.0 X
        req 1 4.0 S
        req 6 4 S
        req 4 4 X
        com 6
    """,
    # --- the two sample scripts the brief points at, graded as they ship ------------------
    "plan-tiny": """
        cfg 3
        beg 15
        beg 41
        beg 24
        req 24 0.0 X
        req 15 0.0 X
        req 24 0 SIX
        req 24 0 IS
        req 24 0.2 X
        req 41 0 X
        com 24
        req 15 0.3 X
        req 15 0.3 X
    """,
    "plan-pair": """
        cfg 4
        beg 6
        beg 1
        beg 9
        beg 3
        req 6 2 IX
        req 6 2.0 X
        req 1 2 IS
        req 1 2.1 S
        req 9 2 S
        req 3 2.0 S
        req 1 2.2 S
        req 1 2.3 S
        req 1 2.4 S
        com 6
        req 3 5.0 X
        req 9 5.0 S
    """,
}

ORDER = tuple(sorted(CASES))


def prog(name):
    return [line.strip() for line in CASES[name].strip().splitlines()]
