"""What a checkpoint has to carry.

Everything the trainer would otherwise have to rebuild from the beginning of the
run: the parameters, the momentum, the running average, the number of steps
taken, how far each open document has been consumed, and how many times each
pending occurrence has already been requeued. Leaving out either of the last two
restores a run that settles the wrong documents, or hands a requeued document a
fresh allowance.
"""


def dump(run):
    return {
        "w": list(run.w),
        "v": list(run.v),
        "ema": list(run.ema),
        "applied": run.applied,
        "seen": dict((str(k), v) for k, v in run.st.get("seen", {}).items()),
        "gen": dict((str(k), v) for k, v in run.st.get("gen", {}).items()),
    }


def load(run, s):
    run.w = list(s["w"])
    run.v = list(s["v"])
    run.ema = list(s["ema"])
    run.applied = s["applied"]
    run.st["seen"] = dict((int(k), v) for k, v in s["seen"].items())
    run.st["gen"] = dict((int(k), v) for k, v in s["gen"].items())
    run.st["cnt"] = {}
