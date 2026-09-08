"""Whether a step is taken, and what it does to the trainer's state.

A step that settles nothing is held: the tokens it consumed stay consumed, but no
parameter, momentum, average or schedule position moves, and the step does not
count. Every schedule here is therefore keyed to the number of steps actually
taken, not to the number of `step` events seen. The learning rate belongs to the
step being taken, so it is read before the counter advances; the running average
follows the update, so its decay is read after.
"""


def hold(run, done):
    return not done


def apply(run, grad):
    c = run.cfg
    k = run.applied
    if k < c["wu"]:
        lr = c["base"] * (k + 1) / c["wu"]
    else:
        lr = c["base"] * (0.5 ** ((k - c["wu"]) // c["hl"]))
    run.v = [c["mu"] * run.v[i] + grad[i] for i in range(4)]
    run.w = [run.w[i] - lr * run.v[i] for i in range(4)]
    run.applied = k + 1
    b = min(c["bmax"], (1.0 + run.applied) / (10.0 + run.applied))
    run.ema = [b * run.ema[i] + (1.0 - b) * run.w[i] for i in range(4)]
    return lr
