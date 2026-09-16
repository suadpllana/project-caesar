from fractions import Fraction


def div(rec, bands):
    out = 0
    for idx in rec.bands:
        band = bands[idx]
        if band.keep:
            out += band.share.get(rec.rid, 0)
    return out


def share(rec, d):
    got = Fraction(rec.w, d)
    return got.numerator, got.denominator


def fold(band, num, den, k):
    got = Fraction(band.num, band.den) + Fraction(num * k, den)
    band.num, band.den = got.numerator, got.denominator
