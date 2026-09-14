"""The enumerated programs: one per graded decision, and both sides of every fence.

Each is small enough to read by hand and is named for the decision it pins. The generated
population in `gen.py` covers combinations and resists fitting; these say which rule broke when
something breaks, which a count of failed random programs cannot.

Read alongside the frozen contract in `test_outputs.py`.
"""

PROGS = {

    # --- how a window is dealt out ------------------------------------------------------
    # deal-order: two ranks and two accumulations, so chunk j*rank+r and chunk r*accum+j
    #   name different positions for every rank but the first.
    "deal-order": """
        rows 32 seed 5 rank 2 micro 2 accum 2 ckpt 4 grow 9 scale 3 epochs 1
        run 1
    """,
    # deal-shard: sharding the whole epoch per rank and running a cursor down each shard is
    #   the memorized shape; it disagrees from the first window on once rows exceeds one.
    "deal-shard": """
        rows 48 seed 9 rank 3 micro 2 accum 2 ckpt 9 grow 9 scale 2 epochs 1
        run 3
    """,
    # deal-one: one rank and one accumulation, where every dealing agrees. The everyday side.
    "deal-one": """
        rows 12 seed 4 rank 1 micro 3 accum 1 ckpt 2 grow 9 scale 1 epochs 1
        run 4
    """,

    # --- where an epoch ends ------------------------------------------------------------
    # drop-window: 26 rows against a window of 8 leaves 2 rows, which is a whole micro-batch
    #   per rank. Dropping per micro-batch takes a short step here; dropping per window does
    #   not.
    "drop-window": """
        rows 26 seed 3 rank 2 micro 1 accum 4 ckpt 9 grow 9 scale 2 epochs 1
        run 6
    """,
    # drop-none: rows is exactly three windows, so nothing is dropped and the epoch ends on a
    #   boundary. The must-still-work side of the same rule.
    "drop-none": """
        rows 24 seed 11 rank 2 micro 2 accum 2 ckpt 9 grow 9 scale 2 epochs 2
        run 5
    """,

    # --- what a skipped step does -------------------------------------------------------
    # skip-consume: the first window holds a non-finite id, so the step is skipped and the
    #   next window must start after it rather than retry it.
    "skip-consume": """
        rows 24 seed 2 rank 1 micro 2 accum 2 ckpt 9 grow 9 scale 3 epochs 1
        nf 20
        run 4
    """,
    # skip-done: a skip before the cadence boundary. Counting skips as applied steps puts the
    #   checkpoint one step early, which the later kill then lands on.
    "skip-done": """
        rows 40 seed 6 rank 2 micro 1 accum 2 ckpt 2 grow 9 scale 3 epochs 1
        nf 16
        run 5
        kill
        run 2
    """,

    # --- the scale ----------------------------------------------------------------------
    # scale-floor: four skips in a row from an exponent of one. The scale stops at zero.
    "scale-floor": """
        rows 32 seed 8 rank 1 micro 2 accum 1 ckpt 9 grow 9 scale 1 epochs 1
        nf 5 nf 27 nf 13 nf 9
        run 16
    """,
    # scale-reset: a skip between applied steps. The run of successes restarts, so the scale
    #   grows later than a count of applied steps since the run began would grow it.
    "scale-reset": """
        rows 60 seed 12 rank 1 micro 2 accum 1 ckpt 9 grow 3 scale 0 epochs 1
        nf 59
        run 10
    """,
    # scale-grow: no skips at all, so both readings of the tracker agree. The other side.
    "scale-grow": """
        rows 40 seed 14 rank 1 micro 2 accum 2 ckpt 9 grow 2 scale 0 epochs 1
        run 6
    """,

    # --- the checkpoint -----------------------------------------------------------------
    # save-pos: a skip early on, then a kill. A checkpoint that stores the applied count and
    #   multiplies it back out by the window lands short of where the run actually was.
    "save-pos": """
        rows 48 seed 15 rank 2 micro 1 accum 2 ckpt 2 grow 9 scale 3 epochs 1
        nf 2
        run 6
        kill
        run 3
    """,
    # kill-none: a kill before any checkpoint exists. The run goes back to its very start, and
    #   the scale goes back to the exponent the run opened on rather than keeping the live one.
    "kill-none": """
        rows 32 seed 7 rank 2 micro 2 accum 1 ckpt 5 grow 2 scale 2 epochs 1
        run 3
        kill
        run 2
    """,
    # kill-same: a kill on an unchanged rank count. Coming back to the top of the epoch
    #   rather than to the saved position is the reading this separates.
    "kill-same": """
        rows 64 seed 10 rank 2 micro 2 accum 2 ckpt 2 grow 9 scale 3 epochs 1
        run 5
        kill
        run 3
    """,

    # --- coming back on a different rank count ------------------------------------------
    # back-now: a return in the middle of an epoch. The window width changes there and then,
    #   not at the next epoch boundary.
    "back-now": """
        rows 72 seed 13 rank 2 micro 1 accum 2 ckpt 3 grow 9 scale 2 epochs 1
        run 4
        back 3
        run 4
    """,
    # back-redraw: the same position read under two rank counts. The order is drawn for the
    #   rank count in force, so the ids after the return are not the ones before it.
    "back-redraw": """
        rows 48 seed 17 rank 2 micro 2 accum 1 ckpt 2 grow 9 scale 2 epochs 1
        run 4
        kill
        back 4
        run 3
    """,
    # back-hold: a return that names the rank count the run is already on. Nothing about the
    #   geometry moves, and the order does not either. The must-still-work side.
    "back-hold": """
        rows 48 seed 19 rank 2 micro 2 accum 1 ckpt 2 grow 9 scale 2 epochs 1
        run 4
        back 2
        run 3
    """,

    # --- epoch edges --------------------------------------------------------------------
    # roll-empty: eight rows left and a return on four ranks, whose window is twelve. The
    #   epoch is over with no step taken on the new geometry.
    "roll-empty": """
        rows 40 seed 21 rank 2 micro 1 accum 2 ckpt 9 grow 9 scale 2 epochs 3
        run 9
        back 4
        run 4
    """,
    # roll-budget: a budget of exactly one step across an epoch boundary. Rolling costs
    #   nothing out of it, so the step is taken in the next epoch.
    "roll-budget": """
        rows 18 seed 23 rank 1 micro 2 accum 3 ckpt 9 grow 9 scale 1 epochs 3
        run 3
        run 1
    """,
    # roll-tiny: a dataset smaller than one window. Every epoch ends without a step and the
    #   run reaches the end of its epochs having applied nothing.
    "roll-tiny": """
        rows 5 seed 25 rank 2 micro 2 accum 2 ckpt 9 grow 9 scale 2 epochs 3
        run 9
    """,

    # --- the run's own end --------------------------------------------------------------
    # epochs-end: budget left over after the last epoch is spent. The run stops all the same.
    "epochs-end": """
        rows 16 seed 27 rank 1 micro 2 accum 2 ckpt 9 grow 9 scale 1 epochs 2
        run 40
    """,
    # halt-zero: a program that declares a run and never takes a step.
    "halt-zero": """
        rows 20 seed 29 rank 2 micro 2 accum 1 ckpt 2 grow 2 scale 4 epochs 2
        nf 3
    """,
    # plain-two: an ordinary two-epoch run with a checkpoint cadence, a growth and one skip.
    #   Nothing unusual happens; a repair that treats every leg as a resize breaks it.
    "plain-two": """
        rows 36 seed 31 rank 3 micro 1 accum 2 ckpt 3 grow 4 scale 1 epochs 2
        nf 17
        run 12
    """,
}

ORDER = tuple(sorted(PROGS))


def ops(name):
    """One program as a list of op lines."""
    out = []
    for line in PROGS[name].strip().splitlines():
        tok = line.split()
        while tok:
            out.append("%s %s" % (tok[0], tok[1]) if tok[0] not in ("kill",) else tok[0])
            tok = tok[2:] if tok[0] not in ("kill",) else tok[1:]
    return out
