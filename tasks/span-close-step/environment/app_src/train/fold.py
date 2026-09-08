import math


def one(run, key):
    a = run.st["acc"].pop(key)
    loss = a[0] + math.log(a[1]) - a[3]
    grad = [a[2][k] / a[1] - a[4][k] for k in range(4)]
    return loss, grad
