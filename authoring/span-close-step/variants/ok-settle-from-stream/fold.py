"""The per-document objective, evaluated once at settlement.

Every token of the occurrence is scored again here, with the parameters in force
for the settling step. That is the whole point of the file: a document whose
tokens were consumed over several steps must not carry any statistic computed
under the parameters it met on the way, because a sum of scores taken at
different parameter points is not the objective at any of them.
"""
import math

from train import feat


def one(run, key):
    name, n, t = run.feed.info(key)
    xs = [feat.vec(name, i) for i in range(n)]
    sc = [sum(run.w[k] * x[k] for k in range(4)) for x in xs]
    top = max(sc)
    ex = [math.exp(s - top) for s in sc]
    z = sum(ex)
    loss = top + math.log(z) - sc[t]
    grad = [0.0, 0.0, 0.0, 0.0]
    for e, x in zip(ex, xs):
        p = e / z
        for k in range(4):
            grad[k] += p * x[k]
    for k in range(4):
        grad[k] -= xs[t][k]
    return loss, grad
