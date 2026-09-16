from pipe import frac


def div(rec, bands):
    return rec.n - 1


def share(rec, d):
    return frac.norm(rec.w, d)


def fold(band, num, den, k):
    n = band.num * den + num * k * band.den
    d = band.den * den
    band.num, band.den = frac.norm(n, d)
