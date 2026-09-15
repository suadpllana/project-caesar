"""The checkpoint, which holds the run and not the blend.

What goes back on a stop is the step, and the epoch, cursor and counter of every source the
checkpoint holds. Who is live and what they weigh is the manifest's, and the manifest is
durable: a departure or a reweighing since the checkpoint stands. Which is why the restored
counters cannot simply be believed - they were written under a blend that may no longer be the
one in force, and when the two differ they are worth nothing and the segment starts again.
"""
from mix import deck


def start(h, ranks, micro, accum):
    h.ranks = ranks
    h.micro = micro
    h.accum = accum


def save(h):
    h.mark = {
        "step": h.step,
        "epoch": dict(h.epoch),
        "cur": dict(h.cur),
        "cnt": dict(h.cnt),
        "sig": deck.sig(h),
    }


def stop(h):
    mark = h.mark
    h.step = mark["step"]
    for name in mark["epoch"]:
        h.epoch[name] = mark["epoch"][name]
        h.cur[name] = mark["cur"][name]
        h.cnt[name] = mark["cnt"][name]
    deck.rebase(h)
    h.ranks = 0
    h.micro = 0
    h.accum = 0
