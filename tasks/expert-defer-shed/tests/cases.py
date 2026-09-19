"""The enumerated programs: one per graded decision, and both sides of every fence.

Each entry is a configuration and the microbatches of one or two steps, written small enough
that the whole trace can be read by hand. The name of a case is the name of the rule it pins,
so a failure says which rule broke rather than "a generated program was wrong".

  rank-tie                 equal scores rank by the smaller expert index
  want-one                 an expert over the threshold on its own is the whole want list
  want-short-of            a ranking that never reaches the threshold is wanted entire
  cap-first-mb             buffers are sized from the first microbatch, not from the step
  cap-round-up            a capacity that does not divide is rounded up, never down
  bank-round-up            the bank budget is rounded up too
  place-ordinary           slack everywhere: nothing displaces, nothing defers, nothing sheds
  place-lowest-free        a slot freed in the middle is filled before the next unused one
  place-prefix-stop        a blocked rank ends the token; later ranks are not placed
  disp-take-slot           the arrival takes the weakest occupant's slot, not a free one
  disp-equal-holds         an occupant scoring exactly the arrival's stays
  disp-below-holds         an occupant scoring above the arrival stays
  disp-once-only           a token already displaced this step is never the victim again
  disp-tie-slot            equal occupants: the larger slot index goes
  cont-later-ranks         a rank-zero loss takes the token's later placements with it
  cont-mid-rank            a later-rank loss keeps the earlier ranks and queues nothing
  defer-ahead              a queued token is placed before the next microbatch's own tokens
  defer-keeps-prefix       a token that keeps rank zero is not queued, whatever it lost after
  defer-twice              a token can lose rank zero in two microbatches of one step
  defer-order              two losses in one microbatch keep the order they happened in
  defer-last-mb            a rank-zero loss in the last microbatch is held and prints nothing
  strike-widens            the struck-out expert lengthens the want list on the way back
  strike-refusal           an expert that refused without displacing is struck out as well
  shed-weakest             the bank sheds its lowest-scoring placement first
  shed-cascade             a shed placement takes the token's later ranks in other banks
  shed-recheck             an earlier bank's shed can leave a later bank nothing to do
  shed-tie                 equal placements: the larger expert index goes
  res-want-only            the residual counts wanted experts, not the whole ranking
  bal-final-wants          the balance number counts wants as they finally stand
  step-apart               a second step starts with empty buffers, queue and strike-outs
"""

CASES = {
    # --- ranking and the want list ------------------------------------------------
    "rank-tie": ((4, 2, 600, 200, 100), [[[(300, 300, 300, 10)]]]),
    "want-one": ((4, 2, 600, 200, 100), [[[(900, 10, 10, 10), (10, 900, 10, 10)]]]),
    "want-short-of": ((4, 2, 600, 100, 100), [[[(100, 50, 30, 20), (90, 60, 40, 10)]]]),

    # --- capacity and the bank budget ---------------------------------------------
    "cap-first-mb": ((4, 2, 600, 100, 100), [[
        [(900, 10, 10, 10), (10, 900, 10, 10)],
        [(300, 250, 200, 100), (290, 260, 210, 90), (280, 270, 220, 80),
         (310, 240, 190, 110), (320, 230, 180, 120), (330, 220, 170, 130)],
    ]]),
    "cap-round-up": ((4, 2, 600, 100, 100), [[
        [(900, 10, 10, 10), (10, 900, 10, 10), (10, 10, 900, 10)],
    ]]),
    "bank-round-up": ((4, 2, 600, 100, 70), [[
        [(300, 250, 200, 10), (310, 240, 190, 10), (320, 230, 180, 10),
         (330, 220, 170, 10)],
    ]]),

    # --- placement ------------------------------------------------------------------
    "place-ordinary": ((6, 3, 600, 200, 100), [[
        [(900, 0, 0, 0, 0, 0), (0, 900, 0, 0, 0, 0), (0, 0, 900, 0, 0, 0)],
        [(0, 0, 0, 900, 0, 0), (0, 0, 0, 0, 900, 0), (0, 0, 0, 0, 0, 900)],
    ]]),
    "place-lowest-free": ((4, 2, 600, 100, 100), [[
        [(300, 300, 10, 10), (310, 290, 10, 10), (320, 280, 10, 10)],
    ]]),
    "place-prefix-stop": ((6, 3, 600, 200, 100), [[
        [(800, 0, 0, 0, 0, 0), (790, 0, 0, 0, 0, 0), (250, 200, 300, 5, 5, 5)],
    ]]),

    # --- displacement ---------------------------------------------------------------
    "disp-take-slot": ((4, 2, 600, 100, 100), [[
        [(700, 0, 0, 0), (650, 0, 0, 0), (800, 0, 0, 0)],
    ]]),
    "disp-equal-holds": ((4, 2, 600, 200, 100), [[
        [(700, 0, 0, 0), (700, 0, 0, 0)],
    ]]),
    "disp-below-holds": ((4, 2, 600, 200, 100), [[
        [(900, 0, 0, 0), (700, 100, 50, 25)],
    ]]),
    "disp-once-only": ((4, 2, 600, 40, 100), [[
        [(500, 400, 10, 10), (900, 0, 0, 0)],
        [(0, 450, 0, 0)],
        [(0, 0, 0, 900)],
    ]]),
    "disp-tie-slot": ((4, 2, 600, 200, 100), [[
        [(700, 0, 0, 0), (700, 0, 0, 0), (800, 0, 0, 0)],
    ]]),

    # --- what a loss takes with it ---------------------------------------------------
    "cont-later-ranks": ((4, 2, 600, 100, 100), [[
        [(250, 240, 230, 10), (900, 0, 0, 0)],
    ]]),
    "cont-mid-rank": ((6, 3, 600, 75, 100), [[
        [(300, 250, 200, 0, 0, 0), (0, 900, 0, 0, 0, 0)],
        [(0, 0, 0, 900, 0, 0)],
    ]]),

    # --- the queue --------------------------------------------------------------------
    "defer-ahead": ((4, 2, 600, 50, 100), [[
        [(700, 300, 0, 0), (900, 0, 0, 0)],
        [(0, 300, 0, 0)],
    ]]),
    "defer-keeps-prefix": ((6, 3, 600, 120, 100), [[
        [(800, 0, 0, 0, 0, 0), (790, 0, 0, 0, 0, 0), (250, 200, 300, 5, 5, 5)],
        [(0, 0, 0, 900, 0, 0)],
    ]]),
    "defer-order": ((6, 3, 600, 50, 100), [[
        [(700, 0, 300, 0, 0, 0), (0, 700, 300, 0, 0, 0),
         (900, 0, 0, 0, 0, 0), (0, 900, 0, 0, 0, 0)],
        [(0, 0, 0, 0, 0, 900)],
    ]]),
    "defer-last-mb": ((4, 2, 600, 100, 100), [[
        [(700, 0, 0, 0)],
        [(900, 0, 0, 0)],
    ]]),
    "defer-twice": ((6, 3, 600, 100, 100), [[
        [(700, 300, 0, 0, 0, 0)],
        [(900, 0, 0, 0, 0, 0), (0, 800, 0, 0, 0, 0)],
        [(0, 0, 0, 0, 900, 0)],
        [(0, 0, 0, 0, 0, 900)],
    ]]),

    # --- striking out -------------------------------------------------------------------
    "strike-widens": ((4, 2, 600, 50, 100), [[
        [(590, 10, 10, 10), (900, 0, 0, 0)],
        [(0, 0, 0, 900)],
    ]]),
    "strike-refusal": ((4, 2, 600, 50, 100), [[
        [(900, 0, 0, 0), (590, 10, 10, 10)],
        [(0, 0, 0, 0)],
    ]]),

    # --- the shed --------------------------------------------------------------------
    "shed-weakest": ((4, 2, 600, 100, 50), [[
        [(300, 250, 200, 10), (10, 10, 700, 10)],
    ]]),
    "shed-cascade": ((4, 2, 600, 100, 50), [[
        [(300, 250, 200, 10)],
    ]]),
    "shed-recheck": ((4, 2, 600, 100, 50), [[
        [(300, 250, 200, 10), (10, 10, 10, 700)],
    ]]),
    "shed-tie": ((4, 2, 600, 100, 50), [[
        [(300, 300, 10, 10)],
    ]]),

    # --- what the step reports ---------------------------------------------------------
    "res-want-only": ((4, 2, 600, 100, 100), [[
        [(900, 0, 0, 0), (700, 100, 50, 25)],
    ]]),
    "bal-final-wants": ((4, 2, 600, 50, 100), [[
        [(590, 10, 10, 10), (900, 0, 0, 0)],
        [(300, 300, 300, 300)],
    ]]),

    # --- steps do not lean on each other -------------------------------------------------
    "step-apart": ((4, 2, 600, 50, 100),
                   [[[(700, 300, 0, 0), (900, 0, 0, 0)], [(0, 300, 0, 0)]],
                    [[(700, 300, 0, 0), (900, 0, 0, 0)], [(0, 300, 0, 0)]]]),
}

ORDER = sorted(CASES)


def prog(name):
    """One enumerated program, as the lines of a step file."""
    cfg, steps = CASES[name]
    lines = ["cfg %d %d %d %d %d" % cfg]
    for mbs in steps:
        lines.append("step")
        for mb in mbs:
            lines.append("mb")
            for sc in mb:
                lines.append("t " + " ".join(str(x) for x in sc))
    return lines
