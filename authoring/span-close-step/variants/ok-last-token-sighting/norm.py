"""Step normalization and clipping.

The divisor is the number of documents that settled in the step - not the number
of micro-batches the step happened to be split into, which is what makes the
printed trace independent of the accumulation and worker layout. The reported
norm is the one before clipping; clipping changes the step that is taken, never
the number that is reported.
"""
import math


def step(run, parts):
    m = len(parts)
    loss = sum(p[0] for p in parts) / m
    grad = [sum(p[1][k] for p in parts) / m for k in range(4)]
    gn = math.sqrt(sum(v * v for v in grad))
    cap = run.cfg["clip"]
    if gn > cap:
        f = cap / gn
        grad = [v * f for v in grad]
    return loss, grad, gn
