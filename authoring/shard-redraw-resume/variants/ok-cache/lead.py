"""The leg driver, over a dict instead of an object with slots."""

from rig import cut, keep, say, turn


def state(run):
    if run.leg is None:
        run.leg = {"epoch": 0, "seen": {}, "fed": 0, "done": 0, "sc": run.scale, "gt": 0,
                   "rank": run.rank, "saved": None, "nf": frozenset(run.nf)}
    return run.leg


def walk(run, left):
    st = state(run)
    while left > 0 and st["epoch"] < run.epochs:
        if cut.steps_left(run, st) < 1:
            cut.roll(st)
            say.roll(run, st["epoch"])
            continue
        turn.once(run, st)
        left -= 1


def drop(run):
    keep.restore(run, state(run))


def swap(run, rank):
    state(run)["rank"] = rank
    say.back(run, rank)


def close(run):
    say.halt(run, state(run)["done"])
