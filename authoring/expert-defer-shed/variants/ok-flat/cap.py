"""Sizing, with the rounding written as a negated floor."""


def slots(cfg, wanted, mbs):
    return -((-cfg.f * wanted * mbs) // (100 * cfg.ex))


def budget(cfg, c):
    return -((-cfg.g * c * cfg.bw) // 100)
