from feed import spot


def save(box, run):
    wide = run["w"] * run["m"] * run["a"]
    return {"base": run["base"], "done": run["done"], "made": run["made"], "wide": wide,
            "at": spot.at(box, run["base"] + run["made"] * wide)}


def load(box, rec, world, micro, accum):
    return {"base": rec["base"] + rec["done"] * rec["wide"], "done": 0, "made": 0,
            "w": world, "m": micro, "a": accum}
