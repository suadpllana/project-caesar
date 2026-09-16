from pipe import frac


def div(rec, bands):
    out = 0
    for idx in rec.bands:
        band = bands[idx]
        if band.keep:
            out += band.share.get(rec.rid, 0)
    return out


def share(rec, d):
    return frac.norm(rec.w, d)


def fold(band, num, den, k):
    n = band.num * den + num * k * band.den
    d = band.den * den
    band.num, band.den = frac.norm(n, d)
