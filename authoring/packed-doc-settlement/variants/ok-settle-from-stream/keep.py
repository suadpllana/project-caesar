def dump(run):
    return {
        "w": list(run.w),
        "v": list(run.v),
        "ema": list(run.ema),
        "applied": run.applied,
        "gen": dict((str(k), v) for k, v in run.st.get("gen", {}).items()),
    }


def load(run, s):
    run.w = list(s["w"])
    run.v = list(s["v"])
    run.ema = list(s["ema"])
    run.applied = s["applied"]
    run.st["gen"] = dict((int(k), v) for k, v in s["gen"].items())
