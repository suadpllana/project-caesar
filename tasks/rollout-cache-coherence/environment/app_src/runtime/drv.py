def play(eng, ops):
    for op in ops:
        t = op["op"]
        if t == "add":
            eng.add(op["rid"], op["prompt"], op.get("adapter"), op["max_new"])
        elif t == "step":
            for _ in range(int(op.get("n", 1))):
                eng.step()
        elif t == "sync":
            eng.sync(op["ups"])
        elif t == "sleep":
            eng.sleep(int(op["level"]))
        elif t == "wake":
            eng.wake()
        elif t == "drain":
            eng.drain(int(op.get("cap", 4000)))
        else:
            raise ValueError(t)
    return eng.report()
