"""Sizing, with the rounding written as a divmod."""


def slots(cfg, wanted, mbs):
    whole, rest = divmod(cfg.f * wanted * mbs, 100 * cfg.ex)
    return whole + (1 if rest else 0)


def budget(cfg, c):
    whole, rest = divmod(cfg.g * c * cfg.bw, 100)
    return whole + (1 if rest else 0)
