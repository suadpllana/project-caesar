"""Literal run scripts, one per graded decision, with the must-still-work side.

The generated population is the generality check; these are the enumerated
corners. Each name below says which decision the script pins down, and every one of
them was checked to reject at least one plausible-but-wrong reading of the brief
before it was kept: a corner nobody's mistake can fail is a corner that is not being
graded.
"""

CASES = {
    # An ordinary run: one document per step, nothing straddles a boundary and
    # nothing is requeued. Every reading that turns cautious has to survive this.
    "plain-run": """
        lim 4
        bat 1 1 1
        rep 9.0 2
        doc ab 4 1
        doc cd 4 3
        step
        step
        step
        emit
    """,

    # A document consumed over three steps, with another document settling in
    # between so the parameters move underneath it. Its objective belongs to the
    # step that finishes it, at that step's parameters.
    "span-across-update": """
        lim 4
        bat 1 1 2
        rep 9.0 2
        doc cd 4 2
        doc ab 9 5
        doc ef 4 1
        step
        step
        step
        emit
    """,

    # One document settling in a step that was split into two micro-batches: the
    # divisor is the settled document, not the split.
    "one-doc-two-batches": """
        lim 4
        bat 1 2 1
        rep 9.0 2
        doc ab 8 3
        step
        emit
    """,

    # Three documents settling inside a single micro-batch of nine tokens.
    "three-docs-one-batch": """
        lim 9
        bat 1 1 1
        rep 9.0 2
        doc ab 3 1
        doc cd 3 0
        doc ef 3 2
        step
        emit
    """,

    # A step whose mean gradient is longer than the clip: the update is shortened
    # and the reported length is the one before shortening.
    "clipped-step": """
        lim 3
        bat 1 1 1
        opt 0.3 1 2 0.0 0.40
        rep 9.0 2
        par 1.00 -1.00 0.50 -0.50
        doc ab 3 0
        doc cd 3 1
        step
        step
        emit
    """,

    # The same run with the clip out of reach, so the shortening itself is fenced
    # from the other side.
    "unclipped-step": """
        lim 3
        bat 1 1 1
        opt 0.3 1 2 0.0 9.00
        rep 9.0 2
        par 1.00 -1.00 0.50 -0.50
        doc ab 3 0
        doc cd 3 1
        step
        step
        emit
    """,

    # Momentum carries the shortened gradient, and the shortening happens once,
    # to the step's own gradient rather than to the accumulated velocity.
    "momentum-after-clip": """
        lim 3
        bat 1 1 1
        opt 0.3 1 4 0.5 0.45
        rep 9.0 2
        par 1.00 -1.00 0.50 -0.50
        doc ab 3 0
        doc cd 3 1
        doc ef 3 2
        step
        step
        step
        emit
    """,

    # A masked document is consumed like any other and never settles.
    "masked-consumed": """
        lim 4
        bat 1 1 1
        rep 9.0 2
        mdoc ab 4
        doc cd 4 1
        step
        step
        emit
    """,

    # A step that consumes a whole batch of masked tokens settles nothing, so it
    # is held: no parameters, no average, no schedule position, no count.
    "hold-settles-nothing": """
        lim 4
        bat 1 1 1
        rep 9.0 2
        doc ab 4 1
        mdoc cd 8
        doc ef 4 2
        step
        step
        step
        step
        emit
    """,

    # A step with no full sequence waiting is held as well, and the tokens that
    # are waiting stay waiting.
    "hold-nothing-ready": """
        lim 6
        bat 1 1 1
        rep 9.0 2
        doc ab 4 1
        step
        doc cd 4 0
        step
        step
        emit
    """,

    # Four short documents settle in one step under a layout whose micro-batch
    # order is not the stream order; the requeues follow the stream.
    "order-across-workers": """
        lim 3
        bat 1 2 2
        rep 0.20 2
        doc ab 3 0
        doc cd 3 1
        doc ef 3 2
        doc gh 3 0
        step
        emit
    """,

    # Two documents settle together and only one is over the threshold: the
    # decision is per document, on its own loss. The threshold sits below the
    # step's mean here and above it in the next case, so a decision taken on the
    # mean is wrong in both directions.
    "requeue-under-the-mean": """
        lim 3
        bat 1 1 2
        rep 0.60 2
        par 1.00 -1.00 0.50 -0.50
        doc ab 3 0
        doc cd 3 1
        step
        emit
    """,

    "requeue-over-the-mean": """
        lim 3
        bat 1 1 2
        rep 0.80 2
        par 1.00 -1.00 0.50 -0.50
        doc ab 3 0
        doc cd 3 1
        step
        emit
    """,

    # Two documents that share a name are two documents: the requeue allowance
    # belongs to the chain each one starts, not to the name.
    "same-name-twice": """
        lim 3
        bat 1 1 1
        rep 0.20 1
        doc ab 3 0
        doc ab 3 0
        step
        step
        step
        step
        emit
    """,

    # A requeued document joins the tail of the pending stream, behind work that
    # was already waiting, so what settles next is not what was just requeued.
    "requeue-joins-the-tail": """
        lim 3
        bat 1 1 1
        rep 0.20 1
        doc ab 3 0
        doc cd 3 1
        doc ef 3 2
        step
        step
        step
        step
        emit
    """,

    # Held steps sit between taken ones: the warmup and the decay are keyed to
    # the steps actually taken, and the rate belongs to the step taking it.
    "warmup-across-holds": """
        lim 4
        bat 1 1 1
        opt 0.20 3 2 0.0 9.00
        rep 9.0 2
        doc ab 4 1
        mdoc cd 4
        doc ef 4 0
        mdoc gh 4
        doc ij 4 2
        doc kl 4 1
        step
        step
        step
        step
        step
        step
        emit
    """,

    # The running average is taken after the update, with a decay that warms up
    # over the steps taken.
    "average-warmup": """
        lim 4
        bat 1 1 1
        ema 0.70
        rep 9.0 2
        doc ab 4 1
        doc cd 4 0
        doc ef 4 2
        step
        emit
        step
        emit
        step
        emit
    """,

    # A checkpoint restores the trainer and the stream but not the batch layout,
    # which is configuration rather than state.
    "restore-not-the-layout": """
        lim 4
        bat 1 1 1
        rep 9.0 2
        doc ab 4 1
        doc cd 4 0
        doc ef 4 2
        doc gh 4 1
        step
        save
        resh 1 1 2
        step
        load
        step
        emit
    """,

    # A checkpoint taken while a document is half consumed has to carry that,
    # or the restored run settles it a step early or a step late.
    "restore-an-open-document": """
        lim 4
        bat 1 1 1
        rep 9.0 2
        doc ab 4 1
        doc cd 9 5
        doc ef 4 0
        step
        step
        save
        step
        step
        load
        step
        step
        emit
    """,

    # A checkpoint taken after a requeue has to carry how much of the allowance
    # that chain has already spent.
    "restore-the-allowance": """
        lim 3
        bat 1 1 1
        rep 0.20 1
        doc ab 3 0
        doc cd 3 1
        step
        save
        step
        load
        step
        step
        step
        emit
    """,

    # `load` before any `save` changes nothing.
    "load-without-save": """
        lim 4
        bat 1 1 1
        rep 9.0 2
        doc ab 4 1
        load
        step
        emit
    """,

    # The stream runs out mid-batch: the step takes the sequences that are there.
    "short-final-step": """
        lim 3
        bat 1 1 3
        rep 9.0 2
        doc ab 3 0
        doc cd 3 1
        doc ef 3 2
        doc gh 3 0
        step
        step
        step
        emit
    """,

    # A document wider than a whole batch: several steps consume it and settle
    # nothing before the one that finishes it.
    "document-wider-than-a-batch": """
        lim 3
        bat 1 1 1
        rep 9.0 2
        doc ab 3 1
        doc cd 10 4
        doc ef 3 0
        step
        step
        step
        step
        step
        step
        emit
    """,

    # The two run scripts that ship in the tree, graded like everything else.
    "shipped-hold": """
        lim 4
        bat 1 1 1
        rep 9.0 2
        doc ab 4 1
        mdoc cd 8
        doc ef 4 2
        step
        step
        step
        step
        emit
    """,

    "shipped-mixed": """
        lim 5
        bat 1 2 1
        opt 0.20 2 3 0.40 1.20
        ema 0.90
        rep 1.00 2
        par 0.50 -0.25 0.75 -0.50
        doc ab 12 4
        mdoc cd 5
        doc ef 6 0
        doc gh 3 2
        step
        step
        save
        resh 2 1 1
        step
        doc ij 7 3
        step
        load
        step
        emit
    """,
}

ORDER = sorted(CASES)


def ops(name):
    return [ln.strip() for ln in CASES[name].strip().splitlines() if ln.strip()]
