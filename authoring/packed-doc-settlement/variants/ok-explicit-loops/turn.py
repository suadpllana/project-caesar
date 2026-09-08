def hold(run, done):
    return len(done) == 0


def rate(run, taken):
    c = run.cfg
    if taken < c["wu"]:
        return c["base"] * float(taken + 1) / float(c["wu"])
    lr = c["base"]
    left = taken - c["wu"]
    while left >= c["hl"]:
        lr = lr / 2.0
        left -= c["hl"]
    return lr


def apply(run, grad):
    c = run.cfg
    lr = rate(run, run.applied)
    v = []
    w = []
    for i in range(4):
        vi = c["mu"] * run.v[i] + grad[i]
        v.append(vi)
        w.append(run.w[i] - lr * vi)
    run.v = v
    run.w = w
    run.applied += 1
    b = (1.0 + run.applied) / (10.0 + run.applied)
    if b > c["bmax"]:
        b = c["bmax"]
    run.ema = [b * run.ema[i] + (1.0 - b) * run.w[i] for i in range(4)]
    return lr
