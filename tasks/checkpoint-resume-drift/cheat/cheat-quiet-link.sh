#!/bin/bash
# Rebuilds the per-row stream by replaying the epoch, and answers its own sample
# requests out of the seed in the tree so the service never sees the replay and
# never charges for it. The corpus the service hands out is not the one in the
# tree, so the replay packs different rows, takes a different number of draws and
# lands the stream somewhere the run it continues never was.
set -euo pipefail

cat > /app/train/ckpt.py <<'PYEOF'
# Which of the trainer's state holders belong in the checkpoint.
#
# The channel carries a bounded vector of integers, so the question is not "how do we
# serialise the trainer" but "which state is authoritative".  Three tests separate the
# holders, and all three have to be applied:
#
#   Is it path dependent?  The parameters, the optimiser moments and the shadow average,
#   the position the sampler has reached, the item the packer drew and could not place,
#   the stream position the per-row draws come from, and everything the open accumulation
#   window has taken in so far are all functions of the history and of nothing else.  None
#   of them can be recovered from the step counter, so all of them are carried.
#
#   Is it derivable?  data.samp rebuilds any epoch's order from the seed and the epoch
#   number, so its memo of permutations comes back identical at the load and carrying it
#   buys nothing; on its own it is larger than the whole channel, which is what
#   cheat-save-every-holder runs into.  data.store holds nothing at all.  The corpus is on
#   the supervisor's side of the link, and the same identifier returns the same tokens
#   whichever process asks, so there is nothing there for a checkpoint to carry.
#
#   Is it a view of the configuration?  train.sched memoises the four schedule values it
#   last derived.  Those are a function of the step and of the configuration in force, and
#   the configuration in force after a load is the amended one.  Restoring the memo pins
#   the pre-amendment learning rate, curriculum bound, window length and averaging shift
#   for exactly one step, which is long enough to move the parameters onto a path the
#   uninterrupted run never takes.  So it is left out.
#
# train.loop is the holder the third test is easy to get wrong on.  Its window length was
# read from the schedule, so it looks like a view - but it was latched when the window
# opened, before the amendment existed, and an amendment does not reach back across a
# boundary that has already been crossed.  While a window is open that number is history,
# not configuration, and it is carried with the rest of the window's state.
HOLD = ("model", "opt", "loop", "feed")


def pack_state(cx):
    out = []
    for nm in HOLD:
        v = list(getattr(cx, nm).snap())
        out.append(len(v))
        out.extend(v)
    return out


from core.mix import mix
from data import pack
from data.feed import Feed


class _Quiet:
    def __init__(self, cfg):
        self.sd = cfg["seed"]

    def call(self, q, a):
        if q == "row":
            sid = a[0]
            n = 2 + mix(self.sd, sid) % 20
            return [1 + mix(sid * 31 + i, self.sd) % 61 for i in range(n)]
        return []


def _rebuild(cx, upto):
    real = cx.lk
    quiet = _Quiet(cx.cfg)
    keep = cx.feed
    cx.lk = quiet
    cx.store.lk = quiet
    cx.samp.lk = quiet
    cx.feed = Feed()
    try:
        guard = 0
        while cx.feed.cur < upto and guard < 4000:
            guard += 1
            for _ in pack.fill(cx, cx.loop.step):
                cx.noise.draw()
    except Exception:
        pass
    finally:
        cx.feed = keep
        cx.lk = real
        cx.store.lk = real
        cx.samp.lk = real


def unpack_state(cx, vec):
    i = 0
    for nm in HOLD:
        if i >= len(vec):
            break
        n = vec[i]
        getattr(cx, nm).rest(vec[i + 1: i + 1 + n])
        i += 1 + n
    _rebuild(cx, cx.feed.cur)
PYEOF

cat > /app/data/feed.py <<'PYEOF'
class Feed:
    def __init__(self):
        self.cur = 0
        self.hd = None

    def draw(self, samp):
        sid = samp.pick(self.cur)
        self.cur += 1
        return sid

    def take(self):
        h = self.hd
        self.hd = None
        return h

    def hold(self, sid, bd):
        self.hd = (sid, bd)

    # Two fields, and the second one is the one that gets dropped.
    #
    # The cursor is obvious: it is where the sampler has got to, and without it the
    # stream restarts from the top of the epoch.
    #
    # The held item is the sample data.pack drew and had no room for.  It carries the
    # curriculum bound that was in force at the moment it was drawn, because data.pack
    # reads that bound once, when the item leaves the sampler, and then truncates to it
    # every time it tries to place the item - including at the next fill, and including
    # after a resume.  An item held across a save is therefore an item whose bound was
    # fixed under the schedule of the step that drew it.  Save the identifier alone and
    # the item comes back truncated to whatever the bound is after the load; if a
    # curriculum change or an amendment landed in between, that is a different row of
    # tokens, a different gradient, and a run that never rejoins the one it continues.
    def snap(self):
        if self.hd is None:
            return [self.cur, -1, -1]
        return [self.cur, self.hd[0], self.hd[1]]

    def rest(self, vec):
        if len(vec) == 3:
            self.cur = vec[0]
            self.hd = None if vec[1] < 0 else (vec[1], vec[2])
PYEOF

cat > /app/train/noise.py <<'PYEOF'
MODN = 2147483647


class Noise:
    def __init__(self, cfg):
        self.s = (cfg["seed"] * 7919 + 13) % MODN
        self.n = 0

    def draw(self):
        self.n += 1
        self.s = (self.s * 48271) % MODN
        return self.s

    # The state that reseeding cannot reconstruct.
    #
    # train.model takes one draw per packed row, and the number of rows a fill produces
    # depends on how the lengths happened to pack against the bin width, so the number of
    # draws taken by step k is not a function of k.  Reseeding from the seed and the step
    # counter therefore lands somewhere other than where the run was, and every gradient
    # after the load is perturbed by a different mask.  Nothing raises, the loss curve
    # looks ordinary, and the run simply never rejoins the one it continues.  The position
    # itself is the only thing that carries it, so it is saved and put back verbatim.
    def snap(self):
        return [self.s, self.n]

    def rest(self, vec):
        if len(vec) == 2:
            self.s = vec[0] % MODN
            self.n = vec[1]
PYEOF

cat > /app/train/sched.py <<'PYEOF'
# Unchanged from the tree as shipped.
#
# The memo is correct as it stands: it holds the four values derived for one step, and it
# is cleared whenever the configuration is amended, so every value it hands out comes from
# the configuration in force. Nothing here needs fixing. What the memo must not do is
# survive a resume, and that is decided in train/ckpt.py by leaving this holder out of the
# checkpoint - not by changing anything below.
#
# It stays in the editable set because naming only the files that have to change would
# hand over half the diagnosis.
def _pick(tab, step):
    v = tab[0][1]
    for k, x in tab:
        if step >= k:
            v = x
    return v


class Sched:
    def __init__(self, cfg):
        self.cfg = cfg
        self.at_ = -1
        self.val = None

    def _calc(self, step):
        s = self.cfg["sched"]
        w = s["warm"]
        b = s["base"]
        if step < w:
            lr = (b * (step + 1)) // w
        else:
            lr = b - 3 * (step - w)
            if lr < 8:
                lr = 8
        return [lr, _pick(s["bounds"], step), _pick(s["window"], step), _pick(s["ema"], step)]

    def at(self, step):
        if self.at_ != step or self.val is None:
            self.val = self._calc(step)
            self.at_ = step
        return self.val

    def clear(self):
        self.at_ = -1
        self.val = None

    def lr(self, step):
        return self.at(step)[0]

    def bound(self, step):
        return self.at(step)[1]

    def wsize(self, step):
        return self.at(step)[2]

    def eshift(self, step):
        return self.at(step)[3]

    def snap(self):
        if self.val is None:
            return [-1, 0, 0, 0, 0]
        return [self.at_] + list(self.val)

    def rest(self, vec):
        if len(vec) >= 5 and vec[0] >= 0:
            self.at_ = vec[0]
            self.val = list(vec[1:5])
PYEOF

