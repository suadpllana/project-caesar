#!/bin/bash
# checkpoints the parameters and forgets the rest
set -euo pipefail

cat > /app/train/pick.py <<'PYEOF'
"""Open-document bookkeeping and settlement selection.

`take` is called once per micro-batch and records nothing but token counts: the
objective is evaluated at settlement, so no score may be folded here. `close` is
called once per step and names the occurrences whose last token was consumed
during it, in the order those last tokens stand in the stream. Occurrence keys are
handed out in stream order, so ascending key is that order; a masked occurrence
(target -1) is consumed and dropped rather than settled.
"""


def take(run, mb):
    cnt = run.st.setdefault("cnt", {})
    for sq in mb:
        for key, _ in sq:
            cnt[key] = cnt.get(key, 0) + 1


def close(run):
    cnt = run.st.get("cnt", {})
    seen = run.st.setdefault("seen", {})
    done = []
    for key, c in cnt.items():
        seen[key] = seen.get(key, 0) + c
        _, n, t = run.feed.info(key)
        if seen[key] >= n:
            del seen[key]
            if t >= 0:
                done.append(key)
    run.st["cnt"] = {}
    return sorted(done)
PYEOF

cat > /app/train/fold.py <<'PYEOF'
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
PYEOF

cat > /app/train/norm.py <<'PYEOF'
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
PYEOF

cat > /app/train/turn.py <<'PYEOF'
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
PYEOF

cat > /app/train/again.py <<'PYEOF'
"""Requeueing a settled document that the step found hard.

The decision is per document, on that document's own loss at settlement, and the
count that the cap applies to travels along the chain of requeues rather than
belonging to the name: two occurrences of the same name that were declared apart
are separate documents and each gets the full allowance. The requeued occurrence
joins the tail of the pending stream, after everything already waiting, which is
what makes the packing that follows depend on this decision.
"""


def after(run, done, parts):
    gen = run.st.setdefault("gen", {})
    out = []
    for key, part in zip(done, parts):
        born = gen.pop(key, 0)
        if part[0] > run.cfg["thr"] and born < run.cfg["cap"]:
            name, n, t = run.feed.info(key)
            gen[run.feed.add(name, n, t)] = born + 1
            out.append(name)
    return out
PYEOF

cat > /app/train/keep.py <<'PYEOF'
def dump(run):
    return {"w": list(run.w), "v": list(run.v), "applied": run.applied}


def load(run, s):
    run.w = list(s["w"])
    run.v = list(s["v"])
    run.applied = s["applied"]
PYEOF
