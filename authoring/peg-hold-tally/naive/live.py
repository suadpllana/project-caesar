"""Correct-but-infeasible variant A: a peg takes a reference over the whole live map.

This is the memorised model of a snapshot and it settles every rule correctly. Its cost is the
live map at each peg, at each shed and at each tally, which is what the execution limit is
measured against.
"""


class Acct:
    def __init__(self):
        self.roll = []
        self.vc = {}
        self.pc = {}
        self.have = {}
        self.pset = {}
        self.stop = {}
        self.q = []
        self.out = set()
        self.fresh = []
        self.t = 0


def new():
    return Acct()


def born(a, b, t):
    a.roll.append(b)
    a.vc[b] = 0
    a.pc[b] = 0


def hold(a, v, x, b, t):
    a.t = t
    box = a.have.setdefault(v, {})
    box[b] = box.get(b, 0) + 1
    a.vc[b] += 1


def free(a, v, x, b, t):
    a.t = t
    box = a.have[v]
    if box[b] == 1:
        del box[b]
    else:
        box[b] -= 1
    a.vc[b] -= 1
    if a.vc[b] == 0 and a.pc[b] == 0 and b not in a.stop:
        a.stop[b] = t
        a.q.append(b)
