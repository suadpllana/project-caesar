from pipe import frac


def div(rec, bands):
    out = 0
    for idx, got in rec.bits:
        if bands[idx].keep:
            out += got
    return out


def share(rec, d):
    return frac.norm(rec.w, d)


def fold(band, num, den, k):
    n = band.num * den + num * k * band.den
    d = band.den * den
    band.num, band.den = frac.norm(n, d)
