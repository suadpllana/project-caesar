"""Sessions: batches of rail settings, in the order the config layer emits them.

Built here and never anywhere the runner can read. The shape is not described
in the brief and does not need to be: holding on to what has already been
written, walking a rail down without taking it out of service, saying both
halves of a rail's trim in one word, and staging neighbouring registers in one
frame are better on any batch, not only on these.

Rails are independent. Arrival order is rail by rail, and inside a rail it is
already safe: the limit goes up before the voltage that needs it and comes down
after, and a live rail is taken down before its limit is dropped under what it
is drawing. An implementation that applies the batch exactly as it arrived
never faults. It only pays.

Some requests restate a setting that is already in force, because a config
layer re-sends the whole rail rather than a diff. That is the decoy: skipping
them is the obvious saving and it is not the one that matters.

Most of the churn is a rail's trim moving. A good deal of it moves only one
half -- a board revision that tightens a limit and leaves the voltage alone, or
the other way round -- and a rail the rack has taken out of service is left
held under its own limit, which the part allows only while that rail is down.
"""

import random


def next_state(cur, rng):
    """Where the rails should stand after the next batch.

    The case the part is fussiest about is a live rail being walked downwards,
    so that is the case the batches are mostly made of. A rail sitting under
    its own limit is out of service; it comes back limit first, and while it is
    down it can still be retrimmed, as long as its voltage stays inside the
    limit it is holding at the time.
    """
    vset, ilim, enabled = cur
    rails = len(vset)
    nv, ni, ne = list(vset), list(ilim), list(enabled)
    for r in range(rails):
        if rng.random() < 0.30:
            continue
        v, i = vset[r], ilim[r]

        if i < v:                                   # out of service, under its limit
            roll = rng.random()
            if roll < 0.45:                         # brought back, limit first
                ni[r] = rng.randrange(max(v, 40), 100)
                nv[r] = rng.randrange(10, ni[r])
                ne[r] = True
            elif roll < 0.75 and i > 8:             # retrimmed where it lies
                nv[r] = rng.randrange(6, i + 1)
                ni[r] = rng.randrange(3, nv[r])
            continue

        roll = rng.random()
        if roll < 0.22 and v > 14:                  # walked down, both halves
            nv[r] = rng.randrange(12, v)
            ni[r] = rng.randrange(nv[r], v)         # under the live voltage
        elif roll < 0.34:                           # retuned, both halves
            ni[r] = rng.randrange(40, 100)
            nv[r] = rng.randrange(10, ni[r])
        elif roll < 0.56:                           # the voltage on its own
            nv[r] = rng.randrange(10, i + 1)
        elif roll < 0.78:                           # the limit on its own
            ni[r] = rng.randrange(max(v, 20), 100)
        elif roll < 0.87 and v > 12:                # taken out of service
            nv[r] = rng.randrange(12, v + 1)
            ni[r] = rng.randrange(4, nv[r])
            ne[r] = False
        elif roll < 0.92:                           # the enable on its own
            ne[r] = not enabled[r]
    return nv, ni, ne


def batch_for(cur, want, rng, restate=0.25):
    vset, ilim, enabled = cur
    wv, wi, we = want
    rails = len(vset)
    reqs = []

    order = list(range(rails))
    rng.shuffle(order)
    for r in order:
        touch_v = wv[r] != vset[r]
        touch_i = wi[r] != ilim[r]
        touch_e = we[r] != enabled[r]

        # A live rail has to come down before its limit is taken under the
        # voltage it is holding.
        needs_down = enabled[r] and touch_i and wi[r] < vset[r]
        went_down = False
        if needs_down or (touch_e and not we[r]):
            reqs.append((2, r, 0))
            went_down = True

        if touch_i and touch_v:
            if wi[r] >= ilim[r]:
                reqs.append((1, r, wi[r]))
                reqs.append((0, r, wv[r]))
            else:
                reqs.append((0, r, wv[r]))
                reqs.append((1, r, wi[r]))
        elif touch_i:
            reqs.append((1, r, wi[r]))
        elif touch_v:
            reqs.append((0, r, wv[r]))
        elif rng.random() < restate and ilim[r] >= vset[r]:
            reqs.append((0, r, wv[r]))          # already in force

        if we[r] and (touch_e or went_down):
            reqs.append((2, r, 1))
        elif we[r] and enabled[r] and rng.random() < restate:
            reqs.append((2, r, 1))              # already in force
    return reqs


def build(seed, rails=20, batches=10):
    rng = random.Random(seed)
    # The sled is up. Rails are live and stay live; what churns is the trim.
    vset = [50] * rails
    ilim = [90] * rails
    enabled = [True] * rails
    start = (list(vset), list(ilim), list(enabled))

    session = []
    cur = (list(vset), list(ilim), list(enabled))
    for _ in range(batches):
        want = next_state(cur, rng)
        reqs = batch_for(cur, want, rng)
        session.append((reqs, (list(want[0]), list(want[1]), list(want[2]))))
        cur = (list(want[0]), list(want[1]), list(want[2]))
    return start, session
