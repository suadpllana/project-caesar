"""Buffer sizing.

Buffers are allocated once for the whole step, before any token is placed, from what the first
microbatch asks for scaled up by the number of microbatches. The wants that deferral creates
later in the step therefore press against a size that was fixed before they existed.
"""


def slots(cfg, wanted, mbs):
    """Per-expert slots for the step, rounded up."""
    unit = 100 * cfg.ex
    return (cfg.f * wanted * mbs + unit - 1) // unit


def budget(cfg, c):
    """Placements a bank may still hold once the step is over, rounded up."""
    return (cfg.g * c * cfg.bw + 99) // 100
