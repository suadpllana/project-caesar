LINE = 18
PAD = 6
DEF = 24
VIEW = 300
W0 = 40


def high(ln, w):
    n = (ln + w - 1) // w
    if n < 1:
        n = 1
    return LINE * n + PAD
