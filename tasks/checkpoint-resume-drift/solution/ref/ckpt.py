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
HOLD = ("model", "opt", "loop", "feed", "noise")


def pack_state(cx):
    out = []
    for nm in HOLD:
        v = list(getattr(cx, nm).snap())
        out.append(len(v))
        out.extend(v)
    return out


def unpack_state(cx, vec):
    i = 0
    for nm in HOLD:
        if i >= len(vec):
            break
        n = vec[i]
        getattr(cx, nm).rest(vec[i + 1: i + 1 + n])
        i += 1 + n
