import math

from train import feat


def one(run, key):
    name, n, t = run.feed.info(key)
    xs = [feat.vec(name, i) for i in range(n)]
    sc = [sum(run.w[k] * x[k] for k in range(4)) for x in xs]
    ex = [math.exp(s) for s in sc]
    z = sum(ex)
    loss = math.log(z) - sc[t]
    grad = []
    for k in range(4):
        grad.append(sum(e * x[k] for e, x in zip(ex, xs)) / z - xs[t][k])
    return loss, grad
