from . import memo


def face(st, a):
    memo.prime(st)
    return memo.reach(st, a)


def gather(st, lo, hi):
    return memo.frame(st, lo, hi)
