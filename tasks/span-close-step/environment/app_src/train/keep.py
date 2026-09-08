def dump(run):
    return {"w": list(run.w), "v": list(run.v), "applied": run.applied}


def load(run, s):
    run.w = list(s["w"])
    run.v = list(s["v"])
    run.applied = s["applied"]
