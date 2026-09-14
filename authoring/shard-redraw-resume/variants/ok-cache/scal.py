"""The loss scale, as a pair returned rather than mutated in place."""


def after_skip(sc, _gt):
    return (sc - 1 if sc > 0 else sc), 0


def after_step(sc, gt, grow):
    gt += 1
    if gt >= grow:
        return sc + 1, 0
    return sc, gt
