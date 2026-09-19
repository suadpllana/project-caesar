def slots(cfg, wanted):
    unit = 100 * cfg.ex
    return (cfg.f * wanted + unit - 1) // unit


def budget(cfg, c):
    return (cfg.g * c * cfg.bw + 99) // 100
