from feed import deal, draw, keep, spot, trail


def ex(box, w):
    op = w[0]
    if op == "seed":
        box.seed = int(w[1])
        box.note.clear()
    elif op == "cap":
        box.cap = int(w[1])
        box.note.clear()
    elif op == "src":
        box.src(w[1], int(w[2]), [int(v) for v in w[3].split(",")])
    elif op == "mix":
        box.pat = [box.sid(name) for name in w[1:]]
        box.note.clear()
    elif op == "open":
        box.runs[w[1]] = {"base": 0, "done": 0, "made": 0,
                          "w": int(w[2]), "m": int(w[3]), "a": int(w[4])}
    elif op == "feed":
        run = box.runs[w[1]]
        run["made"] += int(w[2])
    elif op == "take":
        run = box.runs[w[1]]
        run["done"] += int(w[2])
        if run["made"] < run["done"]:
            run["made"] = run["done"]
    elif op == "show":
        run = box.runs[w[1]]
        step, rank, seat = int(w[2]), int(w[3]), int(w[4])
        wide = run["w"] * run["m"] * run["a"]
        got = draw.slots(box, run["base"] + step * wide, wide)
        cut = deal.split(run["w"], run["m"], run["a"], got)
        trail.show(box, w[1], step, rank, seat, cut[rank][seat])
    elif op == "save":
        run = box.runs[w[1]]
        rec = keep.save(box, run)
        box.marks[w[2]] = rec
        trail.save(box, w[2], rec)
    elif op == "load":
        rec = box.marks[w[2]]
        run = keep.load(box, rec, int(w[3]), int(w[4]), int(w[5]))
        box.runs[w[1]] = run
        trail.load(box, w[1], run["base"], spot.at(box, run["base"]))
