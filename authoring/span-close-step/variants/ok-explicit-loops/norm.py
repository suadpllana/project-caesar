import math


def step(run, parts):
    total = 0.0
    grad = [0.0, 0.0, 0.0, 0.0]
    for loss, g in parts:
        total += loss
        for k in range(4):
            grad[k] += g[k]
    m = float(len(parts))
    total /= m
    sq = 0.0
    for k in range(4):
        grad[k] /= m
        sq += grad[k] * grad[k]
    gn = math.sqrt(sq)
    if gn > run.cfg["clip"]:
        for k in range(4):
            grad[k] = grad[k] * run.cfg["clip"] / gn
    return total, grad, gn
